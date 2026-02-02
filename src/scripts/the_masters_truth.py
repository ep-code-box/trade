
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def the_masters_truth(code, name):
    print(f"\n🚀 [{name} ({code})] 스승님의 정석 로직 검증...")
    
    # 1. 기본정보(현재가) 호출 -> 실제 주식 갯수 확인
    res_p = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", 
                                   params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}, 
                                   tr_id="FHKST01010100", use_real=True)
    
    shares = res_p.get("output", {}).get("lstn_stcn")
    print(f"✅ 1단계 성공: 실제 주식 갯수(lstn_stcn) = {shares}")

    # 2. 기업 재무(재무비율) 호출 -> 주당현금배당금(per_sto_divi_amt) 확인
    # FID_DIV_CLS_CODE: 0 (연도별 결산 데이터)
    res_f = await kis_get_raw_async("/uapi/domestic-stock/v1/finance/financial-ratio", 
                                   params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}, 
                                   tr_id="FHKST66430300", use_real=True)
    
    if res_f and "output" in res_f:
        # 최신 결산 데이터(202412 등)를 찾습니다.
        for item in res_f["output"]:
            dps = item.get("per_sto_divi_amt") # 'sto' 임에 주의!
            date = item.get("stac_yymm")
            if dps and float(dps) > 0:
                print(f"✅ 2단계 성공: {date} 기준 주당현금배당금(per_sto_divi_amt) = {dps}원")
                print(f"🎉 스승님의 말씀이 맞았습니다. 역산할 필요 없이 재무 API에 '진짜 배당금'이 있었습니다.")
                return
    print("❌ 실패: 배당금 필드를 찾지 못했습니다.")

async def main():
    if not get_access_token(): return
    await the_masters_truth("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
