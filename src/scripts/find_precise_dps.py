
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def find_precise_dps(code, name):
    print(f"\n🚀 [{name} ({code})] 재무비율(FHKST66430300) 내 'pft_dvdn_amt_val' 정밀 추적...")
    path = "/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430300", use_real=True)
    
    if res and "output" in res and res["output"]:
        item = res["output"][0]
        # 사용자님의 '재무 호출' 로직에서 사용했을 것으로 추정되는 필드들
        target_fields = ['pft_dvdn_amt_val', 'stck_dvdn_amt', 'dvdn_amt', 'dvdn_rate', 'payout_rate']
        
        found = {k: item[k] for k in target_fields if k in item}
        
        if found:
            print(f"✅ 결정적 필드 포착: {json.dumps(found, indent=2, ensure_ascii=False)}")
        else:
            print("⚠️ 타겟 필드가 없습니다. 전체 필드 중 'val'이 포함된 필드를 출력합니다.")
            val_fields = {k: v for k, v in item.items() if 'val' in k.lower()}
            print(json.dumps(val_fields, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await find_precise_dps("005930", "삼성전자")
    await find_precise_dps("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
