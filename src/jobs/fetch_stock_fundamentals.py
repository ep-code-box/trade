"""
[v8.0] 스승님의 지침 기반 '초광속 컬럼 직결' 엔진
기능: 단일 API 호출(FHKST01010600)로 ROE 및 배당율 직접 수집
특징: 역산 없음, 지연 없음, 공식 컬럼값 그대로 매핑
"""
import asyncio
import time
import pandas as pd
from datetime import datetime
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw_async

async def fetch_simple_fundamental(code, sem):
    """안정성 API(FHKST01010600) 단일 호출로 핵심 지표 직접 수집"""
    async with sem:
        path = "/uapi/domestic-stock/v1/quotations/inquire-stability"
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010600", use_real=True)
        
        if res and "output" in res:
            o = res["output"]
            return {
                "code": code,
                "roe": float(o.get("roe_val") or 0),
                "yield": float(o.get("dvdn_rate") or 0)
            }
        return None

def batch_update_db_fast(conn, results):
    """컬럼값 그대로 DB에 고속 주입"""
    if not results: return
    cur = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    
    for r in results:
        if not r: continue
        # 1. master_info에 ROE 직접 저장
        cur.execute("UPDATE master_info SET roe = ?, updated_at = ? WHERE code = ?", (r["roe"], today, r["code"]))
        
        # 2. daily_analysis에 배당수익률 직접 저장
        if r["yield"] > 0:
            cur.execute("""
                UPDATE daily_analysis 
                SET dividend_yield = ? 
                WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis)
            """, (r["yield"], r["code"]))
    conn.commit()

async def main_async():
    if not get_access_token(): return
    conn = get_connection()
    stocks = pd.read_sql_query("SELECT code FROM master_info WHERE LENGTH(code) = 6", conn)["code"].tolist()
    conn.close()

    total = len(stocks)
    print(f"🚀 [v8.0] 초광속 컬럼 직결 엔진 가동: {total}개 종목")
    start_time = time.time()
    
    # KIS 실전 API 한계치(30 TPS)에 근접하게 세팅
    sem = asyncio.Semaphore(30)
    batch_size = 100
    
    for i in range(0, total, batch_size):
        chunk = stocks[i : i + batch_size]
        tasks = [fetch_simple_fundamental(c, sem) for c in chunk]
        results = await asyncio.gather(*tasks)
        
        conn = get_connection()
        batch_update_db_fast(conn, results)
        conn.close()
        
        elapsed = time.time() - start_time
        print(f"[{min(i+batch_size, total)}/{total}] 동기화 완료 | 속도: {(i+len(chunk))/elapsed:.1f} 종목/초", end="\r")

    print(f"\n\n✅ 전 종목 ROE 및 배당율 컬럼 직결 완료. (소요시간: {time.time()-start_time:.1f}초)")

if __name__ == "__main__":
    asyncio.run(main_async())