
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_price_fundamentals(code, name):
    print(f"\n🚀 [{name} ({code})] 주식현재가 재무지표(FHKST01010500) 스캔...")
    path = "/uapi/domestic-stock/v1/quotations/inquire-stability" # 이 경로가 재무지표를 포함하기도 함
    # 실제로는 이 경로가 아닐 수 있으므로 TR ID 중심으로 탐색
    path = "/uapi/domestic-stock/v1/quotations/inquire-stability" # 기존에 성공했던 경로
    
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010500", use_real=True)
    
    if res and "output" in res:
        output = res["output"]
        dps = output.get("per_stock_dvdn_amt")
        print(f"✅ 결과 포착: DPS = {dps}원")
        if dps: print("🎊 드디어 찾았습니다! 이 TR이 정답입니다.")
        else: print(f"전체 필드:\n{json.dumps(output, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 실패: {res}")

async def main():
    if not get_access_token(): return
    await test_price_fundamentals("005930", "삼성전자")

if __name__ == "__main__":
    asyncio.run(main())
