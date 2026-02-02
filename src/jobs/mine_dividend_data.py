"""전 종목 배당 마이닝 (Async 30 TPS 광속 버전)."""
import asyncio
import time
import pandas as pd
from datetime import datetime
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw_async

async def fetch_dividend_sector_async(market_gb, sector_code):
    """비동기 업종별 배당 데이터 수집 (최근 365일 Trailing Window)"""
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    
    from datetime import datetime, timedelta
    now = datetime.now()
    # [Trailing 12 Months] 오늘로부터 정확히 1년 전부터 조회
    f_dt = (now - timedelta(days=365)).strftime("%Y%m%d")
    t_dt = now.strftime("%Y%m%d")
    
    params = {
        "CTS_AREA": "", "GB1": market_gb, "UPJONG": sector_code,
        "GB2": "0", "GB3": "2", "F_DT": f_dt, "T_DT": t_dt, "GB4": "0",
    }
    # [v3.5] 실시간 배당 이력 수집
    data = await kis_get_raw_async(path, params=params, tr_id="HHKDB13470100", use_real=True)
    return (data.get("output") or []) if data else []

def save_mining_results(summary):
    """마이닝된 결과를 DB에 일괄 반영"""
    if not summary: return
    conn = get_connection()
    cur = conn.cursor()
    updated = 0
    for code, info in summary.items():
        total_dps = info["total_dps"]
        count = len(info["dps_list"])
        cycle = "분기/월" if count >= 4 else "반기배당" if count >= 2 else "연배당"
        
        # 1. master_info 업데이트 (DPS 원본 보존)
        cur.execute("UPDATE master_info SET per_stock_dvdn_amt = ?, dividend_cycle = ?, dividend_count = ? WHERE code = ?", (total_dps, cycle, count, code))
        
        # 2. daily_analysis 업데이트 (오늘 주가 기준 실시간 수익률 계산)
        cur.execute("""
            UPDATE daily_analysis 
            SET dividend_yield = (CAST(? AS REAL) / NULLIF(close, 0)) * 100 
            WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis)
        """, (total_dps, code))
        
        if cur.rowcount > 0: updated += 1
    conn.commit()
    conn.close()
    return updated

async def main_async():
    if not get_access_token(): return
    print("🚀 [v3.6] 전 시장(KOSPI/KOSDAQ) 배당 마이닝 대작전 개시 (Target: 30 TPS)")
    
    # 1. 전 시장 업종 목록 확보 (코스피: '1', 코스닥: '3')
    sectors = []
    # 코스피 전 업종 (0001 ~ 0999)
    for i in range(1, 1000): sectors.append(("1", f"{i:04d}"))
    # 코스닥 전 업종 (1001 ~ 1999)
    for i in range(1, 1000): sectors.append(("3", f"{1000+i:04d}"))
    
    start_time = time.time()
    all_raw_data = []
    completed = 0
    
    # 2. 비동기 업종 스캔 (병렬 수준 최적화)
    sem = asyncio.Semaphore(100)
    async def task(m, s):
        async with sem: return await fetch_dividend_sector_async(m, s)

    futures = [task(m, s) for m, s in sectors]
    for fut in asyncio.as_completed(futures):
        data = await fut
        if data: all_raw_data.extend(data)
        completed += 1
        if completed % 20 == 0:
            print(f"[{completed}/{len(sectors)}] 업종 스캔 중... (속도: {completed/(time.time()-start_time):.1f} TPS)")

    # 3. 데이터 정제 (실무형 중복 제거 및 연간 합산)
    print(f"\n📊 데이터 정제 중... (수집된 원시 행: {len(all_raw_data)})")
    summary = {}
    unique_events = set() # (종목코드, 기준일, 배당금, 배당률) 고유 이벤트 관리
    
    for item in all_raw_data:
        code = item.get("sht_cd", "").strip()
        dps = int(item.get("per_sto_divi_amt", 0))
        b_date = item.get("base_dt", "00000000")
        y_rate = item.get("divi_rate", "0") # 배당률
        
        if not code or dps <= 0: continue
        
        # [실무 규칙] (코드, 기준일, 금액, 배당률)이 모두 같아야만 동일한 배당 이벤트로 간주
        event_key = (code, b_date, dps, y_rate)
        if event_key in unique_events:
            continue
        unique_events.add(event_key)
        
        if code not in summary: 
            summary[code] = {"dps_list": [], "total_dps": 0}
        
        summary[code]["dps_list"].append(dps)
        summary[code]["total_dps"] += dps

    # 4. DB 저장
    updated_count = save_mining_results(summary)
    print(f"✅ 완료! {updated_count}개 종목의 배당 유전자를 해독했습니다. (소요시간: {time.time()-start_time:.1f}초)")

def main(): asyncio.run(main_async())
if __name__ == "__main__": main()