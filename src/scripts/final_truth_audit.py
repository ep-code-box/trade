
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def the_final_truth_audit(code, name):
    print(f"\n🚀 [{name}] 주식기본조회(CTPF1002R) 전 필드 덤프...")
    path = "/uapi/domestic-stock/v1/quotations/search-stock-info"
    params = {"PRDT_TYPE_CD": "300", "PDNO": code}
    res = await kis_get_raw_async(path, params=params, tr_id="CTPF1002R", use_real=True)
    if res and "output" in res:
        output = res["output"]
        # 모든 필드를 알파벳 순으로 정렬하여 출력
        sorted_output = dict(sorted(output.items()))
        print(json.dumps(sorted_output, indent=2, ensure_ascii=False))
    else:
        print(f"실패: {res}")

async def main():
    if not get_access_token(): return
    await the_final_truth_audit("005380", "현대차")

if __name__ == "__main__":
    asyncio.run(main())

