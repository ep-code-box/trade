
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_financial_ratios(code, name):
    print(f"\n🚀 [{name} ({code})] 재무비율(FHKST66430300) 데이터 정밀 스캔...")
    path = "/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0"
    }
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430300", use_real=True)
    
    if res and "output" in res and res["output"]:
        # 모든 필드를 출력하여 '배당' 관련 키워드가 있는지 확인
        item = res["output"][0] # 가장 최신 데이터
        print(f"✅ 최신 기준일: {item.get('stac_yymm')}")
        
        # 'dvdn', 'div', 'payout' 등 배당 관련 키워드가 포함된 필드 필터링
        dividend_related = {k: v for k, v in item.items() if any(word in k.lower() for word in ['dvdn', 'div', 'payout', 'rate'])}
        if dividend_related:
            print(f"📍 포착된 배당/비율 관련 필드:\n{json.dumps(dividend_related, indent=2, ensure_ascii=False)}")
        else:
            print("⚠️ 배당 관련 필드를 찾지 못했습니다. 전체 필드 상위 20개를 출력합니다.")
            print(json.dumps(dict(list(item.items())[:20]), indent=2, ensure_ascii=False))
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await test_financial_ratios("005930", "삼성전자")
    await asyncio.sleep(0.5)
    await test_financial_ratios("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
