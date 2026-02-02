
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async

async def hunt_for_dividend_value(code, name):
    print(f"\n🚀 [{name}] 진짜 배당금 수치 사냥 시작...")
    
    # 사냥할 타겟 API들
    targets = [
        ("재무비율", "/uapi/domestic-stock/v1/finance/financial-ratio", "FHKST66430300"),
        ("수익성", "/uapi/domestic-stock/v1/finance/profit-ratio", "FHKST66430400"),
        ("기타비율", "/uapi/domestic-stock/v1/finance/other-major-ratios", "FHKST66430500"),
        ("대차대조표", "/uapi/domestic-stock/v1/finance/balance-sheet", "FHKST66430100"),
        ("손익계산서", "/uapi/domestic-stock/v1/finance/income-statement", "FHKST66430200")
    ]
    
    for api_name, path, tr_id in targets:
        res = await kis_get_raw_async(path, params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_DIV_CLS_CODE": "0"}, tr_id=tr_id, use_real=True)
        if res and "output" in res:
            # 전체 JSON 문자열에서 11200 (현대차 예상 DPS) 또는 유사 수치 검색
            raw_str = str(res["output"])
            if "11200" in raw_str or "11,200" in raw_str or "132299" in raw_str:
                print(f"✅ [{api_name}] 에서 유력한 수치 포착!")
                print(raw_str[:500]) # 증거 출력

async def main():
    if not get_access_token(): return
    await hunt_for_dividend_value("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())
