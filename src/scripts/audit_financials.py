
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def audit_financial_statements(code, name):
    print(f"\n🔍 [{name} ({code})] 재무제표(손익계산서) 공식 규격 감사 시작...")
    
    # TR FHKST66430200: 국내주식 손익계산서
    path = "/uapi/domestic-stock/v1/finance/income-statement"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0" # 0:년, 1:분기
    }
    
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST66430200", use_real=True)
    
    if res and "output" in res and res["output"]:
        # 최신 3개년치 데이터 분석
        print(f"✅ 총 {len(res['output'])}개년치 데이터 수신 성공")
        print(f"{ '연도':<10} | {'매출액(억)':>15} | {'영업이익(억)':>15} | {'당기순익(억)':>15}")
        print("-" * 65)
        
        for item in res["output"][:3]:
            year = item.get("stac_yymm", "N/A")
            sales = item.get("sale_account", "0")
            operating_profit = item.get("bsop_prti", "0")
            net_income = item.get("thtr_ntin", "0")
            
            print(f"{year:<10} | {float(sales):>15,.0f} | {float(operating_profit):>15,.0f} | {float(net_income):>15,.0f}")
            
        return res["output"][0]
    else:
        print(f"❌ 데이터 수신 실패: {res.get('msg1') if res else '응답 없음'}")
        return None

async def main():
    if not get_access_token(): return
    # 삼성전자와 현대차를 대상으로 재무제표 데이터 감사
    await audit_financial_statements("005930", "삼성전자")
    await asyncio.sleep(0.5)
    await audit_financial_statements("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
