
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_profitability_ratios(code, name):
    print(f"\n🚀 [{name} ({code})] 수익성비율(FHKST66430400) 데이터 감사 시작...")
    path = "/uapi/domestic-stock/v1/finance/profit-ratio"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0" # 전체 구분
    }
    
    # 실전(REAL) 도메인 호출 (데이터 정확도 확보)
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430400", use_real=True)
    
    if res and "output" in res:
        print(f"✅ 데이터 수신 성공 (항목 수: {len(res['output'])})")
        # 모든 필드를 출력하여 배당 관련 필드 포착
        # 보통 리스트 형태로 연도별 데이터가 옵니다.
        for i, item in enumerate(res["output"][:2]): # 최신 2개년치만
            print(f"\n[기록 {i+1} - 기준일: {item.get('stac_yymm', 'Unknown')}]")
            # 배당 관련 유력 필드 추출 시도
            dps_fields = ["stck_dvdn_amt", "pft_dvdn_amt_val", "dvdn_payout_ratio", "per_stock_dvdn_amt"]
            found_any = False
            for field in dps_fields:
                if field in item:
                    print(f"   📍 포착된 배당 필드: {field} = {item[field]}")
                    found_any = True
            
            if not found_any:
                print("   ⚠️ 알려진 배당 필드가 없습니다. 전체 필드 구조를 확인합니다.")
                print(json.dumps(item, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    
    await test_profitability_ratios("005930", "삼성전자")
    await asyncio.sleep(0.5)
    await test_profitability_ratios("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
