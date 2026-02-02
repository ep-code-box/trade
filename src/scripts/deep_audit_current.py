
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def deep_audit_current_price(code, name):
    print(f"\n🚀 [{name}] 주식현재가(FHKST01010100) 모든 응답 그룹 덤프...")
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010100", use_real=True)
    if res:
        # 모든 키(output, output1, ...)를 출력하여 어디에 배당이 있는지 확인
        for key in res.keys():
            if isinstance(res[key], dict):
                # 배당 관련 필드명 탐색
                found = {k: v for k, v in res[key].items() if any(x in k.lower() for x in ['dvdn', 'div', 'stcn'])}
                if found:
                    print(f"✅ [{key}] 에서 배당/주수 필드 발견:\n{json.dumps(found, indent=2, ensure_ascii=False)}")
            elif isinstance(res[key], list) and res[key]:
                print(f"✅ [{key}] 리스트 형태 데이터 존재 (항목수: {len(res[key])})")

async def main():
    if not get_access_token(): return
    await deep_audit_current_price("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
