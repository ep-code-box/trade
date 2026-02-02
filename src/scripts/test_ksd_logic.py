
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_ksd_dividend(code, name):
    print(f"\n🚀 [{name} ({code})] 예탁원 배당 정보(ksdinfo/dividend) 스캔...")
    path = "/uapi/domestic-stock/v1/ksdinfo/dividend"
    # 공식 예제 파라미터 규격 적용
    params = {
        "SHTN_PDNO": code,
        "INQR_STRT_DT": "20240101",
        "INQR_END_DT": "20241231",
        "GB1": "0", # 0:전체
        "HIGH_GB": ""
    }
    
    res = await kis_get_raw_async(path, params=params, tr_id="HHKDB669102C0", use_real=True)
    
    if res and "output" in res and res["output"]:
        print(f"✅ 데이터 수신 성공 (항목 수: {len(res['output'])})")
        for item in res["output"]:
            dps = item.get("per_sto_divi_amt")
            base_dt = item.get("stck_dvdn_base_dt")
            pay_dt = item.get("divi_pay_dt")
            print(f"   📍 배당기준일: {base_dt} | 현금배당금: {dps}원 | 지급일: {pay_dt}")
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")

async def main():
    if not get_access_token(): return
    await test_ksd_dividend("005930", "삼성전자")
    await asyncio.sleep(0.5)
    await test_ksd_dividend("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
