
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_other_ratios(code, name):
    print(f"\n🚀 [{name} ({code})] 기업 재무(기타주요비율:FHKST66430500) 정밀 스캔...")
    path = "/uapi/domestic-stock/v1/finance/other-major-ratios"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0"
    }
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430500", use_real=True)
    
    if res and "output" in res and res["output"]:
        item = res["output"][0]
        print(f"✅ 기준일: {item.get('stac_yymm')}")
        
        # 모든 필드를 샅샅이 뒤집니다.
        # dvdn_payout_ratio (배당성향), dvdn_yield_rate (배당수익률) 등 탐색
        found = {k: v for k, v in item.items() if any(x in k.lower() for x in ['dvdn', 'div', 'payout'])}
        if found:
            print(f"📍 빙고! 배당 관련 필드 발견:\n{json.dumps(found, indent=2, ensure_ascii=False)}")
        else:
            print("⚠️ 이 TR에도 배당 필드가 없습니다. 전체 필드 목록:")
            print(json.dumps(item, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await test_other_ratios("005930", "삼성전자")
    await test_other_ratios("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
