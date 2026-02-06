import asyncio
import os
import sys
sys.path.append(os.getcwd())
from src.kis_api import kis_get_async
from src.auth import get_access_token

async def test_fetch():
    token = get_access_token()
    if not token:
        print("토큰 획득 실패")
        return
    
    code = "005930" # 삼성전자
    today_str = "20260206"
    
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", 
        "FID_INPUT_ISCD": code, 
        "FID_INPUT_DATE_1": today_str, 
        "FID_INPUT_DATE_2": today_str, 
        "FID_PERIOD_DIV_CODE": "D", 
        "FID_ORG_ADJ_PRC": "0"
    }
    
    print(f"Requesting data for {code} for date {today_str}...")
    res = await kis_get_async(path, params=params, tr_id="FHKST03010100")
    
    if res and "output2" in res:
        data = res["output2"]
        if data:
            print(f"SUCCESS: Date {data[0]['stck_bsop_date']}, Close {data[0]['stck_clpr']}")
        else:
            print("EMPTY: output2 list is empty (Data not ready)")
    else:
        print(f"ERROR: Response error or no data: {res}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
