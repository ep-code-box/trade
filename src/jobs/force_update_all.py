"""전 종목 OHLCV 데이터를 강제 업데이트하여 DB의 무결성을 확보합니다."""
import time
import pandas as pd
from src.db import get_connection
from src.jobs.fetch_daily_price import fetch_price_history, process_and_save
from datetime import datetime, timedelta

def update_all_stocks():
    conn = get_connection()
    # 상장된 전 종목 가져오기
    query = "SELECT code, name FROM master_info WHERE LENGTH(code) = 6"
    all_stocks = pd.read_sql_query(query, conn)
    conn.close()
    
    total = len(all_stocks)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    print(f"전 종목 {total}개 데이터 풀 업데이트 시작 (예상 소요시간: 40분)...")
    print("API 호출 제한을 준수하며 진행합니다.")
    
    for idx, row in all_stocks.iterrows():
        code = row['code']
        name = row['name']
        print(f"[{idx+1}/{total}] {name}({code}) 처리 중...", end="\r")
        
        try:
            data = fetch_price_history(code, start_date, end_date)
            if data:
                process_and_save(code, data)
        except Exception as e:
            print(f"\n[오류] {name}({code}): {e}")
        
        # API 안전장치 (0.1초 딜레이)
        time.sleep(0.1)
        
    print("\n전 종목 업데이트 완료. 지표 재계산을 수행하세요.")

if __name__ == "__main__":
    update_all_stocks()
