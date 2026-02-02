
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_stability_dividend(code, name):
    print(f"\n🚀 [{name} ({code})] 안정성비율(FHKST0101010600) 배당 필드 추적...")
    path = "/uapi/domestic-stock/v1/quotations/inquire-stability"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010600", use_real=True)
    
    if res and "output" in res:
        o = res["output"]
        print(f"ROE: {o.get('roe_val')}")
        print(f"배당수익률(dvdn_rate): {o.get('dvdn_rate')}")
        # 배당과 관련된 다른 필드가 있는지 전체 탐색
        found = {k: v for k, v in o.items() if any(x in k.lower() for x in ['dvdn', 'rate'])}
        print(f"관련 필드:\n{json.dumps(found, indent=2, ensure_ascii=False)}")
    else:
        print("실패")

async def main():
    if not get_access_token(): return
    await test_stability_dividend("005930", "삼성전자")
    await test_stability_dividend("033780", "KT&G")

if __name__ == "__main__":
    asyncio.run(main())
