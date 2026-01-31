"""Track1/Track2 후보 뷰 생성. 실행: python -m src.scripts.setup_views"""
from src.db import get_connection


def create_views():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DROP VIEW IF EXISTS view_trend_candidates")
    # Track 1: 추세추종 — 상승추세 + 변동성 수축(VCP) + 거래량 드라이업 + 52주고가 근처
    # vcp_ratio = 10일 변동성/50일 변동성 (0 나누기 방지)
    cur.execute("""
        CREATE VIEW view_trend_candidates AS
        SELECT 
            d.date, d.code, m.name, m.market_type,
            d.close, d.amount, d.volume, d.volume_sma_50,
            d.sma_50, d.sma_150, d.sma_200, 
            d.rs_score,
            (d.vol_std_10d / NULLIF(d.vol_std_50d, 0)) as vcp_ratio,
            d.high_52w
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
        WHERE d.date = (SELECT MAX(date) FROM daily_analysis)
          AND d.amount >= 3000000000
          AND d.vol_std_50d > 0
          AND d.close > d.sma_50 
          AND d.sma_50 > d.sma_150 
          AND d.sma_150 > d.sma_200 
          AND d.vol_std_10d < d.vol_std_50d * 0.8 
          AND (d.volume_sma_50 IS NULL OR d.volume <= d.volume_sma_50 * 1.0)
          AND d.high_52w > 0 AND d.close >= d.high_52w * 0.75
        ORDER BY d.rs_score DESC, vcp_ratio ASC
    """)

    cur.execute("DROP VIEW IF EXISTS view_dividend_candidates")
    cur.execute("""
        CREATE VIEW view_dividend_candidates AS
        SELECT 
            m.code, m.name, m.market_type,
            d.close, 
            (CAST(m.stck_sdpr AS REAL) / d.close) * 100 as est_yield_from_base,
            m.per, m.pbr,
            m.sale_account, m.bsop_prfi, m.thtr_ntin
        FROM master_info m
        JOIN daily_analysis d ON m.code = d.code
        WHERE d.date = (SELECT MAX(date) FROM daily_analysis)
          AND d.market_cap >= 500000000000
          AND m.thtr_ntin > 0
    """)

    conn.commit()
    conn.close()
    print("Views created successfully.")


if __name__ == "__main__":
    create_views()
