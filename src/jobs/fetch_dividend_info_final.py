"""[v15.2] API 배당수익률 직송 엔진 (Direct Mapping). 실행: python -m src.jobs.fetch_dividend_info_final"""
import asyncio
import time
import pandas as pd
from datetime import datetime
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw_async

async def fetch_yield_direct_async(code, name, sem):
    async with sem:
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010100", use_real=True)
        if res and res.get("output"):
            out = res["output"]
            # API 제공 배당 수익률 직접 사용 (Recorded Yield)
            dy = float(out.get("dvdn_yield") or 0)
            dps = int(float(out.get("per_stck_dvdn_amt") or 0))
            real_name = out.get("hts_kor_isnm", name)
            return {"code": code, "name": real_name, "yield": dy, "dps": dps}
        return None

def batch_update_db(results):
    if not results: return
    conn = get_connection()
    cur = conn.cursor()
    max_date = cur.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    for r in results:
        if not r: continue
        # Recorded DPS 및 Name 정화
        cur.execute("UPDATE master_info SET per_stock_dvdn_amt = ?, name = ? WHERE code = ?", (r['dps'], r['name'], r['code']))
        # API 직송 배당수익률 업데이트
        cur.execute("""
            UPDATE daily_analysis 
            SET dividend_yield = ? 
            WHERE code = ? AND date = ?
        """, (r['yield'], r['code'], max_date))
    
    conn.commit()
    conn.close()

async def main_async():
    if not get_access_token(): return
    conn = get_connection()
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) = 6", conn)
    conn.close()
    
    total = len(stocks)
    print(f"🚀 [v15.2] API 정밀 배당수익률(dvdn_yield) 직송 시작: {total}개 종목")
    
    sem = asyncio.Semaphore(30)
    batch_size = 100
    start_time = time.time()
    
    for i in range(0, total, batch_size):
        chunk = stocks.iloc[i:i+batch_size]
        tasks = [fetch_yield_direct_async(row['code'], row['name'], sem) for _, row in chunk.iterrows()]
        results = await asyncio.gather(*tasks)
        batch_update_db(results)
        print(f"[{min(i+batch_size, total)}/{total}] 진행 중...", end="\r")

    print(f"\n✅ 완료. (소요시간: {time.time()-start_time:.1f}초)")

def main(): asyncio.run(main_async())
if __name__ == "__main__": main()