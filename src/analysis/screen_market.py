"Track1/Track EX/Track2 통합 리포트 v2.4 (초슬림 원라인 브리핑)."
import pandas as pd
import numpy as np
from datetime import datetime
from src.db import get_connection
from src.analysis.market_filter import check_market_health
from collections import Counter
import os

def get_themes_for_stock(code):
    conn = get_connection()
    df = pd.read_sql_query("SELECT category_name FROM sectors_themes WHERE code = ? AND category_type = 'THEME'", conn, params=(code,))
    conn.close()
    return df["category_name"].tolist()

def get_trend_candidates_db():
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    query = f"""
    SELECT 
        d.date, d.code, m.name, m.market_type,
        d.close, d.amount, d.volume, d.rs_score,
        (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
        d.high_52w, d.low_52w, d.sma_20, d.sma_50, d.sma_150, d.sma_200,
        d.volume_sma_50, m.bsop_prfi, m.thtr_ntin, m.roe
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      AND d.close > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
      AND d.high_52w IS NOT NULL
      AND d.close >= d.low_52w * 1.25
      AND d.close >= d.high_52w * 0.80
      AND d.rs_score >= 80
      AND (d.vol_std_10d / d.vol_std_50d) < 0.9
      AND d.volume < (d.volume_sma_50 * 0.8)
      AND ((m.bsop_prfi > 0 AND m.thtr_ntin > 0) OR (d.rs_score >= 90))
    ORDER BY d.rs_score DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

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

def generate_full_report():
    print("-" * 100)
    print(f" [TrendHunter v2.4] 전설의 정석 (1-Line Brief) | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 100)
    
    market_status = check_market_health()
    status_str = "✅ [공격]" if not any(m['status'] == 'RED' for m in market_status) else "🚨 [방어]"
    indices = " / ".join([f"{m['name']}:{m['curr']:,.0f}" for m in market_status])
    print(f"[{status_str}] {indices}")

    raw_df = get_trend_candidates_db()
    final_list = []
    for _, row in raw_df.iterrows():
        if check_chart_pattern(row['code']):
            quality = get_supply_quality(row['code'])
            if "이탈" not in quality:
                row['quality'] = quality
                final_list.append(row)
    
    if final_list:
        trend_df = pd.DataFrame(final_list)
        themed_stocks = []
        unthemed_stocks = []
        all_themes = []
        for _, row in trend_df.iterrows():
            themes = get_themes_for_stock(row["code"])
            if themes: themed_stocks.append((row, themes)); all_themes.extend(themes)
            else: unthemed_stocks.append(row)

        top_1_theme = Counter(all_themes).most_common(1)[0][0] if all_themes else "기타"
        
        def print_one_line(row, weight, prefix):
            entry = get_breakout_price(row['high_52w'])
            stop = max(adjust_to_tick(entry * 0.93), int(row['sma_20']))
            print(f"{prefix} {row['name']:<10} ({row['code']}) | RS {row['rs_score']:2.0f} | {row['quality']} | 🎯진입:{entry:>8,} | 🛡️손절:{stop:>8,} | ⚓비중:{weight}")

        print(f"\n[🔥 TRACK 1: {top_1_theme}]")
        t1_c = 0
        for row, themes in themed_stocks:
            if top_1_theme in themes:
                print_one_line(row, "15%", " ▶")
                t1_c += 1
                if t1_c >= 3: break

        print(f"\n[🚀 TRACK EX: 독립강세]")
        for row in unthemed_stocks[:3]:
            print_one_line(row, " 3%", " ▶")

        print(f"\n[🏆 MARKET LEADERS: 틈새대장]")
        ml_c = 0
        for row, themes in themed_stocks:
            if top_1_theme not in themes:
                print_one_line(row, " 7%", " ▶")
                ml_c += 1
                if ml_c >= 3: break
    else:
        print("\n[🔍] 현재 전설의 기준을 통과한 성장주가 없습니다.")

    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    query_div = f"SELECT DISTINCT m.code, m.name, d.dividend_yield, m.roe FROM daily_analysis d JOIN master_info m ON d.code = m.code WHERE d.date = '{max_date}' AND d.dividend_yield >= 7.0 AND m.thtr_ntin > 0 AND m.roe >= 10.0 ORDER BY d.dividend_yield DESC LIMIT 3"
    div_df = pd.read_sql_query(query_div, conn)
    conn.close()
    
    print(f"\n[🛡️ TRACK 2: 고배당파킹]")
    for _, row in div_df.iterrows():
        print(f" ▶ {row['name']:<10} ({row['code']}) | 배당:{row['dividend_yield']:>5.1f}% | ROE:{row['roe']:>5.1f}% | ⚓비중:현금전량")

    print("-" * 100)

if __name__ == "__main__":
    generate_full_report()
