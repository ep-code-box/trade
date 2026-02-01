"""RS 80점 이상 전 종목의 수급(외인/기관)을 전수 조사하여 '수급 우량주'만 선별합니다."""
import time
import pandas as pd
from src.db import get_connection
from src.kis_api import kis_get_raw
from datetime import datetime, timedelta

def get_high_rs_stocks():
    conn = get_connection()
    # RS 80점 이상인 종목만 추출
    query = """
    SELECT DISTINCT code, name, rs_score FROM daily_analysis d
    JOIN master_info m USING(code)
    WHERE d.date = (SELECT MAX(date) FROM daily_analysis)
      AND d.rs_score >= 80
    ORDER BY d.rs_score DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def check_supply_batch(stocks):
    results = []
    total = len(stocks)
    
    # 최근 5일 기준 (오늘 포함)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    
    print(f"RS 80+ 종목 {total}개 수급 전수 조사 시작 ({start_date}~{end_date})...")
    print("-" * 60)
    print(f"{ '종목명':<10} | {'RS':<3} | {'외인(5일)':>10} | {'기관(5일)':>10} | {'판정'}")
    print("-" * 60)
    
    for idx, row in stocks.iterrows():
        code = row['code']
        name = row['name']
        rs = row['rs_score']
        
        path = "/uapi/domestic-stock/v1/quotations/inquire-investor"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D"
        }
        
        try:
            res = kis_get_raw(path, params=params, tr_id="FHKST01010900", delay=0.1) # 딜레이 약간 줌
            
            if not res or "output" not in res:
                continue
                
            frgn_sum = 0
            orgn_sum = 0
            
            # 최근 5일치 합산
            for day_data in res['output'][:5]:
                frgn_sum += int(day_data['frgn_ntby_qty'])
                orgn_sum += int(day_data['orgn_ntby_qty'])
            
            status = "Unknown"
            if frgn_sum < 0 and orgn_sum < 0:
                status = "🚨 양매도"
            elif frgn_sum > 0 and orgn_sum > 0:
                status = "🌟 쌍끌이"
            elif frgn_sum > 0:
                status = "✅ 외인주도"
            elif orgn_sum > 0:
                status = "✅ 기관주도"
            
            print(f"{name:<10} | {rs:.0f}  | {frgn_sum:>10,} | {orgn_sum:>10,} | {status}")
            
            results.append({
                "code": code,
                "name": name,
                "frgn_sum": frgn_sum,
                "orgn_sum": orgn_sum,
                "status": status
            })
            
        except Exception:
            pass
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    stocks = get_high_rs_stocks()
    # 시간 관계상 상위 50개만 먼저 보여드리고, 나머지는 계속 돌리겠습니다.
    # 전체를 원하시면 stocks 전체를 넣으면 됩니다.
    df = check_supply_batch(stocks) # 전체 실행
    
    # 결과를 CSV로 저장 (나중에 분석용)
    df.to_csv("supply_check_result.csv", index=False)
    print(f"\n총 {len(df)}개 종목 수급 분석 완료. 'supply_check_result.csv' 저장됨.")
