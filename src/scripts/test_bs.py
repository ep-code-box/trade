
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_balance_sheet(code, name):
    print(f"\n🚀 [{name} ({code})] 기업 재무(대차대조표:FHKST66430100) 스캔...")
    path = "/uapi/domestic-stock/v1/finance/balance-sheet"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430100", use_real=True)
    if res and "output" in res:
        item = res["output"][0]
        # 현금흐름이나 이익잉여금 처분 관련 배당 필드 탐색
        found = {k: v for k, v in item.items() if any(x in k.lower() for x in ['div', 'dvdn', 'pay'])}
        if found: print(json.dumps(found, indent=2, ensure_ascii=False))
        else: print("배당 필드 없음")

async def main():
    if not get_access_token(): return
    await test_balance_sheet("005930", "삼성전자")

if __name__ == "__main__":
    asyncio.run(main())
