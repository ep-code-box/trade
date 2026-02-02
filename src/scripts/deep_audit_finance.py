
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def deep_audit_finance(code, name):
    print(f"\n🚀 [{name} ({code})] 기업 재무(기타주요비율:FHKST66430500) 전수 조사...")
    path = "/uapi/domestic-stock/v1/finance/other-major-ratios"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430500", use_real=True)
    
    if res and "output" in res and res["output"]:
        # 최신 결산 데이터(보통 202412)를 가져옵니다.
        # 장 종료 후에도 이 데이터는 나와야 합니다.
        item = res["output"][0]
        print(f"✅ 기준일: {item.get('stac_yymm')}")
        
        # 값이 0이 아닌 모든 필드를 출력합니다. (배당금은 0보다 클 것이므로)
        meaningful_data = {k: v for k, v in item.items() if v and float(v) != 0}
        print(f"📍 값이 있는 필드 목록:\n{json.dumps(meaningful_data, indent=2, ensure_ascii=False)}")
    else:
        print("❌ 데이터 없음")

async def main():
    if not get_access_token(): return
    # 배당을 많이 주는 '현대차'와 'KT&G'로 테스트 (데이터가 확실히 나오게)
    await deep_audit_finance("005380", "현대차")
    await deep_audit_finance("033780", "KT&G")

if __name__ == "__main__":
    asyncio.run(main())
