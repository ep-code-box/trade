"""배당순위 API 원천 데이터 샘플 1건 출력. 실행: python -m src.scripts.debug_api"""
from src.auth import get_access_token
from src.kis_api import kis_get_raw


def debug_check():
    if not get_access_token():
        print("Token Error")
        return
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    params = {"CTS_AREA": "", "GB1": "1", "UPJONG": "0001", "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": "1"}
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True)
    if data:
        output = data.get("output", [])
        if output:
            print(f"원천 데이터 샘플: '{output[0].get('sht_cd')}' (길이: {len(str(output[0].get('sht_cd', '')))})")
            print(f"종목명: {output[0].get('isin_name')}")


if __name__ == "__main__":
    debug_check()
