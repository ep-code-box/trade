"""일봉·지표 수집 후 daily_analysis 적재. 실행: python -m src.jobs.fetch_daily_price"""
import sqlite3
import time
import pandas as pd
from datetime import datetime, timedelta

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get


def get_target_stocks_with_last_date():
    conn = get_connection()
    df_master = pd.read_sql_query("SELECT code, name FROM master_info WHERE LENGTH(code) = 6", conn)
    df_last = pd.read_sql_query("SELECT code, MAX(date) as last_date FROM daily_analysis GROUP BY code", conn)
    conn.close()
    return pd.merge(df_master, df_last, on="code", how="left")


def fetch_price_history(code, start_date, end_date):
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "1",
    }
    data = kis_get(path, params=params, tr_id="FHKST03010100", use_real=False, delay=0.06)
    return data.get("output2") if data else None


def process_and_save(code, data_list):
    if not data_list:
        return
    df = pd.DataFrame(data_list)
    df = df[["stck_bsop_date", "stck_clpr", "stck_oprc", "stck_hgpr", "stck_lwpr", "acml_vol", "acml_tr_pbmn"]]
    df.columns = ["date", "close", "open", "high", "low", "volume", "amount"]
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = pd.to_numeric(df[col])
    df = df.sort_values("date").reset_index(drop=True)

    conn = get_connection()
    past_df = pd.read_sql_query("SELECT * FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 200", conn, params=(code,))
    if not past_df.empty:
        past_df = past_df.sort_values("date").reset_index(drop=True)
        past_df_core = past_df[["date", "close", "open", "high", "low", "volume", "amount"]]
        full_df = pd.concat([past_df_core, df]).drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    else:
        full_df = df

    full_df["sma_20"] = full_df["close"].rolling(window=20).mean()
    full_df["sma_50"] = full_df["close"].rolling(window=50).mean()
    full_df["sma_150"] = full_df["close"].rolling(window=150).mean()
    full_df["sma_200"] = full_df["close"].rolling(window=200).mean()
    full_df["volume_sma_50"] = full_df["volume"].rolling(window=50).mean()
    full_df["vol_std_10d"] = full_df["close"].rolling(window=10).std()
    full_df["vol_std_50d"] = full_df["close"].rolling(window=50).std()
    full_df["high_52w"] = full_df["close"].rolling(window=250, min_periods=1).max()
    full_df["low_52w"] = full_df["close"].rolling(window=250, min_periods=1).min()
    full_df["dividend_yield"] = 0.0
    full_df["rs_score"] = 0.0

    new_dates = df["date"].tolist()
    save_df = full_df[full_df["date"].isin(new_dates)].copy()
    db_df = save_df[
        [
            "date", "close", "volume", "amount", "sma_20", "sma_50", "sma_150", "sma_200",
            "high_52w", "low_52w", "rs_score", "vol_std_10d", "vol_std_50d", "dividend_yield", "volume_sma_50",
        ]
    ].copy()
    db_df["code"] = code
    db_df["market_cap"] = None

    try:
        db_df.to_sql("daily_analysis", conn, if_exists="append", index=False)
    except sqlite3.IntegrityError:
        pass
    except Exception:
        pass
    conn.close()


def main():
    if not get_access_token():
        print("Token Error")
        return
    stocks = get_target_stocks_with_last_date()
    total = len(stocks)
    today_str = datetime.now().strftime("%Y%m%d")
    print(f"Checking updates for {total} stocks...")
    update_count = 0
    for idx, row in stocks.iterrows():
        code = row["code"]
        last_date = row["last_date"]
        if pd.isna(last_date):
            start_dt = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
        else:
            if str(last_date) >= today_str:
                continue
            last_dt_obj = datetime.strptime(str(last_date), "%Y%m%d")
            start_dt = (last_dt_obj + timedelta(days=1)).strftime("%Y%m%d")
            if start_dt > today_str:
                continue
        print(f"[{idx+1}/{total}] Updating {row['name']}({code}) from {start_dt}...", end="\r")
        data = fetch_price_history(code, start_dt, today_str)
        if data:
            process_and_save(code, data)
            update_count += 1
        if idx > 0 and idx % 100 == 0:
            time.sleep(0.5)
    print(f"\nDone. Updated: {update_count} stocks.")


if __name__ == "__main__":
    main()
