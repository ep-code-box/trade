import asyncio
import pandas as pd
from datetime import datetime, timedelta
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async, kis_get_async
from src.db import get_connection
import json

async def get_stock_info(code):
    """TR CTPF1604R: 상품기본조회 (상장주식수, 액면가 등)"""
    path = "/uapi/domestic-stock/v1/quotations/search-info"
    params = {"PRDT_TYPE_CD": "300", "PDNO": code}
    res = await kis_get_raw_async(path, params=params, tr_id="CTPF1604R", use_real=True)
    return res.get("output", {})

async def get_growth_rates(code):
    """TR FHKST66430800: 성장성비율 (EPS 증가율, 매출액 증가율)"""
    path = "/uapi/domestic-stock/v1/finance/growth-ratio"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430800", use_real=True)
    return res.get("output", {})

async def monitor_stock(code, name):
    print(f"\n🔍 [{name} ({code})] 데이터 감사 (Data Audit) 시작...")
    
    # 1. 수정주가 추세 확인 (리버모어의 관점)
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    today = datetime.now().strftime("%Y%m%d")
    prev = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
    
    params = {
        "FID_COND_SCR_DIV_CODE": "J", "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": prev, "FID_INPUT_DATE_2": today,
        "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0" # 수정주가 적용
    }
    
    price_res = await kis_get_raw_async(path, params=params, tr_id="FHKST03010100", use_real=True)
    if price_res and "output2" in price_res and price_res["output2"]:
        latest = price_res["output2"][0]
        curr_price = float(latest['stck_clpr'])
        prev_price = float(price_res["output2"][1]['stck_clpr'])
        change = ((curr_price - prev_price) / prev_price) * 100
        print(f"   📈 수정주가: {curr_price:,.0f}원 ({change:+.2f}%) | 거래량: {int(latest['acml_vol']):,}주")
    else:
        print("   ⚠️ 시세 데이터 수집 실패 (권한 또는 파라미터 확인 필요)")

    # 2. 펀더멘털 점검 (오닐의 관점: CAN SLIM의 'C'와 'A')
    info = await get_stock_info(code)
    growth = await get_growth_rates(code)
    
    if info or growth:
        eps_growth = growth.get('eps_grrt', 'N/A') # EPS 증가율
        sales_growth = growth.get('sale_grrt', 'N/A') # 매출액 증가율
        print(f"   🛡️ 기초체력: EPS성장 {eps_growth}% | 매출성장 {sales_growth}%")
    else:
        print("   ⚠️ 펀더멘털 데이터 수집 실패")

    # 3. 배당 및 현금 흐름 (미너비니의 관점)
    conn = get_connection()
    db_data = conn.execute("""
        SELECT per_stock_dvdn_amt, dividend_yield, roe 
        FROM master_info 
        JOIN daily_analysis USING(code) 
        WHERE code = ? ORDER BY date DESC LIMIT 1
    """, (code,)).fetchone()
    conn.close()
    
    if db_data:
        dps, yield_rate, roe = db_data
        print(f"   💰 배당체력: DPS {dps}원 | 수익률 {yield_rate:.2f}% | ROE {roe:.1f}%")

async def main():
    if not get_access_token():
        print("❌ 토큰 발급 실패")
        return
    
    # 스승님의 3대장
    targets = [("005930", "삼성전자"), ("005380", "현대차"), ("088350", "한화생명")]
    
    print(f"=== [TrendHunter] 데이터 감사 시스템 v4.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    for code, name in targets:
        await monitor_stock(code, name)
        await asyncio.sleep(0.5) # Rate Limit 준수

if __name__ == "__main__":
    asyncio.run(main())