"""RS 80점 이상 정예 종목의 OHLCV 데이터를 강제 업데이트하여 장중 고가를 복구합니다."""
import time
import pandas as pd
from src.db import get_connection
from src.jobs.fetch_daily_price import fetch_price_history, process_and_save
from datetime import datetime, timedelta

def update_elite_stocks():
    conn = get_connection()
    # RS 80점 이상 + 거래대금 30억 이상인 종목만 추출
    query = """
    SELECT DISTINCT code, name FROM daily_analysis d
    JOIN master_info m USING(code)
    WHERE d.date = (SELECT MAX(date) FROM daily_analysis)
      AND d.rs_score >= 80
      AND d.amount >= 3000000000
    """
    elite_df = pd.read_sql_query(query, conn)
    conn.close()
    
    total = len(elite_df)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    print(f"정예 종목 {total}개 데이터 긴급 복구 시작...")
    
    for idx, row in elite_df.iterrows():
        code = row['code']
        name = row['name']
        print(f"[{idx+1}/{total}] {name}({code}) 업데이트 중...", end="\r")
        
        data = fetch_price_history(code, start_date, end_date)
        if data:
            process_and_save(code, data)
        
        # API 부하 방지 (초당 10건 제한 고려)
        time.sleep(0.1)
        
    print("\n정예 종목 복구 완료.")

if __name__ == "__main__":
    update_elite_stocks()
