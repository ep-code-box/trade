"""
[v11.0] 스승님의 지침 기반 '초광속' 무결점 엔진
기능: 비동기 Triple Chain (주수+이익+비율) 정밀 수집
속도: 30 TPS Target (전 종목 2분 내 주파)
"""
import asyncio
import time
import pandas as pd
from datetime import datetime
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw_async

async def fetch_precise_audit(code, sem):
    """4단계 정밀 감사 연쇄 호출 (비동기)"""
    async with sem:
        p_base = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        p_ratio = {**p_base, "FID_DIV_CLS_CODE": "0"}
        
        # 3개의 요청을 병렬로 던짐
        tasks = [
            kis_get_raw_async("/uapi/domestic-stock/v1/quotations/search-stock-info", params={"PRDT_TYPE_CD": "300", "PDNO": code}, tr_id="CTPF1002R", use_real=True),
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/income-statement", params=p_ratio, tr_id="FHKST66430200", use_real=True),
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/other-major-ratios", params=p_ratio, tr_id="FHKST66430500", use_real=True)
        ]
        res = await asyncio.gather(*tasks)
        
        return {
            "code": code,
            "shares": res[0].get("output", {}).get("lstg_stqt") if res[0] else None,
            "income_list": res[1].get("output") if res[1] else [],
            "ratio_list": res[2].get("output") if res[2] else []
        }

def get_dec_item(data_list):
    if not data_list: return None
    for item in data_list:
        if str(item.get("stac_yymm", "")).endswith("12"): return item
    return data_list[0] if data_list else None

def batch_update_db_final(conn, results):
    cur = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    
    for res in results:
        code = res["code"]
        shares = float(res["shares"] or 0)
        inc = get_dec_item(res["income_list"])
        rat = get_dec_item(res["ratio_list"])
        
        net_income = float(inc.get("thtr_ntin") or 0) if inc else 0
        payout = float(rat.get("payout_rate") or 0) if rat else 0
        
        calculated_dps = 0
        if shares > 0 and net_income > 0 and payout > 0:
            eps = (net_income * 100000000) / shares
            p_ratio = payout if payout < 1.0 else payout / 100.0
            calculated_dps = int(eps * p_ratio)
            
            # 15% 세이프티 캡
            try:
                # 최신 종가 조회 (메모리 성능 위해 최소화)
                p_row = conn.execute("SELECT close FROM daily_analysis WHERE code=? ORDER BY date DESC LIMIT 1", (code,)).fetchone()
                if p_row and p_row[0] > 0 and (calculated_dps / p_row[0]) > 0.15: calculated_dps = 0
            except: pass

        cur.execute("""
            UPDATE master_info 
            SET thtr_ntin = ?, lstn_stcn = ?, per_stock_dvdn_amt = CASE WHEN ? > 0 THEN ? ELSE per_stock_dvdn_amt END, updated_at = ?
            WHERE code = ?
        """, (net_income, shares, calculated_dps, calculated_dps, today, code))
        
        if calculated_dps > 0:
            cur.execute("UPDATE daily_analysis SET dividend_yield = (CAST(? AS REAL)/NULLIF(close,0))*100 WHERE code=? AND date=(SELECT MAX(date) FROM daily_analysis)", (calculated_dps, code))
    conn.commit()

async def main_async():
    if not get_access_token(): return
    conn = get_connection()
    stocks = pd.read_sql_query("SELECT code FROM master_info WHERE LENGTH(code) = 6", conn)["code"].tolist()
    conn.close()

    total = len(stocks)
    print(f"🚀 [v11.0] 초광속 펀더멘털 엔진 가동: {total}개 종목")
    start_time = time.time()
    
    # 루프 내부에서 세마포어 생성 (이벤트 루프 일치 보장)
    sem = asyncio.Semaphore(30)
    
    batch_size = 50
    for i in range(0, total, batch_size):
        chunk = stocks[i : i + batch_size]
        tasks = [fetch_precise_audit(c, sem) for c in chunk]
        results = await asyncio.gather(*tasks)
        
        conn = get_connection()
        batch_update_db_final(conn, results)
        conn.close()
        
        elapsed = time.time() - start_time
        print(f"[{min(i+batch_size, total)}/{total}] 광속 정화 중... (속도: {(i+len(chunk))/elapsed:.1f} 종목/초)", end="\r")

    print(f"\n\n✅ 모든 작전이 광속으로 종료되었습니다. (소요시간: {time.time()-start_time:.1f}초)")

def main(): asyncio.run(main_async())
if __name__ == "__main__": main()
