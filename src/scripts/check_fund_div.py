
import asyncio
from src.auth import get_access_token
from src.kis_api import kis_get_raw_async
import json

async def check_fundamental_dividend(code):
    path = "/uapi/domestic-stock/v1/quotations/inquire-stability"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = await kis_get_raw_async(path, params=params, tr_id="FHKST01010600", use_real=True)
    if res and "output" in res:
        print(f"\n[펀더멘털 API 응답: {code}]")
        # 배당 관련 필드명이 있는지 샅샅이 뒤집니다.
        output = res["output"]
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
        # 예상되는 배당 필드: per_stock_dvdn_amt, dvdn_rate, dvdn_pay_dt 등
        dps = output.get("per_stock_dvdn_amt") or output.get("dvdn_amt")
        print(f"\n포착된 배당금(DPS): {dps}")

async def main():
    if not get_access_token(): return
    await check_fundamental_dividend("005930") # 삼성전자

if __name__ == "__main__":
    asyncio.run(main())

