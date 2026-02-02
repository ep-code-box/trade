
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from src.auth import get_access_token
from src.kis_api import kis_get_async

async def get_dps_from_info(code):
    """방법 1: 주식 기본 정보 API에서 제공하는 DPS 필드 조회"""
    path = "/uapi/domestic-stock/v1/quotations/search-stock-info"
    params = {"PRDT_TYPE_CD": "300", "PDNO": code}
    # 실전(REAL) API가 데이터가 정확하므로 실전 사용
    res = await kis_get_async(path, params=params, tr_id="CTPF40020000", use_real=False)
    if res and "output" in res:
        return int(res["output"].get("per_stock_dvdn_amt", 0))
    return 0

async def get_dps_from_history(code):
    """방법 2: 배당 이력 API에서 최근 1년치 합산"""
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-dividend"
    # 시작일을 1년 전으로 설정
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    today = datetime.now().strftime("%Y%m%d")
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_STRT_ORG_DT": one_year_ago,
        "FID_END_ORG_DT": today
    }
    
    res = await kis_get_async(path, params=params, tr_id="HHKST01010100", use_real=False)
    
    if res and "output" in res:
        history = res["output"]
        total_dps = 0
        payouts = []
        for item in history:
            dps = int(item.get("per_stock_dvdn_amt", 0))
            record_date = item.get("stck_dvdn_base_dt", "Unknown")
            if dps > 0:
                total_dps += dps
                payouts.append(f"{record_date}:{dps}원")
        return total_dps, payouts
    return 0, []

async def get_dps_from_price(code):
    """방법 3: 주식 현재가 API (FHKST01010100) 조회"""
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = await kis_get_async(path, params=params, tr_id="FHKST01010100", use_real=False)
    if res and "output" in res:
        return int(res["output"].get("per_stock_dvdn_amt", 0))
    return 0

async def compare_stocks(stock_list):
    print(f"\n{'종목명':<10} | {'코드':<6} | {'기본정보(A)':>8} | {'현재가(B)':>8} | {'이력합산(C)':>8}")
    print("-" * 75)
    
    for code, name in stock_list:
        dps_info = await get_dps_from_info(code)
        dps_price = await get_dps_from_price(code)
        dps_calc, payouts = await get_dps_from_history(code)
        
        print(f"{name:<10} | {code:<6} | {dps_info:>8,}원 | {dps_price:>8,}원 | {dps_calc:>8,}원")
        if payouts:
            print(f"  └─ (C)이력: {', '.join(payouts)}")
        await asyncio.sleep(0.2)

async def main():
    if not get_access_token():
        print("토큰 발급 실패")
        return
        
    test_stocks = [
        ("005930", "삼성전자"),
        ("005380", "현대차"),
        ("088350", "한화생명"),
        ("000810", "삼성화재"),
        ("034730", "SK"),
        ("033780", "KT&G")
    ]
    
    print("=== 배당 데이터 추출 방식 비교 테스트 ===")
    await compare_stocks(test_stocks)

if __name__ == "__main__":
    asyncio.run(main())
