"Track1/Track EX/Track2 통합 리포트 (Direct SQL - No Duplicates)."
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.analysis.market_filter import check_market_health
from collections import Counter

def get_themes_for_stock(code):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT category_name FROM sectors_themes WHERE code = ? AND category_type = 'THEME'",
        conn,
        params=(code,),
    )
    conn.close()
    return df["category_name"].tolist()

def get_trend_candidates_direct():
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    query = f"""
    SELECT 
        d.date, d.code, m.name, m.market_type,
        d.close, d.amount, d.volume, d.rs_score,
        (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
        d.high_52w, d.sma_20, d.sma_50, d.sma_150, d.sma_200,
        d.volume_sma_50, m.bsop_prfi, m.thtr_ntin, m.roe
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      AND d.close > d.sma_20 AND d.sma_20 > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
      AND d.high_52w IS NOT NULL
      AND d.close >= d.high_52w * 0.85
      AND d.rs_score >= 80
      AND (d.close / d.sma_200) < 2.0
      AND (d.vol_std_10d / d.vol_std_50d) < 0.9
      AND d.volume < (d.volume_sma_50 * 0.7)
      AND ((m.bsop_prfi > 0 AND m.thtr_ntin > 0) OR (d.rs_score >= 90))
    ORDER BY d.rs_score DESC, vcp_ratio ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_tick_size(price):
    if price < 2000: return 1
    if price < 5000: return 5
    if price < 20000: return 10
    if price < 50000: return 50
    if price < 200000: return 100
    if price < 500000: return 500
    return 1000

def adjust_to_tick(price, method='up'):
    tick = get_tick_size(price)
    if method == 'up':
        return ((int(price) // tick) + 1) * tick
    else:
        return (int(price) // tick) * tick

def get_breakout_price(high_52w):
    target = high_52w * 1.02
    if 98000 <= target < 100000: target = 100500
    elif 48000 <= target < 50000: target = 50500
    elif 9800 <= target < 10000: target = 10100
    elif 4900 <= target < 5000: target = 5050
    return adjust_to_tick(target, 'up')

def check_chart_pattern(code):
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT open, high, low, close, volume FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 10", conn
    )
    conn.close()
    if len(df) < 10: return False
    cols = ['open', 'high', 'low', 'close', 'volume']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    if (df['close'] == 0).any(): return False
    recent = df.head(5).copy()
    recent['fluctuation'] = (recent['high'] - recent['low']) / recent['close']
    if recent['fluctuation'].mean() > 0.04: return False
    recent['upper_shadow'] = recent.apply(lambda x: (x['high'] - x['close']) if x['close'] > x['open'] else (x['high'] - x['open']), axis=1)
    if (recent['upper_shadow'] / recent['close']).mean() > 0.02: return False
    down_days = df[df['close'] < df['open']]
    up_days = df[df['close'] > df['open']]
    if not down_days.empty and not up_days.empty:
        if down_days['volume'].mean() > (up_days['volume'].mean() * 1.2): return False 
    return True

def generate_full_report():
    print("=" * 60)
    print(f" [TrendHunter] 오늘의 S급 마스터 종목 보고서 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 60)
    print("\n[🚦 시장 환경 분석]")
    market_status = check_market_health()
    is_dangerous = False
    for m in market_status:
        icon = "🟢" if m['status'] == 'GREEN' else "🔴"
        val_str = f"{m['curr']:,.2f}" if m['curr'] > 0 else "N/A"
        print(f"   {icon} {m['name']}: {val_str}")
        if m['status'] == 'RED': is_dangerous = True
    if is_dangerous:
        print("\n   ⚠️ 시장 하락 추세. 공격적 매수 금지.")
    else:
        print("\n   ✅ 시장 상승 추세. 주도주 매매 적기.")

    raw_trend_df = get_trend_candidates_direct()
    print("   >> 차트 패턴 및 거래량 수축(VDU) 정밀 분석 중...")
    valid_indices = [idx for idx, row in raw_trend_df.iterrows() if check_chart_pattern(row['code'])]
    trend_df = raw_trend_df.loc[valid_indices].copy()
    
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    query_div = f"SELECT DISTINCT m.code, m.name, d.close, d.dividend_yield, COALESCE(m.dividend_cycle, '연배당') as cycle, m.roe FROM daily_analysis d JOIN master_info m ON d.code = m.code WHERE d.date = '{max_date}' AND d.dividend_yield >= 7.0 AND m.thtr_ntin > 0 AND m.roe >= 10.0 ORDER BY d.dividend_yield DESC LIMIT 15"
    div_df = pd.read_sql_query(query_div, conn)
    conn.close()
    
    themed_stocks = []
    unthemed_stocks = []
    all_themes = []
    for _, row in trend_df.iterrows():
        themes = get_themes_for_stock(row["code"])
        if themes:
            themed_stocks.append((row, themes))
            all_themes.extend(themes)
        else:
            unthemed_stocks.append(row)

    theme_counts = Counter(all_themes)
    top_3_themes = [t for t, c in theme_counts.most_common(3)]
    track1_list = [(r, t) for r, t in themed_stocks if any(theme in t for theme in top_3_themes)]
    market_leaders = [(r, t) for r, t in themed_stocks if not any(theme in t for theme in top_3_themes)]

    print(f"\n[🔥 TRACK 1: 시장 주도 테마 섹터 (Top 2 압축)]")
    if not track1_list:
        print("   조건을 만족하는 주도 테마주가 없습니다.")
    else:
        theme_groups = {t: [] for t in top_3_themes}
        for row, themes in track1_list:
            for t in top_3_themes:
                if t in themes:
                    theme_groups[t].append(row)
                    break
        for t in top_3_themes:
            for row in sorted(theme_groups[t], key=lambda x: x["rs_score"], reverse=True)[:2]:
                entry = get_breakout_price(row["high_52w"])
                stop = max(adjust_to_tick(entry * 0.93), int(row["sma_20"]))
                print(f"\n▶ {row['name']} ({row['code']}) | RS {row['rs_score']:.0f} | 테마: {t}")
                print(f"   [진입] {entry:,}원  |  [손절] {stop:,}원")

    print(f"\n[🏆 MARKET LEADERS: 틈새시장 대장주 (Top 5)]")
    if not market_leaders:
        print("   조건을 만족하는 틈새시장 대장주가 없습니다.")
    else:
        for row, themes in market_leaders[:5]:
            entry = get_breakout_price(row["high_52w"])
            stop = max(adjust_to_tick(entry * 0.93), int(row["sma_20"]))
            print(f"\n▶ {row['name']} ({row['code']}) | RS {row['rs_score']:.0f} | 테마: {themes[0]}")
            print(f"   [진입] {entry:,}원  |  [손절] {stop:,}원")

    print(f"\n[🚀 TRACK EX: 무소속 독립 강세주 (Top 5)]")
    if not unthemed_stocks:
        print("   조건을 만족하는 독립 강세주가 없습니다.")
    else:
        for row in unthemed_stocks[:5]:
            entry = get_breakout_price(row["high_52w"])
            stop = max(adjust_to_tick(entry * 0.93), int(row["sma_20"]))
            print(f"\n▶ {row['name']} ({row['code']}) | RS {row['rs_score']:.0f}")
            print(f"   [진입] {entry:,}원  |  [손절] {stop:,}원 | [비중] 3% 미만")

    print(f"\n[🛡️ TRACK 2: 고배당 안전주 (수익률 7%↑ & 흑자 & ROE 10%↑)]")
    if div_df.empty:
        print("   조건을 만족하는 고배당주가 없습니다.")
    else:
        for _, row in div_df.iterrows():
            print(f"▶ {row['name']} ({row['code']}) | 수익률: {row['dividend_yield']:.2f}% | ROE: {row['roe']:.1f}%")

    print("\n[AI 멘토의 행동 지침]")
    print("""마스터는 예측하지 않습니다. 오직 원칙이라는 선을 넘는 놈만 사냥합니다.""")

if __name__ == "__main__":
    generate_full_report()
