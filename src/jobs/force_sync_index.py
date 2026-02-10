import time
import pandas as pd
from datetime import datetime, timedelta
from src.db import get_connection
from src.kis_api import kis_get_raw

def fetch_index_full_history(code):
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
    all_data = []
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=1200)).strftime("%Y%m%d")
    current_end = end_date
    
    print(f"-> Fetching {code} from {start_date} to {end_date}...")
    for i in range(15):
        params = {
            "FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date, "FID_INPUT_DATE_2": current_end,
            "FID_PERIOD_DIV_CODE": "D"
        }
        res = kis_get_raw(path, params=params, tr_id="FHKUP03500100")
        if not res or "output2" not in res or not res["output2"]: break
        chunk = res["output2"]
        all_data.extend(chunk)
        last_date_str = chunk[-1]["stck_bsop_date"]
        if last_date_str == current_end: break
        current_end = (datetime.strptime(last_date_str, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        if current_end < start_date: break
        time.sleep(0.1)
    return all_data

def sync_index():
    conn = get_connection()
    for code, name in [("0001", "KOSPI"), ("1001", "KOSDAQ")]:
        data = fetch_index_full_history(code)
        if not data: continue
        df = pd.DataFrame(data)
        df = df.rename(columns={
            "stck_bsop_date": "date", "bstp_nmix_prpr": "close",
            "bstp_nmix_oprc": "open", "bstp_nmix_hgpr": "high", "bstp_nmix_lwpr": "low",
            "acml_vol": "volume", "acml_tr_pbmn": "amount"
        })
        for col in ["close", "open", "high", "low", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col])
        df = df.sort_values("date").reset_index(drop=True)
        
        # 지표 계산
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["sma_150"] = df["close"].rolling(window=150).mean()
        df["sma_200"] = df["close"].rolling(window=200).mean()
        df["volume_sma_50"] = df["volume"].rolling(window=50).mean()
        df["vol_std_10d"] = df["close"].rolling(window=10).std()
        df["vol_std_50d"] = df["close"].rolling(window=50).std()
        df["high_52w"] = df["close"].rolling(window=250, min_periods=1).max()
        df["low_52w"] = df["close"].rolling(window=250, min_periods=1).min()
        df["code"] = code
        df["rs_score"] = 0
        df["dividend_yield"] = 0

        # DB에 존재하는 컬럼만 필터링 (에러 방지 핵심)
        valid_cols = [
            "date", "code", "open", "high", "low", "close", "volume", "amount",
            "sma_20", "sma_50", "sma_150", "sma_200", "high_52w", "low_52w",
            "rs_score", "vol_std_10d", "vol_std_50d", "dividend_yield", "volume_sma_50"
        ]
        final_df = df[[c for c in valid_cols if c in df.columns]].copy()
        
        cur = conn.cursor()
        cur.execute("DELETE FROM daily_analysis WHERE code = ?", (code,))
        final_df.to_sql("daily_analysis", conn, if_exists="append", index=False)
        conn.commit()
        print(f"✅ {name}: {len(final_df)} rows saved.")
    conn.close()

if __name__ == "__main__": sync_index()