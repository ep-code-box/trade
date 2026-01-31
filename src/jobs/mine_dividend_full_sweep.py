"""전 종목 주식기본조회(실전 CTPF1002R)로 DPS·PER/PBR 수집. 실행: python -m src.jobs.mine_dividend_full_sweep"""
import time
import pandas as pd

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get


def fetch_stock_basic_info(code):
    path = "/uapi/domestic-stock/v1/quotations/search-stock-info"
    params = {"PRDT_TYPE_CD": "300", "PDNO": code}
    data = kis_get(path, params=params, tr_id="CTPF1002R", use_real=True, delay=0.06)
    return data.get("output") if data else None


def update_db(code, output):
    if not output:
        return
    dps = int(output.get("per_stock_dvdn_amt", 0) or 0)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE master_info SET per_stock_dvdn_amt = ? WHERE code = ?", (dps, code))
    if dps > 0:
        cur.execute(
            "UPDATE daily_analysis SET dividend_yield = (CAST(? AS REAL) / close) * 100 WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)",
            (dps, code, code),
        )
    conn.commit()
    conn.close()


def main():
    if not get_access_token():
        print("Token Error")
        return
    conn = get_connection()
    stocks = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) = 6", conn)
    conn.close()
    total = len(stocks)
    print(f"--- [전수조사] {total}개 종목 배당 마이닝 시작 ---")
    success = 0
    for idx, row in stocks.iterrows():
        code = row["code"]
        print(f"[{idx+1}/{total}] {row['name']}({code}) 처리 중...", end="\r")
        output = fetch_stock_basic_info(code)
        if output:
            update_db(code, output)
            success += 1
        if idx > 0 and idx % 100 == 0:
            print(f"\n{idx}개 완료... 잠시 대기")
            time.sleep(1)
    print(f"\n전수조사 완료. 성공: {success} / 전체: {total}")


if __name__ == "__main__":
    main()
