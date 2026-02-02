
from src.kis_api import kis_get_raw

def debug_dividend_pagination():
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    # Market 1 (KOSPI), Div 1 (Settlement)
    params = {
        "CTS_AREA": "", "GB1": "1", "UPJONG": "0001",
        "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": "1",
    }
    print("Sending request...")
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True)
    if data:
        print("Keys in data:", data.keys())
        # Print non-list keys to find pagination info
        for k, v in data.items():
            if not isinstance(v, list):
                print(f"{k}: {v}")
        
        output = data.get("output", [])
        print(f"Output count: {len(output)}")
    else:
        print("No data returned")

if __name__ == "__main__":
    debug_dividend_pagination()
