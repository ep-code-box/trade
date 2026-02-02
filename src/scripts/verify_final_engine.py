
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import pandas as pd

async def verify_engine_logic(code):
    print(f"\n🚀 [{code}] 최종 엔진 로직 검증 시작...")
    
    # 1. ROE 수집 (안정성 비율)
    path_stab = "/uapi/domestic-stock/v1/quotations/inquire-stability"
    res_stab = await kis_get_raw_async(path_stab, params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}, tr_id="FHKST01010600", use_real=True)
    
    # 2. 배당성향 수집 (기타 주요 비율)
    path_ratio = "/uapi/domestic-stock/v1/finance/other-major-ratios"
    res_ratio = await kis_get_raw_async(path_ratio, params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}, tr_id="FHKST66430500", use_real=True)
    
    roe_raw = res_stab.get("output", {}).get("roe_val", "0") if res_stab else "0"
    payout_raw = res_ratio.get("output")[0].get("payout_rate", "0") if res_ratio and res_ratio.get("output") else "0"
    
    print(f"   [Raw Data] ROE 원본: {roe_raw} | 배당성향 원본: {payout_raw}")
    
    # 파싱 로직 적용
    try:
        roe = float(roe_raw[6:]) if len(str(roe_raw)) > 6 and '.' not in str(roe_raw)[:6] else float(roe_raw)
        payout = float(payout_raw)
        print(f"   [Parsed] 보정된 ROE: {roe:.2f}% | 보정된 배당성향: {payout:.2f}%")
        
        if roe > 0:
            print(f"   ✅ ROE {roe:.2f}% 포착 성공! 기초 체력이 확인되었습니다.")
        if payout >= 0:
            print(f"   ✅ 배당성향 {payout:.2f}% 포착 성공! 배당 정책이 확인되었습니다.")
            
    except Exception as e:
        print(f"   ❌ 파싱 오류: {e}")

async def main():
    if not get_access_token(): return
    await verify_engine_logic("005930") # 삼성전자
    await verify_engine_logic("005380") # 현대차

if __name__ == "__main__":
    asyncio.run(main())
