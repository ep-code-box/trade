
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def final_check_profitability(code, name):
    print(f"\n🔍 [{name}] 수익성비율 리스트 전수 조사...")
    path = "/uapi/domestic-stock/v1/finance/profit-ratio"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430400", use_real=True)
    if res and "output" in res:
        for item in res["output"]:
            date = item.get("stac_yymm")
            # 주당배당금(stck_dvdn_amt) 필드 확인
            dps = item.get("stck_dvdn_amt") or item.get("dvdn_amt")
            print(f"📅 {date}: {item}")
            if dps and float(dps) > 0:
                print(f"   🎉 드디어 찾았습니다! {date} 기준 주당배당금 {dps}원 포착!")

async def main():
    if not get_access_token(): return
    await final_check_profitability("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())

