
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def proof_of_data():
    code = "033780" # KT&G (확실한 배당주)
    print(f"--- [{code}] KT&G 데이터 실전 검증 ---")
    
    # 1. 실제 주식수 확인 (기본정보)
    res_b = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/search-stock-info", 
                                   params={"PRDT_TYPE_CD": "300", "PDNO": code}, 
                                   tr_id="CTPF1002R", use_real=True)
    
    # 2. 배당 비율 확인 (기업 재무)
    res_r = await kis_get_raw_async("/uapi/domestic-stock/v1/finance/other-major-ratios", 
                                   params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}, 
                                   tr_id="FHKST66430500", use_real=True)

    if res_b and "output" in res_b:
        print(f"\n[1. 기본정보 응답]")
        print(f" > 실제 주식수(lstg_stqt): {res_b['output'].get('lstg_stqt')}")
    
    if res_r and "output" in res_r:
        print(f"\n[2. 기업 재무 응답 (최근 3개 항목)]")
        for item in res_r["output"][:3]:
            print(f" > 기준일: {item.get('stac_yymm')} | 배당비율(payout_rate): {item.get('payout_rate')}")

async def main():
    if not get_access_token(): return
    await proof_of_data()

if __name__ == "__main__":
    asyncio.run(main())
