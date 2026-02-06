"일봉 수집 비동기 + 초정밀 로깅 (Target 30 TPS)."
import asyncio
import time
import pandas as pd
from datetime import datetime, timedelta
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_async

# 글로벌 카운터
api_call_count = 0

async def fetch_single_stock_async(code, name, last_date, today_str):
    global api_call_count
    # [최적화] 초기 적재 시 300일(3회), 평소 100일(1회)
    max_calls = 3 if pd.isna(last_date) else 1
    
    start_dt = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d") if pd.isna(last_date) else \
               (datetime.strptime(str(last_date), "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    
    if start_dt > today_str: return None, None

    path, mrkt_div, tr_id = ("/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice", "U", "FHKUP03500100") if len(code) == 4 else ("/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", "J", "FHKST03010100")

    all_data = []
    current_end = today_str
    
    for _ in range(max_calls):
        # [스승님의 지침] FID_ORG_ADJ_PRC: "0" (수정주가 적용) - 배당락 착시 방지
        params = {
            "FID_COND_MRKT_DIV_CODE": mrkt_div, 
            "FID_INPUT_ISCD": code, 
            "FID_INPUT_DATE_1": start_dt, 
            "FID_INPUT_DATE_2": current_end, 
            "FID_PERIOD_DIV_CODE": "D", 
            "FID_ORG_ADJ_PRC": "0"
        }
        data = await kis_get_async(path, params=params, tr_id=tr_id)
        api_call_count += 1 # 실제 API 쏜 횟수
        
        if not data or not data.get("output2"): break
        chunk = data.get("output2")
        if mrkt_div == "U":
            for d in chunk:
                d["stck_clpr"] = d.get("bstp_nmix_prpr"); d["stck_oprc"] = d.get("bstp_nmix_oprc")
                d["stck_hgpr"] = d.get("bstp_nmix_hgpr"); d["stck_lwpr"] = d.get("bstp_nmix_lwpr")
        all_data.extend(chunk)
        if len(chunk) < 100: break
        current_end = (datetime.strptime(chunk[-1]["stck_bsop_date"], "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        if current_end < start_dt: break
            
    return code, all_data

def save_batch_fast(results):
    if not results: return
    data = []
    for code, data_list in results:
        for d in data_list:
            data.append((d["stck_bsop_date"], code, float(d.get("stck_oprc") or 0), float(d.get("stck_hgpr") or 0), float(d.get("stck_lwpr") or 0), float(d.get("stck_clpr") or 0), int(float(d.get("acml_vol") or 0)), int(float(d.get("acml_tr_pbmn") or 0)), 0.0))
    if not data: return
    conn = get_connection()
    try:
        conn.executemany("INSERT OR IGNORE INTO daily_analysis (date, code, open, high, low, close, volume, amount, rs_score) VALUES (?,?,?,?,?,?,?,?,?)", data)
        conn.commit()
    except Exception as e:
        print(f"DB 저장 중 오류 발생: {e}")
    conn.close()

async def main_async():
    global api_call_count
    if not get_access_token(): return
    
    # [TrendHunter Policy] 18:00 이전에는 데이터 완결성을 위해 어제를 타겟으로 함
    now = datetime.now()
    if now.hour < 18:
        today_str = (now - timedelta(days=1)).strftime("%Y%m%d")
    else:
        today_str = now.strftime("%Y%m%d")
        
    conn = get_connection()
    # [Clean Start] 오늘자 불완전 데이터 강제 삭제 (무결성 보장)
    conn.execute("DELETE FROM daily_analysis WHERE date = ?", (today_str,))
    conn.commit()
    
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) IN (4, 6)", conn)
    stocks = pd.concat([stocks, pd.DataFrame([{"code":"0001","name":"KOSPI"},{"code":"1001","name":"KOSDAQ"}])]).drop_duplicates(subset=["code"])
    df_status = pd.read_sql_query("SELECT code, MAX(date) as last_date FROM daily_analysis GROUP BY code", conn)
    conn.close()
    stocks = pd.merge(stocks, df_status, on="code", how="left")
    target_stocks = stocks[stocks['last_date'] != today_str]
    
    total = len(target_stocks)
    print(f"🚀 [v3.2] 광속 엔진 가동: {total}개 종목 (Target: 30 TPS API)")
    
    start_time = time.time()
    completed, batch = 0, []
    # 150개를 동시에 네트워크에 태움
    sem = asyncio.Semaphore(150)
    
    async def task(r):
        async with sem: return await fetch_single_stock_async(r['code'], r['name'], r['last_date'], today_str)

    futures = [asyncio.create_task(task(r)) for _, r in target_stocks.iterrows()]
    
    for fut in asyncio.as_completed(futures):
        code, data = await fut
        if data: batch.append((code, data))
        completed += 1
        
        if len(batch) >= 100 or completed == total:
            await asyncio.to_thread(save_batch_fast, list(batch))
            batch = []
            
        if completed % 100 == 0 or completed == total:
            elapsed = time.time() - start_time
            # 실시간 TPS 계산 (종목 기준 vs API 호출 기준)
            stock_tps = completed / elapsed
            api_tps = api_call_count / elapsed
            print(f"[{completed}/{total}] 종목속도: {stock_tps:.1f} STPS | 실전 API 속도: {api_tps:.1f} TPS")

    await asyncio.sleep(2)
    print(f"\n✅ 작전 종료. 총 호출 {api_call_count}건, 평균 {api_call_count/(time.time()-start_time):.1f} TPS")

def main(): asyncio.run(main_async())
if __name__ == "__main__": main()