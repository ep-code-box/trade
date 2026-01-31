"""KIS API vs pykrx 배당 수익률 비교 (특정 종목). 실행: python -m src.scripts.compare_dividend_sources"""
import requests
from pykrx import stock

from src.auth import get_access_token, APP_KEY, APP_SECRET, REAL_BASE_URL


def get_kis_dividend_yield(code):
    token = get_access_token()
    if not token:
        return 0, 0, 0
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "HHKDB13470100",
        "custtype": "P",
    }
    params = {"CTS_AREA": "", "GB1": "0", "UPJONG": "0001", "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": "0"}
    res = requests.get(f"{REAL_BASE_URL}/uapi/domestic-stock/v1/ranking/dividend-rate", headers=headers, params=params, timeout=30)
    if res.status_code == 200:
        data = res.json().get("output", [])
        total_dps = sum(int(i["per_sto_divi_amt"]) for i in data if i.get("sht_cd") == code)
        price_res = requests.get(
            "https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=headers,
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
            timeout=30,
        )
        json_data = price_res.json()
        if "output" in json_data and isinstance(json_data["output"], dict):
            curr_price = int(json_data["output"]["stck_prpr"])
        else:
            curr_price = 0
        yield_pct = (total_dps / curr_price) * 100 if curr_price > 0 else 0
        return total_dps, curr_price, yield_pct
    return 0, 0, 0


def get_pykrx_dividend_yield(code):
    target_date = "20260130"
    df = stock.get_market_fundamental(target_date, target_date, code)
    if not df.empty:
        return df.iloc[0]["DPS"], df.iloc[0]["DIVIDEND"]
    return 0, 0


def main():
    code = "000810"
    print(f"=== [{code}] 배당 데이터 소스 비교 분석 ===")
    kis_dps, kis_price, kis_yield = get_kis_dividend_yield(code)
    pykrx_dps, pykrx_yield = get_pykrx_dividend_yield(code)
    print("\n[데이터 소스 A: 한국투자증권 API]")
    print(f"  DPS: {kis_dps:,}원 | 현재가: {kis_price:,}원 | 수익률: {kis_yield:.2f}%")
    print("\n[데이터 소스 B: pykrx (KRX)]")
    print(f"  DPS: {pykrx_dps:,.0f} | 수익률: {pykrx_yield:.2f}%")


if __name__ == "__main__":
    main()
