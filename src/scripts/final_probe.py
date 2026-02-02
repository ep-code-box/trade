
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def final_probe_payout(code, name):
    print(f"\n🚀 [{name} ({code})] 배당성향(payout_rate) 연도별 데이터 추적...")
    # FID_DIV_CLS_CODE: 0 (연도별 데이터)
    path = "/uapi/domestic-stock/v1/finance/other-major-ratios"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430500", use_real=True)
    
    if res and "output" in res:
        for item in res["output"]:
            # payout_rate가 있는지, 그리고 0이 아닌 수치가 있는지 확인
            payout = item.get("payout_rate")
            date = item.get("stac_yymm")
            print(f"   📅 기준일: {date} | 배당성향: {payout}")
            if payout and float(payout) > 0:
                print(f"   🎉 드디어 찾았습니다! {date} 기준 배당성향 {payout}% 포착!")
                return True
    return False

async def main():
    if not get_access_token(): return
    # 현대차로 최종 확인
    await final_probe_payout("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())

