
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def exhaustive_search(code, name):
    print(f"\n🔍 [{name}] 재무비율 리스트 전수 조사...")
    path = "/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430300", use_real=True)
    if res and "output" in res:
        for item in res["output"]:
            date = item.get("stac_yymm")
            # 모든 필드명과 값을 한 줄로 출력
            print(f"📅 {date}: {item}")

async def main():
    if not get_access_token(): return
    await exhaustive_search("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
