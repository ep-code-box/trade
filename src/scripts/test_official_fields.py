
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def test_official_fields(code, name):
    print(f"\n🚀 [{name} ({code})] 공식 필드 추출 테스트...")
    
    # 1. 주식현재가 (FHKST01010100)
    res_p = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", 
                                   params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}, 
                                   tr_id="FHKST01010100", use_real=True)
    
    # 2. 주식기본조회 (CTPF1002R)
    res_b = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/search-stock-info", 
                                   params={"PRDT_TYPE_CD": "300", "PDNO": code}, 
                                   tr_id="CTPF1002R", use_real=True)
    
    print(f"--- [방법 1: 주식현재가] ---")
    if res_p and "output" in res_p:
        o = res_p["output"]
        print(f"상장주수(lstn_stcn): {o.get('lstn_stcn')}")
        print(f"주당배당금(per_stock_dvdn_amt): {o.get('per_stock_dvdn_amt')}")
        print(f"배당수익률(dvdn_rate): {o.get('dvdn_rate')}")
    else:
        print("실패")

    print(f"--- [방법 2: 주식기본조회] ---")
    if res_b and "output" in res_b:
        o = res_b["output"]
        # 모든 배당 관련 필드 출력
        found = {k: v for k, v in o.items() if any(x in k.lower() for x in ['dvdn', 'stcn', 'amt'])}
        print(json.dumps(found, indent=2, ensure_ascii=False))
    else:
        print("실패")

async def main():
    if not get_access_token(): return
    for c, n in [("005930", "삼성전자"), ("005380", "현대차"), ("033780", "KT&G")]:
        await test_official_fields(c, n)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
