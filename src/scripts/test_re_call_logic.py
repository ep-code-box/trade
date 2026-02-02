
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_income_statement(code, name):
    print(f"\n🚀 [{name} ({code})] 기업 재무(손익계산서:FHKST66430200) 스캔 시작...")
    path = "/uapi/domestic-stock/v1/finance/income-statement"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0"
    }
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430200", use_real=True)
    
    if res and "output" in res and res["output"]:
        item = res["output"][0] # 최신 연도/분기
        print(f"✅ 기준일: {item.get('stac_yymm')} | 매출액: {item.get('sale_account')}억")
        
        # '배당'과 관련된 모든 필드 검색
        # 손익계산서 하단이나 재무비율에 배당금이 포함되는 경우가 많음
        dividend_fields = {k: v for k, v in item.items() if any(word in k.lower() for word in ['dvdn', 'div', 'pay'])}
        if dividend_fields:
            print(f"📍 발견된 배당 데이터: {json.dumps(dividend_fields, indent=2, ensure_ascii=False)}")
        else:
            print("⚠️ 이 TR의 직접 응답에는 배당 필드가 없습니다. 전체 필드 구조 상위 10개:")
            print(json.dumps(dict(list(item.items())[:10]), indent=2, ensure_ascii=False))
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await test_income_statement("005930", "삼성전자")
    await asyncio.sleep(0.5)
    await test_income_statement("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
