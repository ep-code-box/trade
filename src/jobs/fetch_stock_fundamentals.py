"""전 종목 펀더멘털 업데이트 (Async 20 TPS 고속 버전)."""
import asyncio
import time
import pandas as pd
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_async

async def fetch_fundamental_single_async(code):
    path = "/uapi/domestic-stock/v1/quotations/inquire-stability"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = await kis_get_async(path, params=params, tr_id="FHKST01010600")
    return code, res.get('output') if res and "output" in res else None

def update_fundamental_batch_sync(results):
    if not results: return
    conn = get_connection()
    cur = conn.cursor()
    for code, data in results:
        # [v3.5] ROE 날짜 접두어 제거 로직 통합
        roe_raw = str(data.get('roe_val', 0)).strip()
        try:
            roe = float(roe_raw[6:]) if len(roe_raw) > 6 else float(roe_raw)
        except: roe = 0.0
        
        cur.execute("""
            UPDATE master_info SET roe = ?, updated_at = datetime('now') WHERE code = ?
        """, (roe, code))
    conn.commit()
    conn.close()

async def main_async():
    if not get_access_token(): return
    conn = get_connection()
    # ROE가 아직 수집되지 않은 종목 위주로 타겟팅 (혹은 전체)
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) = 6", conn)
    conn.close()

    total = len(stocks)
    print(f"🚀 펀더멘털 비동기 고속 수집 시작: {total}개 종목 (Target: 20 TPS)")
    start_time = time.time()
    completed, batch = 0, []
    
    sem = asyncio.Semaphore(100)
    async def task(c):
        async with sem: return await fetch_fundamental_single_async(c)

    futures = [task(r['code']) for _, r in stocks.iterrows()]
    for fut in asyncio.as_completed(futures):
        code, data = await fut
        if data: batch.append((code, data))
        completed += 1
        
        if len(batch) >= 100 or completed == total:
            asyncio.create_task(asyncio.to_thread(update_fundamental_batch_sync, list(batch)))
            batch = []
            
        if completed % 100 == 0 or completed == total:
            print(f"[{completed}/{total}] 펀더멘털 수집 중... (현재 속도: {completed/(time.time()-start_time):.2f} TPS)")

    await asyncio.sleep(2)
    print(f"\n✅ 펀더멘털 수집 완료. (소요시간: {time.time()-start_time:.1f}초)")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()