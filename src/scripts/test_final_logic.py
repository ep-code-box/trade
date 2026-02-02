
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_stock_basic_info(code, name):
    print(f"\n🚀 [{name} ({code})] 상품기본정보(CTPF1604R) 배당 추출 테스트...")
    path = "/uapi/domestic-stock/v1/quotations/search-info"
    params = {
        "PRDT_TYPE_CD": "300",
        "PDNO": code
    }
    
    # TR ID: CTPF1604R (명세서 85번 항목)
    res = await kis_get_raw_async(path, params=params, tr_id="CTPF1604R", use_real=True)
    
    if res and "output" in res:
        output = res["output"]
        dps = output.get("per_stock_dvdn_amt")
        yield_rate = output.get("dvdn_rate")
        print(f"✅ 포착된 데이터: 주당배당금(DPS) = {dps}원 | 배당수익률 = {yield_rate}%")
        
        if not dps or int(float(dps)) == 0:
            print("   ⚠️ DPS가 0입니다. 전체 응답 구조에서 배당 관련 필드를 재탐색합니다.")
            related = {k: v for k, v in output.items() if 'dvdn' in k.lower() or 'amt' in k.lower()}
            print(json.dumps(related, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await test_stock_basic_info("005930", "삼성전자")
    await asyncio.sleep(0.5)
    await test_stock_basic_info("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
