"""배당순위 API(코스피/코스닥·결산/중간) 수집 후 DB 업데이트. 실행: python -m src.jobs.fetch_high_dividend_rank"""
from datetime import datetime

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_rank(market_gb="1", dividend_gb="0"):
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    params = {
        "CTS_AREA": "", "GB1": market_gb, "UPJONG": "0001",
        "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": dividend_gb,
    }
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True, delay=0.1)
    if not data:
        return []
    if data.get("rt_cd") != "0":
        print(f"API Error: {data.get('msg1', '')}")
        return []
    return data.get("output1", [])


def update_db(data_list):
    if not data_list:
        return
    conn = get_connection()
    cur = conn.cursor()
    for item in data_list:
        code = item.get("sht_cd", "")
        dps = item.get("per_sto_divi_amt")
        yield_pct = item.get("divi_rate")
        cur.execute(
            "UPDATE master_info SET per_stock_dvdn_amt = ?, updated_at = ? WHERE code = ?",
            (dps, datetime.now().strftime("%Y-%m-%d"), code),
        )
        cur.execute(
            "UPDATE daily_analysis SET dividend_yield = ? WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)",
            (yield_pct, code, code),
        )
    conn.commit()
    conn.close()


def main():
    if not get_access_token():
        print("Token Error")
        return
    print("Fetching High Dividend Rankings (Production API)...")
    for m in ["1", "3"]:
        for d in ["1", "2"]:
            m_name = "KOSPI" if m == "1" else "KOSDAQ"
            d_name = "Final" if d == "1" else "Interim"
            print(f"Requesting {m_name} - {d_name}...")
            results = fetch_dividend_rank(m, d)
            if results:
                print(f"Found {len(results)} stocks.")
                update_db(results)
            else:
                print("No data found or Error.")


if __name__ == "__main__":
    main()
