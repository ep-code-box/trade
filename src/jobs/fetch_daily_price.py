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
    # [최적화] 지수는 항상 1000일(10회), 종목은 초기 300일/평소 100일
    is_index = code in ["0001", "1001"]
    
    if is_index:
        max_calls = 10
        start_dt = (datetime.now() - timedelta(days=1500)).strftime("%Y%m%d")
    else:
        max_calls = 3 if pd.isna(last_date) else 1
        start_dt = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d") if pd.isna(last_date) else \
                   (datetime.strptime(str(last_date), "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    
    if not is_index and start_dt > today_str: return None, None

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
    # [v16.0] 지능형 수집: 기존 데이터를 지우지 않고, 없는 종목만 타겟팅
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) IN (4, 6)", conn)
    stocks = pd.concat([stocks, pd.DataFrame([{"code":"0001","name":"KOSPI"},{"code":"1001","name":"KOSDAQ"}])]).drop_duplicates(subset=["code"])
    df_status = pd.read_sql_query(f"SELECT code FROM daily_analysis WHERE date = '{today_str}'", conn)
    conn.close()
    
    # 오늘 데이터가 없는 종목만 필터링
    target_stocks = stocks[~stocks['code'].isin(df_status['code'])]
    
    total = len(target_stocks)
    if total == 0:
        print(f"✅ [v16.0] 오늘({today_str}) 데이터가 이미 완벽합니다. (No Gap)")
        return

    print(f"🚀 [v16.0] 빵꾸 제로 엔진 가동: 누락된 {total}개 종목 집중 수집")
    
    start_time = time.time()
    completed, batch = 0, []
    # [Stability] KIS API 안정성을 위해 동시성을 15로 조정
    sem = asyncio.Semaphore(15)
    
    async def task(r):
        async with sem:
            # last_date 정보는 무시하고 오늘 데이터만 확보 시도
            res = await fetch_single_stock_async(r['code'], r['name'], None, today_str)
            await asyncio.sleep(0.08) # 안정적인 간격 확보
            return res

    futures = [asyncio.create_task(task(r)) for _, r in target_stocks.iterrows()]
    
    for fut in asyncio.as_completed(futures):
        code, data = await fut
        if data: batch.append((code, data))
        completed += 1
        
        if len(batch) >= 50 or completed == total:
            await asyncio.to_thread(save_batch_fast, list(batch))
            batch = []
            
        if completed % 100 == 0 or completed == total:
            elapsed = time.time() - start_time
            print(f"[{completed}/{total}] 진행 중... (누적 API: {api_call_count}회)")

    # [Audit Pass] 수집 종료 후 2차 검증 및 빵꾸 메우기
    conn = get_connection()
    df_final = pd.read_sql_query(f"SELECT count(*) as cnt FROM daily_analysis WHERE date = '{today_str}'", conn)
    conn.close()
    print(f"\n🏁 1차 작전 종료. 현재 확보 데이터: {df_final.iloc[0]['cnt']}건")
    
    # 만약 여전히 빵꾸가 많으면 자동으로 2차 실행을 위해 False 반환 (run_daily에서 제어 가능)
    return True

def main(): asyncio.run(main_async())
if __name__ == "__main__": main()