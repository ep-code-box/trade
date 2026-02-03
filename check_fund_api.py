from src.auth import get_access_token
from src.kis_api import kis_get_raw
import json

def check():
    if not get_access_token(): return
    
    code = "005930" # Samsung Electronics
    path = "/uapi/domestic-stock/v1/finance/financial-ratio"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_DIV_CLS_CODE": "0"
    }
    
    print(f"Requesting {path} for {code}...")
    res = kis_get_raw(path, params=params, tr_id="FHKST66430300", use_real=True)
    
    if res and "output" in res:
        print(json.dumps(res["output"], indent=2, ensure_ascii=False))
    else:
        print("No output or error:", res)

if __name__ == "__main__":
    check()
