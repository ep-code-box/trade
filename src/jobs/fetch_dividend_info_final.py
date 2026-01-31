"""실전 주식기본조회(배당 DPS) 후 master_info·daily_analysis 업데이트. 실행: python -m src.jobs.fetch_dividend_info_final"""
import pandas as pd

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get


def fetch_dps_real(code):
    path = "/uapi/domestic-stock/v1/quotations/search-stock-info"
    params = {"PRDT_TYPE_CD": "300", "PDNO": code}
    data = kis_get(path, params=params, tr_id="CTPF40020000", use_real=True, delay=0.05)
    if not data or "output" not in data:
        return 0
    dps = data["output"].get("per_stock_dvdn_amt", 0)
    return dps


def update_dividend_db(code, dps):
    if not dps:
        return
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE master_info SET per_stock_dvdn_amt = ? WHERE code = ?", (dps, code))
        cur.execute(
            "UPDATE daily_analysis SET dividend_yield = (CAST(? AS REAL) / close) * 100 WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)",
            (dps, code, code),
        )
    except Exception:
        pass
    conn.commit()
    conn.close()


def main():
    if not get_access_token():
        print("Token Error")
        return
    conn = get_connection()
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE scrt_grp_cls_code='ST'", conn)
    conn.close()
    total = len(stocks)
    print(f"Fetching DPS for {total} stocks via Real API...")
    for idx, row in stocks.iterrows():
        code = row["code"]
        dps = fetch_dps_real(code)
        if dps and int(dps) > 0:
            update_dividend_db(code, dps)
            print(f"[{idx+1}/{total}] {row['name']}({code}): DPS {dps} - UPDATED")
        else:
            print(f"[{idx+1}/{total}] {row['name']}({code}): No Dividend", end="\r")
    print("\nDividend sync complete.")


if __name__ == "__main__":
    main()
