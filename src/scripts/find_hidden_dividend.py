
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def find_hidden_dps(code, name):
    print(f"\n🚀 [{name} ({code})] 재무비율(FHKST66430300) 내 배당금 필드 정밀 추적...")
    path = "/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0"
    }
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430300", use_real=True)
    
    if res and "output" in res and res["output"]:
        # 모든 필드 중 '배당' 혹은 'amt'가 들어간 필드 전수 조사
        item = res["output"][0]
        # KIS의 재무비율 API는 필드명이 매우 많으므로, 배당금으로 의심되는 모든 필드 출력
        candidates = {k: v for k, v in item.items() if any(x in k.lower() for x in ['divi', 'dvdn', 'amt'])}
        
        if candidates:
            print(f"✅ 결정적 필드 포착:\n{json.dumps(candidates, indent=2, ensure_ascii=False)}")
        else:
            print("⚠️ 일반적인 필드명에는 배당금이 없습니다. 전체 필드명 100개를 분석합니다.")
            print(", ".join(list(item.keys())[:100]))
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await find_hidden_dps("005930", "삼성전자")
    await find_hidden_dps("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
