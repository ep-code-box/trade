
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def check_last_year_dividend(code, name):
    print(f"\n🚀 [{name} ({code})] 2024년 12월 결산 재무 데이터 정밀 진단...")
    path = "/uapi/domestic-stock/v1/finance/other-major-ratios"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430500", use_real=True)
    
    if res and "output" in res:
        # 리스트를 돌며 202412 데이터를 찾습니다.
        for item in res["output"]:
            if item.get("stac_yymm") == "202412":
                print(f"✅ 2024년 결산 데이터 포착!")
                # 배당성향(payout_rate)이나 기타 배당 관련 수치가 있는지 확인
                meaningful = {k: v for k, v in item.items() if v and float(v) != 0}
                print(json.dumps(meaningful, indent=2, ensure_ascii=False))
                return
        print("⚠️ 202412 결산 데이터를 찾지 못했습니다.")

async def main():
    if not get_access_token(): return
    await check_last_year_dividend("005380", "현대차") # 배당 대장 현대차

if __name__ == "__main__":
    asyncio.run(main())

