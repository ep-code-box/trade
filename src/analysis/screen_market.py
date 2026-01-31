"""Track1/Track2 후보군 리포트 출력. 실행: python -m src.analysis.screen_market"""
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
    # vcp_ratio NULL 제외(변동성 미계산 종목), RS 70 이상, VCP 수축 0.5 미만
    df = pd.read_sql_query(
        """
        SELECT date, code, name, market_type, close, amount, vcp_ratio, rs_score, sma_50
        FROM view_trend_candidates
        WHERE vcp_ratio IS NOT NULL AND vcp_ratio < 0.5 AND rs_score >= 70
        ORDER BY rs_score DESC, vcp_ratio ASC LIMIT 15
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
    print("=" * 56)
    print(f" [TrendHunter] 통합 투자 전략 리포트 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 56)
    
    print("\n[🔥 TRACK 1: 추세추종 - 공격형 주도주]")
    if trend_df.empty:
        print("포착된 주도주 없음.")
    else:
        for _, row in trend_df.iterrows():
            themes = get_themes_for_stock(row["code"])
            pivot = int(row["close"] * 1.01)
            stop = max(int(row["sma_50"]), int(row["close"] * 0.93))
            theme_str = ", ".join(themes) if themes else "정보 없음"
            vcp = row['vcp_ratio'] if pd.notna(row['vcp_ratio']) else 0
            print(f"▶ {row['name']} ({row['code']}) | RS: {row['rs_score']:.0f} | VCP: {vcp:.2f}")
            print(f"   - 테마: {theme_str}")
            print(f"   - [액션] 매수: {pivot:,}원 / 손절: {stop:,}원")
            print("-" * 45)
            
    print("\n[💰 TRACK 2: 고배당 뚜벅이 - 수비형 우량주]")
    if div_df.empty:
        print("포착된 고배당주 없음. (데이터 확인 필요)")
    else:
        for _, row in div_df.iterrows():
            print(f"▶ {row['name']} ({row['code']}) | 수익률: {row['dividend_yield']:.2f}% ({row['cycle']})")
            print(f"   - 현재가: {row['close']:,}원 | 예상배당금: {row['dps']:,}원")
            print("-" * 45)
            
    print("\n[AI 멘토의 뼈 때리는 조언]")
    print('"공격으로 수익을 내고, 배당으로 부를 지켜라. 계좌 분리는 원칙이다."')


if __name__ == "__main__":
    generate_full_report()