"""주식현재가 상세(PER/PBR 등) 조회 후 master_info·daily_analysis 업데이트. 실행: python -m src.jobs.fetch_stock_fundamentals"""
import time
import pandas as pd
from datetime import datetime

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get


def get_target_stocks():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT code, name FROM master_info WHERE market_type IN ('KOSPI', 'KOSDAQ') AND scrt_grp_cls_code = 'ST'",
        conn,
    )
    conn.close()
    return df


def fetch_details(code):
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    data = kis_get(path, params=params, tr_id="FHKST01010100", use_real=False, delay=0.05)
    return data.get("output") if data else None


def update_db(code, data):
    if not data:
        return
    conn = get_connection()
    cur = conn.cursor()
    try:
        per = float(data.get("per", 0.0) or 0.0)
        pbr = float(data.get("pbr", 0.0) or 0.0)
        market_cap = int(data.get("hts_avls", 0) or 0) * 100_000_000
        cur.execute(
            "UPDATE daily_analysis SET market_cap = ? WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)",
            (market_cap, code, code),
        )
        cur.execute("UPDATE master_info SET per = ?, pbr = ? WHERE code = ?", (per, pbr, code))
    except Exception:
        pass
    conn.commit()
    conn.close()


def main():
    if not get_access_token():
        print("Token Error")
        return
    stocks = get_target_stocks()
    total = len(stocks)
    print(f"Fetching fundamentals for {total} stocks...")
    success = 0
    for idx, row in stocks.iterrows():
        print(f"[{idx+1}/{total}] {row['name']}({row['code']})", end="\r")
        data = fetch_details(row["code"])
        if data:
            update_db(row["code"], data)
            success += 1
        if idx > 0 and idx % 50 == 0:
            time.sleep(0.5)
    print(f"\nDone. Success: {success}")


if __name__ == "__main__":
    main()
