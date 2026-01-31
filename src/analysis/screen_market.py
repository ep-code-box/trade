"Track1/Track EX/Track2 통합 리포트 (Direct SQL - No Duplicates)."
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

def get_trend_candidates_direct():
    """뷰를 거치지 않고 직접 초결벽주의 원칙으로 쿼리"""
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    query = f"""
    SELECT 
        d.date, d.code, m.name, m.market_type,
        d.close, d.amount, d.volume, d.rs_score,
        (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
        d.high_52w, d.sma_50
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      AND d.close > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
      AND d.close >= d.high_52w * 0.85
      AND d.rs_score >= 70
      AND (d.vol_std_10d / d.vol_std_50d) < 0.8
      AND d.volume < (
          SELECT d2.volume FROM daily_analysis d2 
          WHERE d2.code = d.code AND d2.date < d.date 
          ORDER BY d2.date DESC LIMIT 1
      ) * 0.6
    ORDER BY d.rs_score DESC, vcp_ratio ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def generate_full_report():
    trend_df = get_trend_candidates_direct()
    
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    # 중복 제거 및 최신 데이터 한정
    query_div = f"""
    SELECT DISTINCT m.code, m.name, d.close, d.dividend_yield,
           COALESCE(m.dividend_cycle, '연배당') as cycle,
           COALESCE(m.per_stock_dvdn_amt, 0) as dps
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.dividend_yield >= 5.0
    ORDER BY d.dividend_yield DESC LIMIT 15
    """
    div_df = pd.read_sql_query(query_div, conn)
    conn.close()
    
    print("=" * 60)
    print(f" [TrendHunter] 통합 투자 전략 리포트 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 60)

    themed_list = []
    extra_list = []

    for _, row in trend_df.iterrows():
        themes = get_themes_for_stock(row["code"])
        if themes:
            themed_list.append((row, themes))
        else:
            extra_list.append(row)

    print(f"\n[🔥 TRACK 1: 테마 주도주] - 집단적 시세 분출")
    if not themed_list:
        print("   포착된 테마주 없음.")
    else:
        for row, themes in themed_list:
            pivot = int(row["close"] * 1.01)
            stop = max(int(row["sma_50"]), int(row["close"] * 0.93))
            print(f"▶ {row['name']} ({row['code']}) | RS: {row['rs_score']:.0f} | VCP: {row['vcp_ratio']:.2f}")
            print(f"   - 테마: {', '.join(themes)}")
            print(f"   - [액션] 매수: {pivot:,}원 돌파 / 손절: {stop:,}원")
            print("-" * 50)

    print(f"\n[🚀 TRACK EX: 테마 외 독립 강세주] - 개별 모멘텀")
    if not extra_list:
        print("   현재 테마에 속하지 않은 독립 강세주가 없습니다.")
    else:
        for row in extra_list:
            pivot = int(row["close"] * 1.01)
            stop = max(int(row["sma_50"]), int(row["close"] * 0.93))
            print(f"▶ {row['name']} ({row['code']}) | RS: {row['rs_score']:.0f} | VCP: {row['vcp_ratio']:.2f}")
            print(f"   - [액션] 매수: {pivot:,}원 돌파 / 손절: {stop:,}원")
            print("-" * 50)

    print(f"\n[💰 TRACK 2: 고배당 뚜벅이] - 수비형 우량주")
    if div_df.empty:
        print("   포착된 고배당주 없음.")
    else:
        for _, row in div_df.iterrows():
            print(f"▶ {row['name']} ({row['code']}) | 수익률: {row['dividend_yield']:.2f}% ({row['cycle']})")
            print(f"   - 현재가: {row['close']:,}원 | 예상배당금: {row['dps']:,}원")
            print("-" * 50)

    print("\n[AI 멘토의 최종 조언]")
    print("\"시장은 인내심 없는 자의 돈을 인내심 있는 자에게 옮기는 기계다.\"")

if __name__ == "__main__":
    generate_full_report()