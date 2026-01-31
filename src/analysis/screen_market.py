"Track1/Track EX/Track2 통합 리포트. 실행: python3 run.py screen"
import pandas as pd
from datetime import datetime
from src.db import get_connection

def get_themes_for_stock(code):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT category_name FROM sectors_themes WHERE code = ? AND category_type = 'THEME'",
        conn,
        params=(code,),
    )
    conn.close()
    return df["category_name"].tolist()

def get_trend_candidates():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT date, code, name, market_type, close, amount, vcp_ratio, rs_score, sma_50
        FROM view_trend_candidates
        WHERE vcp_ratio IS NOT NULL AND vcp_ratio < 0.5 AND rs_score >= 70
        ORDER BY rs_score DESC, vcp_ratio ASC
        """,
        conn,
    )
    conn.close()
    return df

def get_dividend_candidates():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT d.code, m.name, d.close, d.dividend_yield,
               COALESCE(m.dividend_cycle, '연배당') as cycle,
               COALESCE(m.per_stock_dvdn_amt, 0) as dps
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
        WHERE d.date = (SELECT MAX(date) FROM daily_analysis)
          AND d.dividend_yield >= 5.0
        ORDER BY d.dividend_yield DESC LIMIT 15
        """,
        conn,
    )
    conn.close()
    return df

def generate_full_report():
    trend_df = get_trend_candidates()
    div_df = get_dividend_candidates()
    
    print("=" * 60)
    print(f" [TrendHunter] 2-Track + EX 통합 투자 리포트 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 60)

    themed_list = []
    extra_list = []

    for _, row in trend_df.iterrows():
        themes = get_themes_for_stock(row["code"])
        if themes:
            themed_list.append((row, themes))
        else:
            extra_list.append(row)

    # 1. TRACK 1: 테마 주도주
    print(f"\n[🔥 TRACK 1: 테마 주도주] - 집단적 시세 분출")
    if not themed_list:
        print("   포착된 테마주 없음.")
    else:
        for row, themes in themed_list[:15]:
            pivot = int(row["close"] * 1.01)
            stop = max(int(row["sma_50"]), int(row["close"] * 0.93))
            print(f"▶ {row['name']} ({row['code']}) | RS: {row['rs_score']:.0f} | VCP: {row['vcp_ratio']:.2f}")
            print(f"   - 테마: {', '.join(themes)}")
            print(f"   - [액션] 매수: {pivot:,}원 / 손절: {stop:,}원")
            print("-" * 50)

    # 2. TRACK EX: 독립 강세주
    print(f"\n[🚀 TRACK EX: 테마 외 독립 강세주] - 개별 모멘텀")
    if not extra_list:
        print("   현재 테마에 속하지 않은 독립 강세주가 없습니다.")
    else:
        for row in extra_list[:10]:
            pivot = int(row["close"] * 1.01)
            stop = max(int(row["sma_50"]), int(row["close"] * 0.93))
            print(f"▶ {row['name']} ({row['code']}) | RS: {row['rs_score']:.0f} | VCP: {row['vcp_ratio']:.2f}")
            print(f"   - [액션] 매수: {pivot:,}원 / 손절: {stop:,}원")
            print("-" * 50)

    # 3. TRACK 2: 고배당 뚜벅이
    print(f"\n[💰 TRACK 2: 고배당 뚜벅이] - 수비형 우량주")
    if div_df.empty:
        print("   포착된 고배당주 없음.")
    else:
        for _, row in div_df.iterrows():
            print(f"▶ {row['name']} ({row['code']}) | 수익률: {row['dividend_yield']:.2f}% ({row['cycle']})")
            print(f"   - 현재가: {row['close']:,}원 | 예상배당금: {row['dps']:,}원")
            print("-" * 50)

    print("\n[AI 멘토의 최종 조언]")
    print("""테마주가 득세할 때 개별주가 안 보인다면, 시장의 돈이 한곳으로 쏠려있다는 뜻이다.""")
    print("""무리하게 종목을 찾지 말고, 돈이 몰리는 곳의 대장을 잡아라.""")

if __name__ == "__main__":
    generate_full_report()