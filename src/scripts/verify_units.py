
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
from src.db import get_connection
import pandas as pd

async def verify_share_units(code, name):
    print(f"\n🔍 [{name} ({code})] 단위 검증 시작...")
    
    # 1. DB(MST 파싱 결과)에서의 상장주수 확인
    conn = get_connection()
    db_res = conn.execute("SELECT lstn_stcn, market_type FROM master_info WHERE code = ?", (code,)).fetchone()
    conn.close()
    
    # 2. 주식현재가 API (FHKST01010100) 호출하여 실제 상장주수 확인
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    api_res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010100", use_real=True)
    
    if db_res and api_res and "output" in api_res:
        mst_shares = float(db_res[0])
        api_shares = float(api_res["output"]["lstn_stcn"])
        market_type = db_res[1]
        
        ratio = api_shares / mst_shares
        print(f"   - MST 저장값: {mst_shares:,.0f}")
        print(f"   - API 실젯값: {api_shares:,.0f}")
        print(f"   - [결과] 배수 차이: {ratio:.1f}배 | 시장: {market_type}")
        
        if 900 <= ratio <= 1100:
            print(f"   💡 확정: {market_type}의 MST 상장주수는 '천 주' 단위입니다.")
        elif 0.9 <= ratio <= 1.1:
            print(f"   💡 확정: {market_type}의 MST 상장주수는 '개별 주' 단위입니다.")
        else:
            print(f"   ⚠️ 주의: 단위가 일반적이지 않습니다. 확인 필요.")

async def main():
    if not get_access_token(): return
    # 코스피 대장(삼성전자), 코스피 뻥튀기 의심(LIG넥스원), 코스닥(에코프로비엠) 비교
    await verify_share_units("005930", "삼성전자")
    await verify_share_units("079550", "LIG넥스원")
    await verify_share_units("247540", "에코프로비엠")

if __name__ == "__main__":
    asyncio.run(main())
