
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def sample_audit(code, name):
    print(f"\n🧪 [{name} ({code})] 정석 수식 샘플링 감찰...")
    
    # 1. 실제 주수 (CTPF1002R)
    res_shares = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/search-stock-info", 
                                        params={"PRDT_TYPE_CD": "300", "PDNO": code}, 
                                        tr_id="CTPF1002R", use_real=True)
    
    # 2. 당기순이익 (FHKST66430200) - 연도별(0)
    res_income = await kis_get_raw_async("/uapi/domestic-stock/v1/finance/income-statement", 
                                        params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}, 
                                        tr_id="FHKST66430200", use_real=True)
    
    # 3. 배당성향 (FHKST66430500) - 연도별(0)
    res_ratio = await kis_get_raw_async("/uapi/domestic-stock/v1/finance/other-major-ratios", 
                                       params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}, 
                                       tr_id="FHKST66430500", use_real=True)

    try:
        # 공식 데이터 추출
        shares = float(res_shares["output"]["lstg_stqt"])
        
        # 2024년 결산 데이터(12월) 찾기
        income_item = next(i for i in res_income["output"] if i["stac_yymm"] == "202412")
        net_income_mil = float(income_item["thtr_ntin"])
        
        ratio_item = next(i for i in res_ratio["output"] if i["stac_yymm"] == "202412")
        payout_rate = float(ratio_item["payout_rate"])

        # [명세서 기반 정석 수식 적용]
        # EPS = (당기순익_백만원 * 1,000,000) / 실제주수
        eps = (net_income_mil * 1000000) / shares
        # DPS = EPS * payout_rate
        calculated_dps = int(eps * payout_rate)

        print(f"   [Raw] 주수: {shares:,.0f} | 순익(백만): {net_income_mil:,.0f} | 성향: {payout_rate}")
        print(f"   [Calc] 계산된 EPS: {eps:,.0f}원 | 최종 계산 DPS: {calculated_dps:,}원")
        
        # 실제 데이터와 대조 가이드 (예: 현대차 24년 DPS는 약 11,200원 수준)
        print(f"   💡 검증: 계산된 {calculated_dps:,}원이 실제 공시치와 일치하는지 확인하십시오.")

    except Exception as e:
        print(f"   ❌ 샘플링 실패: {e}")

async def main():
    if not get_access_token(): return
    # 배당이 명확한 현대차와 KT&G로 샘플링
    await sample_audit("005380", "현대차")
    await asyncio.sleep(0.5)
    await sample_audit("033780", "KT&G")

if __name__ == "__main__":
    asyncio.run(main())
