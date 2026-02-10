import sqlite3
from src.config import STOCK_DB_PATH

def create_views():
    conn = sqlite3.connect(STOCK_DB_PATH)
    cur = conn.cursor()
    
    # [Track 1] 뷰를 아주 단순화함 (복잡한 서브쿼리 제거)
    cur.execute("DROP VIEW IF EXISTS view_trend_candidates")
    cur.execute('''
        CREATE VIEW view_trend_candidates AS
        SELECT 
            d.date, d.code, m.name, m.market_type,
            d.close, d.amount, d.volume, d.volume_sma_50,
            d.sma_50, d.sma_150, d.sma_200, d.rs_score,
            (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
            d.high_52w
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
    ''')
    
    # [Track 2] 뚜벅이 뷰
    cur.execute("DROP VIEW IF EXISTS view_dividend_candidates")
    cur.execute('''
        CREATE VIEW view_dividend_candidates AS
        SELECT d.code, m.name, d.close, d.dividend_yield,
               COALESCE(m.dividend_cycle, '연배당') as cycle,
               COALESCE(m.per_stock_dvdn_amt, 0) as dps
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
        WHERE d.dividend_yield >= 5.0
    ''')
    
    conn.commit()
    conn.close()
    print("Views simplified and created successfully.")

if __name__ == "__main__":
    create_views()