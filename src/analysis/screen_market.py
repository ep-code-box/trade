"Track1/Track EX/Track2 통합 리포트 v4.5 (거장의 철학 + 정석 엔진 통합)."
import pandas as pd
import numpy as np
from datetime import datetime
from src.db import get_connection
from src.analysis.market_filter import check_market_health
from collections import Counter

def get_themes_for_stock(code):
    conn = get_connection()
    df = pd.read_sql_query("SELECT category_name FROM sectors_themes WHERE code = ? AND category_type = 'THEME'", conn, params=(code,))
    conn.close()
    return df["category_name"].tolist()

def get_supply_quality(code):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT close, open, frgn_net_buy, orgn_net_buy FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 5", conn)
    conn.close()
    if df.empty or df['frgn_net_buy'].isnull().all(): return "Unknown"
    for col in ['close', 'open', 'frgn_net_buy', 'orgn_net_buy']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['is_up'] = df['close'] > df['open']
    up_days = df[df['is_up']]
    down_days = df[~df['is_up']]
    up_supply = (up_days['frgn_net_buy'].sum() + up_days['orgn_net_buy'].sum()) if not up_days.empty else 0
    down_supply = abs(down_days['frgn_net_buy'].sum() + down_days['orgn_net_buy'].sum()) if not down_days.empty else 0
    total_net = df['frgn_net_buy'].sum() + df['orgn_net_buy'].sum()
    if up_supply > down_supply * 1.2: return "🌟 공격적매집"
    if total_net > 0: return "✅ 수급우량"
    if total_net < 0: return "🚨 수급이탈"
    return "👤 개인주도"

def get_tick_size(price):
    if price < 2000: return 1
    elif price < 5000: return 5
    elif price < 20000: return 10
    elif price < 50000: return 50
    elif price < 200000: return 100
    else: return 500

def adjust_to_tick(price, method='up'):
    tick = get_tick_size(price)
    if method == 'up': return ((int(price) // tick) + 1) * tick
    else: return (int(price) // tick) * tick

def get_breakout_price(high_52w):
    return adjust_to_tick(high_52w * 1.005, 'up')

def check_chart_pattern(code):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT open, high, low, close FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 5", conn)
    conn.close()
    if len(df) < 5: return False
    for col in ['open', 'high', 'low', 'close']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    recent = df.head(5)
    if ((recent['high'] - recent['low']) / recent['close']).mean() > 0.06: return False
    recent_shadow = recent.apply(lambda x: (x['high'] - x['close']) if x['close'] > x['open'] else (x['high'] - x['open']), axis=1)
    if (recent_shadow / recent['close']).mean() > 0.03: return False
    return True

def get_trend_candidates_db():
    conn = get_connection()
    res = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()
    if not res or not res[0]:
        conn.close(); return pd.DataFrame()
    max_date = res[0]
    
    # [v4.5 통합 필터] 기존 정석 조건 + RS 90 상향
    query = f"""
    SELECT 
        d.date, d.code, m.name, m.market_type,
        d.close, d.amount, d.volume, d.rs_score,
        (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
        d.high_52w, d.low_52w, d.sma_20, d.sma_50, d.sma_150, d.sma_200,
        d.volume_sma_50, m.bsop_prfi, m.thtr_ntin, m.roe, m.sale_account
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      AND d.close > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
      AND d.close >= d.low_52w * 1.25
      AND d.close >= d.high_52w * 0.80
      AND d.rs_score >= 90
      AND (d.vol_std_10d / d.vol_std_50d) < 0.9
    ORDER BY d.rs_score DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def calculate_survival_trade(row):
    entry = get_breakout_price(row['high_52w'])
    stop_fixed = entry * 0.93
    stop_sma20 = row['sma_20'] or 0
    stop = max(stop_fixed, stop_sma20)
    stop = adjust_to_tick(stop, 'down')
    
    # [스승의 필터] 손절선 붕괴 여부
    is_broken = row['close'] < stop
    
    risk_pct = (entry - stop) / entry if entry > stop else 0.07
    weight = min(20, int(1.0 / risk_pct))
    
    return entry, stop, f"{weight}%", is_broken

def save_to_trade_plan(candidates, track_name="TRACK 1"):
    if not candidates: return
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    for row in candidates:
        entry, stop, weight, is_broken = calculate_survival_trade(row)
        vcp = row.get('vcp_ratio', 0)
        
        # [v4.5] 거장들의 잣대 적용 상태값
        if is_broken: status = 'CANCEL'
        elif vcp > 0.1: status = 'WATCH'
        else: status = 'READY'
        
        rationale = f"RS {row['rs_score']:.1f} | VCP {vcp:.2f} | " + \
                    ("추세 붕괴(매도)" if is_broken else "변동성 수축 대기" if vcp > 0.1 else "돌파 임박")
        
        cursor.execute("SELECT id FROM trade_plan WHERE date = ? AND code = ?", (today, row['code']))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE trade_plan SET entry_price=?, stop_price=?, weight=?, status=?,
                track=?, rs_score=?, vcp_ratio=?, rationale=? WHERE date=? AND code=?
            """, (entry, stop, weight, status, track_name, row['rs_score'], vcp, rationale, today, row['code']))
        else:
            cursor.execute("""
                INSERT INTO trade_plan (date, code, name, entry_price, stop_price, weight, status, track, rs_score, vcp_ratio, rationale) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (today, row['code'], row['name'], entry, stop, weight, status, track_name, row['rs_score'], vcp, rationale))
    conn.commit()
    conn.close()

def generate_full_report():
    print("-" * 105)
    print(f" [TrendHunter v4.5 Master's Soul] 거장의 원칙과 정석 로직의 결합 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 105)
    
    raw_df = get_trend_candidates_db()
    final_list = []
    
    if not raw_df.empty:
        for _, row in raw_df.iterrows():
            if check_chart_pattern(row['code']):
                quality = get_supply_quality(row['code'])
                if "이탈" not in quality:
                    row['quality'] = quality
                    final_list.append(row)
    
    if final_list:
        all_themes = []
        for row in final_list:
            themes = get_themes_for_stock(row["code"])
            if themes: all_themes.extend(themes)
        top_theme = Counter(all_themes).most_common(1)[0][0] if all_themes else "독립강세"
        
        save_to_trade_plan(final_list, f"트랙 1: {top_theme}")
        
        for row in final_list:
            e, s, w, brk = calculate_survival_trade(row)
            mark = "🚨" if brk else "⏳" if row['vcp_ratio'] > 0.1 else "🎯"
            print(f" {mark} {row['name']:<10} | RS {row['rs_score']:2.0f} | {row['quality']} | VCP {row['vcp_ratio']:.2f} | 🎯:{e:>7,} | 🛡️:{s:>7,}")

        # [v4.5] 요약 테이블 업데이트
        conn = get_connection()
        res_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
        total = conn.execute(f"SELECT COUNT(*) FROM daily_analysis WHERE date='{res_date}'").fetchone()[0]
        s2 = conn.execute(f"SELECT COUNT(*) FROM daily_analysis WHERE date='{res_date}' AND close > sma_50 AND sma_50 > sma_150").fetchone()[0]
        avg_rs = conn.execute(f"SELECT AVG(rs_score) FROM daily_analysis WHERE date='{res_date}'").fetchone()[0] or 0
        conn.execute("INSERT OR REPLACE INTO market_summary (date, top_sector, active_leaders, stage2_ratio, market_rs, risk_level) VALUES (?,?,?,?,?,?)",
                     (res_date, top_theme, len(final_list), round(s2/total*100, 1), round(avg_rs, 1), "SAFE" if avg_rs > 45 else "CAUTION"))
        conn.commit(); conn.close()
    else:
        print("\n [!] 거장의 기준을 통과한 주도주가 없습니다. 현금을 확보하고 인내하십시오.")

    # TRACK 2 복구 (v6.0 정석 배당)
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    query_div = f"SELECT DISTINCT m.code, m.name, d.dividend_yield, m.roe FROM daily_analysis d JOIN master_info m ON d.code = m.code WHERE d.date = '{max_date}' AND d.dividend_yield >= 7.0 AND m.roe >= 10.0 ORDER BY d.dividend_yield DESC LIMIT 10"
    div_df = pd.read_sql_query(query_div, conn)
    if not div_df.empty:
        print(f"\n[🛡️ TRACK 2: 정석 고배당 (Trailing 12M)]")
        for _, r in div_df.iterrows():
            print(f" ▶ {r['name']:<10} | 배당:{r['dividend_yield']:>5.1f}% | ROE:{r['roe']:>5.1f}%")
    conn.close()
    print("-" * 105)

if __name__ == "__main__":
    generate_full_report()