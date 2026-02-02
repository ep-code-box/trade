"전 종목 수급 업데이트 (Async 20 TPS 고속 버전)."
import asyncio
import time
import pandas as pd
from datetime import datetime, timedelta
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_async

async def fetch_supply_single_async(code, start_date, end_date):
    path = "/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_date, "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D"
    }
    res = await kis_get_async(path, params=params, tr_id="FHKST01010900")
    return code, res.get('output') if res and "output" in res else None

def safe_int(val):
    try: return int(val) if val and str(val).strip() != "" else 0
    except: return 0

def update_supply_batch_sync(results):
    if not results: return
    conn = get_connection()
    cur = conn.cursor()
    for code, data_list in results:
        for row in data_list:
            date = row['stck_bsop_date']
            frgn, orgn = safe_int(row.get('frgn_ntby_qty')), safe_int(row.get('orgn_ntby_qty'))
            prsn, fin = safe_int(row.get('prsn_ntby_qty')), safe_int(row.get('finc_invt_ntby_qty'))
            inv, pension, etc = safe_int(row.get('invt_trust_ntby_qty')), safe_int(row.get('pension_ntby_qty')), safe_int(row.get('etc_corp_ntby_qty'))
            cur.execute("""
                UPDATE daily_analysis SET frgn_net_buy=?, orgn_net_buy=?, prsn_net_buy=?, fin_net_buy=?, inv_net_buy=?, pension_net_buy=?, etc_net_buy=?
                WHERE code=? AND date=?
            """, (frgn, orgn, prsn, fin, inv, pension, etc, code, date))
    conn.commit()
    conn.close()

async def main_async():
    if not get_access_token(): return
    conn = get_connection()
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) = 6", conn)
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    # [v2.9 임시 주석] 데이터 복구를 위해 전체 강제 수집
    # completed_codes = set(pd.read_sql_query(f"SELECT code FROM daily_analysis WHERE date='{max_date}' AND frgn_net_buy IS NOT NULL", conn)['code'])
    completed_codes = set() 
    conn.close()

    target_stocks = stocks[~stocks['code'].isin(completed_codes)]
    total = len(target_stocks)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    print(f"🚀 수급 비동기 고속 수집 시작: {total}개 종목 (Target: 20 TPS)")
    start_time = time.time()
    completed, batch = 0, []
    
    sem = asyncio.Semaphore(100)
    async def task(r):
        async with sem: return await fetch_supply_single_async(r['code'], start_date, end_date)

    futures = [task(r) for _, r in target_stocks.iterrows()]
    for fut in asyncio.as_completed(futures):
        code, data = await fut
        if data: batch.append((code, data))
        completed += 1
        
        if len(batch) >= 100 or completed == total:
            asyncio.create_task(asyncio.to_thread(update_supply_batch_sync, list(batch)))
            batch = []
            
        if completed % 100 == 0 or completed == total:
            print(f"[{completed}/{total}] 수급 진행 중... (현재 속도: {completed/(time.time()-start_time):.2f} TPS)")

    await asyncio.sleep(2)
    print(f"\n✅ 수급 수집 완료. (소요시간: {time.time()-start_time:.1f}초)")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
