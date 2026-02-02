
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_async, kis_get_raw_async
import json

async def test_api_raw(name, path, params, tr_id):
    """API의 원시 응답을 그대로 출력하여 구조 확인"""
    print(f"\n[테스트: {name}] TR_ID: {tr_id}")
    res = await kis_get_raw_async(path, params=params, tr_id=tr_id, use_real=True)
    if res:
        # 데이터가 너무 길면 일부만 출력
        output = res.get("output", res.get("output1", res))
        print(json.dumps(output, indent=2, ensure_ascii=False)[:1000])
        return output
    print("응답 없음")
    return None

async def main():
    if not get_access_token(): return
    
    # 1. 삼성전자(005930) 대상 테스트
    target_code = "005930"
    
    # [방법 A] 주식기본조회 (기존 방식)
    await test_api_raw("주식기본조회", "/uapi/domestic-stock/v1/quotations/search-stock-info", 
                      {"PRDT_TYPE_CD": "300", "PDNO": target_code}, "CTPF40020000")
    
    # [방법 B] 배당률 상위 조회 (순위 방식)
    # FID_DIV_CLS_CODE: 0(전체), 1(코스피), 2(코스닥)
    await test_api_raw("배당률 상위(KOSPI)", "/uapi/domestic-stock/v1/ranking/dividend-rate", 
                      {"FID_DIV_CLS_CODE": "1", "FID_RANK_SORT_CLS_CODE": "0"}, "HHKDB13470100")

    # [방법 C] 예탁원 배당일정 (공시 방식)
    await test_api_raw("예탁원 배당일정", "/uapi/domestic-stock/v1/ksdinfo/dividend", 
                      {"SHTN_PDNO": target_code, "INQR_STRT_DT": "20240101", "INQR_END_DT": "20241231"}, "HHKDB669102C0")

if __name__ == "__main__":
    asyncio.run(main())
