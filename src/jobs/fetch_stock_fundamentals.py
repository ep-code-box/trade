"""
[v14.0] 거장의 회귀: 정석 필드 매핑 엔진
기능: 비동기 Triple Chain (재무비율 + 주요비율 + 손익계산서)
특징: API 정석 필드(roe_val, eps) 매핑으로 ROE 0.0 이슈 완전 해결
"""
import asyncio
import time
import pandas as pd
from datetime import datetime
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw_async

async def fetch_precise_audit(code, sem):
    """3단계 정밀 재무 감사 (비동기 병렬 호출)"""
    async with sem:
        p_ratio = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
        
        tasks = [
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/financial-ratio", params=p_ratio, tr_id="FHKST66430300", use_real=True),
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/other-major-ratios", params=p_ratio, tr_id="FHKST66430500", use_real=True),
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/income-statement", params=p_ratio, tr_id="FHKST66430200", use_real=True)
        ]
        res = await asyncio.gather(*tasks)
        
        return {
            "code": code,
            "financial_list": res[0].get("output") if res[0] else [],
            "ratio_list": res[1].get("output") if res[1] else [],
            "income_list": res[2].get("output") if res[2] else []
        }

def get_best_stat(data_list):
    if not data_list: return None
    # 12월 결산(연간) 데이터 우선
    for item in data_list:
        if str(item.get("stac_yymm", "")).endswith("12"): return item
    return data_list[0]

def batch_update_db_final(conn, results):
    cur = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    
    for res in results:
        code = res["code"]
        f_inc = get_best_stat(res["financial_list"])
        r_rat = get_best_stat(res["ratio_list"])
        i_inc = get_best_stat(res["income_list"])
        
        # [v14.0] 명세서 정석 필드 매핑: roe_val, eps
        eps = float(f_inc.get("eps") or 0) if f_inc else 0
        roe = float(f_inc.get("roe_val") or 0) if f_inc else 0 # roe -> roe_val로 수정
        payout = float(r_rat.get("payout_rate") or 0) if r_rat else 0
        net_income = float(i_inc.get("thtr_ntin") or 0) if i_inc else 0
        
        calculated_dps = 0
        if eps > 0 and payout > 0:
            p_ratio = payout if payout < 1.0 else payout / 100.0
            calculated_dps = int(eps * p_ratio)
            
            # 15% 세이프티 캡
            try:
                p_row = conn.execute("SELECT close FROM daily_analysis WHERE code=? ORDER BY date DESC LIMIT 1", (code,)).fetchone()
                if p_row and p_row[0] > 0 and (calculated_dps / p_row[0]) > 0.15: 
                    calculated_dps = 0
            except: pass

        # master_info 업데이트
        cur.execute("""
            UPDATE master_info 
            SET roe = ?, 
                eps = ?,
                thtr_ntin = ?,
                per_stock_dvdn_amt = CASE WHEN ? > 0 THEN ? ELSE per_stock_dvdn_amt END, 
                updated_at = ?
            WHERE code = ?
        """, (roe, eps, net_income, calculated_dps, calculated_dps, today, code))
        
        if calculated_dps > 0:
            cur.execute("""
                UPDATE daily_analysis 
                SET dividend_yield = (CAST(? AS REAL) / NULLIF(close, 0)) * 100 
                WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis)
            """, (calculated_dps, code))
            
    conn.commit()

async def main_async():
    if not get_access_token(): return
    conn = get_connection()
    # [v14.1] 증분 업데이트 전략: 최근 7일 이내 업데이트된 종목은 Skip
    query = """
        SELECT code FROM master_info 
        WHERE LENGTH(code) = 6 
          AND (updated_at IS NULL OR updated_at < date('now', '-7 days'))
    """
    stocks = pd.read_sql_query(query, conn)["code"].tolist()
    conn.close()

    total = len(stocks)
    if total == 0:
        print("✅ 모든 종목의 재무 데이터가 최신 상태입니다. (최근 7일 이내)")
        return

    print(f"🚀 [v14.1] 증분 수집 가동: {total}개 종목 (Skip 최근 7일)")
    start_time = time.time()
    
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
        print(f"[{min(i+batch_size, total)}/{total}] 정석 데이터 정화 중... (속도: {(i+len(chunk))/elapsed:.1f} 종목/초)", end="\r")

    print(f"\n\n✅ 모든 펀더멘털 작전이 종료되었습니다. (소요시간: {time.time()-start_time:.1f}초)")

def main(): asyncio.run(main_async())
if __name__ == "__main__": main()