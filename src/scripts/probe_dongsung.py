
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def probe_dongsung():
    code = "002210" # 동성케미컬
    print(f"\n🔍 [{code}] 동성케미컬 정밀 재조사 시작...")
    
    # 1. 주식현재가 (FHKST01010100)
    res_p = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", 
                                   params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
                                   tr_id="FHKST01010100", use_real=True)
    
    # 2. 안정성비율 (FHKST01010600)
    res_s = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-stability", 
                                   params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
                                   tr_id="FHKST01010600", use_real=True)
    
    # 3. 주식기본조회 (CTPF1002R)
    res_b = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/search-stock-info", 
                                   params={"PRDT_TYPE_CD": "300", "PDNO": code},
                                   tr_id="CTPF1002R", use_real=True)

    print("\n--- [방법 1: 주식현재가] ---")
    if res_p and "output" in res_p:
        o = res_p["output"]
        print(f"현재가: {o.get('stck_prpr')} | DPS: {o.get('per_stock_dvdn_amt')} | 수익률: {o.get('dvdn_rate')}")
    
    print("\n--- [방법 2: 안정성비율] ---")
    if res_s and "output" in res_s:
        o = res_s["output"]
        print(f"ROE: {o.get('roe_val')} | 배당수익률(dvdn_rate): {o.get('dvdn_rate')}")
        if o.get('dvdn_rate') == "2192.00":
            print("🚨 범인 포착! 안정성비율 API의 dvdn_rate 필드가 2192.00을 뱉고 있습니다.")

    print("\n--- [방법 3: 주식기본조회] ---")
    if res_b and "output" in res_b:
        o = res_b["output"]
        print(f"상장주수: {o.get('lstg_stqt')} | 기준가: {o.get('stck_sdpr')} | 락구분: {o.get('flng_cls_code')}")

async def main():
    if not get_access_token(): return
    await probe_dongsung()

if __name__ == "__main__":
    asyncio.run(main())
