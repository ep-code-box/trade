"""전체 상장 종목의 수급(외인/기관)을 전수 조사하여 데이터베이스를 구축합니다."""
import time
import pandas as pd
from src.db import get_connection
from src.kis_api import kis_get_raw
from datetime import datetime, timedelta

def get_all_stocks():
    conn = get_connection()
    # 상장된 전 종목 가져오기 (ETF 등 일부 제외)
    query = "SELECT code, name FROM master_info WHERE LENGTH(code) = 6 AND market_type IN ('KOSPI', 'KOSDAQ')"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def check_supply_batch(stocks):
    results = []
    total = len(stocks)
    
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    
    print(f"전 종목 {total}개 수급 전수 조사 시작...")
    print("-" * 60)
    print(f"{'No.':<5} | {'종목명':<12} | {'외인(5일)':>12} | {'기관(5일)':>12} | {'판정'}")
    print("-" * 60)
    
    for idx, row in stocks.iterrows():
        code = row['code']
        name = row['name']
        
        path = "/uapi/domestic-stock/v1/quotations/inquire-investor"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D"
        }
        
        try:
            res = kis_get_raw(path, params=params, tr_id="FHKST01010900", delay=0.1)
            
            if not res or "output" not in res or not res['output']:
                continue
                
            frgn_sum = sum(int(d.get('frgn_ntby_qty', 0)) for d in res['output'])
            orgn_sum = sum(int(d.get('orgn_ntby_qty', 0)) for d in res['output'])
            
            status = "Unknown"
            if frgn_sum < 0 and orgn_sum < 0: status = "🚨 양매도"
            elif frgn_sum > 0 and orgn_sum > 0: status = "🌟 쌍끌이"
            elif frgn_sum > 0: status = "✅ 외인주도"
            elif orgn_sum > 0: status = "✅ 기관주도"
            
            if (idx+1) % 100 == 0: # 100개마다 진행상황 출력
                 print(f"{idx+1:<5} | {name:<12} | {frgn_sum:>12,} | {orgn_sum:>12,} | {status}")
            
            results.append({
                "code": code,
                "name": name,
                "frgn_sum": frgn_sum,
                "orgn_sum": orgn_sum,
                "status": status
            })
            
        except Exception as e:
            print(f"Error on {code}: {e}")
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    stocks_to_scan = get_all_stocks()
    df_result = check_supply_batch(stocks_to_scan)
    
    # 결과를 CSV로 저장
    df_result.to_csv("full_supply_check_result.csv", index=False)
    print(f"\n총 {len(df_result)}개 종목 수급 분석 완료. 'full_supply_check_result.csv' 저장됨.")