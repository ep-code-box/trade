
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def the_real_last_test(code, name):
    print(f"\n🚀 [{name} ({code})] 상품기본조회(CTPF1604R) 배당금 최종 확인...")
    # 경로와 TR_ID를 명세서 85번 항목과 100% 일치시킵니다.
    path = "/uapi/domestic-stock/v1/quotations/search-info"
    params = {"PRDT_TYPE_CD": "300", "PDNO": code}
    
    res = await kis_get_raw_async(path, params=params, tr_id="CTPF1604R", use_real=True)
    
    if res and "output" in res:
        output = res["output"]
        # 명세서에 있는 필드명들을 모두 시도합니다.
        dps = output.get("per_stock_dvdn_amt") or output.get("stck_dvdn_amt") or output.get("dvdn_amt")
        print(f"✅ 결과: DPS = {dps}원")
        if dps:
            print("🎉 드디어 찾았습니다! 이 로직이 정답입니다.")
        else:
            print("전체 응답 필드 확인 (상위 20개):")
            print(json.dumps(dict(list(output.items())[:20]), indent=2, ensure_ascii=False))
    else:
        print(f"❌ 실패: {res}")

async def main():
    if not get_access_token(): return
    await the_real_last_test("005930", "삼성전자")

if __name__ == "__main__":
    asyncio.run(main())
