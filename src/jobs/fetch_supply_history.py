"""전 종목의 투자자별 매매동향(수급)을 수집하여 DB에 업데이트합니다."""
import time
import pandas as pd
from src.db import get_connection
from src.kis_api import kis_get_raw
from datetime import datetime, timedelta

def get_target_stocks():
    conn = get_connection()
    # 상장된 전 종목 가져오기
    query = "SELECT code, name FROM master_info WHERE LENGTH(code) = 6"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def fetch_supply_history(code, start_date, end_date):
    path = "/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D"
    }
    
    # 0.1초 딜레이 (초당 10건 제한)
    time.sleep(0.1)
    res = kis_get_raw(path, params=params, tr_id="FHKST01010900")
    
    if not res or "output" not in res:
        return None
        
    return res['output']

def safe_int(val):
    """빈 문자열이나 잘못된 값을 0으로 변환"""
    try:
        if not val or str(val).strip() == "":
            return 0
        return int(val)
    except (ValueError, TypeError):
        return 0

def update_supply_to_db(code, data_list):
    if not data_list:
        return

    conn = get_connection()
    cur = conn.cursor()
    
    for row in data_list:
        date = row['stck_bsop_date']
        
        # [초결벽주의] 모든 투자 주체 데이터 추출
        frgn = safe_int(row.get('frgn_ntby_qty'))
        orgn = safe_int(row.get('orgn_ntby_qty'))
        prsn = safe_int(row.get('prsn_ntby_qty'))
        fin = safe_int(row.get('finc_invt_ntby_qty'))
        inv = safe_int(row.get('invt_trust_ntby_qty'))
        pension = safe_int(row.get('pension_ntby_qty'))
        etc = safe_int(row.get('etc_corp_ntby_qty'))
        
        # 해당 날짜, 종목의 row에 수급 데이터 업데이트
        cur.execute("""
            UPDATE daily_analysis 
            SET frgn_net_buy = ?, orgn_net_buy = ?,
                prsn_net_buy = ?, fin_net_buy = ?, inv_net_buy = ?, pension_net_buy = ?, etc_net_buy = ?
            WHERE code = ? AND date = ?
        """, (frgn, orgn, prsn, fin, inv, pension, etc, code, date))
        
    conn.commit()
    conn.close()

def main():
    stocks = get_target_stocks()
    total = len(stocks)
    
    # 최근 1개월치만 업데이트 (너무 과거는 의미 없음 + 시간 절약)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    print(f"전 종목 {total}개 수급 데이터 업데이트 시작 ({start_date}~{end_date})...")
    
    for idx, row in stocks.iterrows():
        code = row['code']
        name = row['name']
        print(f"[{idx+1}/{total}] {name}({code}) 수급 업데이트 중...", end="\r")
        
        try:
            data = fetch_supply_history(code, start_date, end_date)
            if data:
                update_supply_to_db(code, data)
        except Exception as e:
            print(f"\n[Error] {name}: {e}")
            
    print("\n수급 데이터 업데이트 완료.")

if __name__ == "__main__":
    main()
