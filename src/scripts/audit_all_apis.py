
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def audit_all_finance_apis(code, name):
    print(f"\n" + "="*80)
    print(f" 🛡️ [{name} ({code})] API 전수 조사 및 이해 (API Audit)")
    print("="*80)
    
    apis = [
        ("주식현재가", "/uapi/domestic-stock/v1/quotations/inquire-price", "FHKST01010100", {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}),
        ("상품기본조회", "/uapi/domestic-stock/v1/quotations/search-info", "CTPF1604R", {"PRDT_TYPE_CD": "300", "PDNO": code}),
        ("재무비율", "/uapi/domestic-stock/v1/finance/financial-ratio", "FHKST66430300", {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}),
        ("손익계산서", "/uapi/domestic-stock/v1/finance/income-statement", "FHKST66430200", {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}),
        ("기타주요비율", "/uapi/domestic-stock/v1/finance/other-major-ratios", "FHKST66430500", {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"})
    ]
    
    results = {}
    for api_name, path, tr_id, params in apis:
        print(f"📡 {api_name} ({tr_id}) 호출 중...")
        res = await kis_get_raw_async(path, params=params, tr_id=tr_id, use_real=True)
        if res and "output" in res:
            out = res["output"]
            if isinstance(out, list): out = out[0]
            
            # 핵심 필드 추출 시도
            shares = out.get("lstn_stcn") or out.get("lstg_stqt")
            dividend = out.get("per_stock_dvdn_amt") or out.get("pft_dvdn_amt_val") or out.get("dvdn_amt")
            roe = out.get("roe_val") or out.get("self_cptl_ntin_inrt")
            net_income = out.get("thtr_ntin")
            
            print(f"   ✅ [데이터] 주수:{shares} | 배당:{dividend} | ROE:{roe} | 당기순익:{net_income}")
            results[api_name] = out
        else:
            print(f"   ❌ [실패] {res.get('msg1') if res else '응답 없음'}")
            
    return results

async def main():
    if not get_access_token(): return
    # 배당과 재무가 가장 확실한 현대차(005380)로 전수 조사
    await audit_all_finance_apis("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
