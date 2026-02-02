
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def dump_all_financial_fields(code, name):
    print(f"\n🔍 [{name} ({code})] 재무비율(FHKST66430300) 전 필드 덤프...")
    path = "/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430300", use_real=True)
    
    if res and "output" in res:
        # 최신 결산 데이터 1건의 모든 필드를 알파벳 순으로 출력
        item = res["output"][0]
        sorted_item = dict(sorted(item.items()))
        print(json.dumps(sorted_item, indent=2, ensure_ascii=False))
    else:
        print("실패")

async def main():
    if not get_access_token(): return
    await dump_all_financial_fields("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())

