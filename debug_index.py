from src.kis_api import kis_get_raw
from datetime import datetime

path = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
params = {
    "FID_COND_MRKT_DIV_CODE": "U",
    "FID_INPUT_ISCD": "0001",
    "FID_INPUT_DATE_1": "20250101",
    "FID_INPUT_DATE_2": datetime.now().strftime("%Y%m%d"),
    "FID_PERIOD_DIV_CODE": "D"
}
res = kis_get_raw(path, params=params, tr_id="FHKUP03500100")
print(res)
