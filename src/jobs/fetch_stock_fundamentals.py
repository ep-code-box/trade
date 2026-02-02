"""
[v6.5] 스승님의 지침 기반 '실제 주수' 펀더멘털 엔진
기능: 주식현재가(실제 주수) + 손익계산서(백만 원) + 배당성향을 결합한 정밀 역산
실행: python -m src.jobs.fetch_stock_fundamentals
"""
import asyncio
import time
import pandas as pd
from datetime import datetime
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw_async

async def fetch_precise_financial_chain(code, sem):
    """4단계 연쇄 호출: 현재가(주수) -> 손익 -> 수익성 -> 기타비율"""
    async with sem:
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        params_ratio = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
        
        tasks = [
            kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", params=params, tr_id="FHKST01010100", use_real=True), # 실제주수(lstn_stcn)
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/income-statement", params=params_ratio, tr_id="FHKST66430200", use_real=True), # 당기순익(백만원)
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/profit-ratio", params=params_ratio, tr_id="FHKST66430400", use_real=True),    # ROE
            kis_get_raw_async("/uapi/domestic-stock/v1/finance/other-major-ratios", params=params_ratio, tr_id="FHKST66430500", use_real=True) # 배당성향
        ]
        res = await asyncio.gather(*tasks)
        
        return {
            "code": code,
            "price_data": res[0].get("output") if res[0] else None,
            "income_list": res[1].get("output") if res[1] else [],
            "profit_list": res[2].get("output") if res[2] else [],
            "ratio_list": res[3].get("output") if res[3] else []
        }

def find_best_record(data_list, target_suffix="12"):
    if not data_list: return None
    for item in data_list:
        if str(item.get("stac_yymm", "")).endswith(target_suffix): return item
    return data_list[0] if data_list else None

def batch_update_db(conn, batch_results):
    cur = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    
    for res in batch_results:
        code = res["code"]
        price = res["price_data"]
        inc = find_best_record(res["income_list"])
        prof = find_best_record(res["profit_list"])
        ratio = find_best_record(res["ratio_list"])
        
        # 1. 실제 상장주수 확보 (단위: 주)
        actual_shares = float(price.get("lstn_stcn", 0)) if price else 0
        
        # 2. 재무 데이터 확보 (단위: 백만 원 / %)
        sales = float(inc.get("sale_account") or 0) if inc else 0
        op_profit = float(inc.get("bsop_prti") or 0) if inc else 0
        net_income = float(inc.get("thtr_ntin") or 0) if inc else 0
        roe = float(prof.get("self_cptl_ntin_inrt") or 0) if prof else 0.0
        payout = float(ratio.get("payout_rate") or 0) if ratio else 0.0

        # 3. 정밀 배당 역산 (백만 원 / 실제 주수)
        calculated_dps = 0
        if actual_shares > 0 and net_income > 0 and payout > 0:
            # EPS = (당기순이익_백만 * 1,000,000) / 실제상장주수
            eps = (net_income * 1000000) / actual_shares
            # payout_rate 지능형 판단 (0.3 -> 30%, 30.0 -> 30%)
            p_ratio = payout if payout < 1.0 else payout / 100.0
            calculated_dps = int(eps * p_ratio)
            
            # 안전장치: 시가 대비 15% 초과 배당은 노이즈로 간주
            curr_price = float(price.get("stck_prpr", 0)) if price else 0
            if curr_price > 0 and (calculated_dps / curr_price) > 0.15:
                calculated_dps = 0

        # DB 업데이트 (상장주수도 실제 주수로 갱신)
        cur.execute("""
            UPDATE master_info 
            SET sale_account = ?, bsop_prfi = ?, thtr_ntin = ?, roe = ?, 
                lstn_stcn = ?, per_stock_dvdn_amt = CASE WHEN ? > 0 THEN ? ELSE per_stock_dvdn_amt END,
                updated_at = ?
            WHERE code = ?
        """, (sales, op_profit, net_income, roe, actual_shares, calculated_dps, calculated_dps, today, code))
        
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
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) = 6", conn).values.tolist()
    conn.close()

    total = len(stocks)
    print(f"🚀 [v6.5] 정밀 주수 기반 펀더멘털 엔진 가동: {total}개 종목")
    start_time = time.time()
    sem = asyncio.Semaphore(20) # 안정적인 20 TPS
    
    batch_size = 40
    for i in range(0, total, batch_size):
        chunk = stocks[i : i + batch_size]
        tasks = [fetch_precise_financial_chain(c[0], sem) for c in chunk]
        results = await asyncio.gather(*tasks)
        
        conn = get_connection() # 배치마다 커넥션
        batch_update_db(conn, results)
        conn.close()
        
        elapsed = time.time() - start_time
        print(f"[{min(i+batch_size, total)}/{total}] 정밀 분석 완료 | 속도: {(i+len(chunk))/elapsed:.1f} 종목/초", end="\r")
        await asyncio.sleep(0.5)
        
    print(f"\n\n✅ 모든 종목의 실제 주수 및 재무 데이터 정화 완료.")

if __name__ == "__main__":
    asyncio.run(main_async())