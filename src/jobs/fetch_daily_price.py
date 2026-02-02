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
    # 데이터 개수가 200개 미만인 종목들을 찾음
    df_count = pd.read_sql_query("SELECT code, COUNT(*) as cnt, MAX(date) as last_date FROM daily_analysis GROUP BY code", conn)
    conn.close()
    
    df = pd.merge(df_master, df_count, on="code", how="left")
    # 200개 미만이면 last_date를 None으로 만들어 전체 수집 강제
    df.loc[df['cnt'] < 200, 'last_date'] = None
    return df


def fetch_price_history(code, start_date, end_date):
    """최소 300개 이상의 데이터를 가져오기 위해 필요시 반복 호출"""
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    all_data = []
    current_end = end_date
    
    # 최대 5번(500일치) 반복 호출하여 과거 데이터 확보
    for _ in range(5):
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": current_end,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "1",
        }
        data = kis_get(path, params=params, tr_id="FHKST03010100", use_real=False, delay=0.06)
        if not data or not data.get("output2"):
            break
        
        chunk = data.get("output2")
        all_data.extend(chunk)
        
        if len(chunk) < 100: # 더 이상 데이터 없음
            break
            
        # 가장 오래된 날짜를 다음 호출의 end_date로 설정 (중복 방지를 위해 하루 전으로)
        last_date_str = chunk[-1]["stck_bsop_date"]
        last_dt = datetime.strptime(last_date_str, "%Y%m%d")
        current_end = (last_dt - timedelta(days=1)).strftime("%Y%m%d")
        
        if current_end < start_date:
            break
            
    return all_data


def process_and_save(code, data_list):
    if not data_list:
        return
    df = pd.DataFrame(data_list)
    df = df[["stck_bsop_date", "stck_clpr", "stck_oprc", "stck_hgpr", "stck_lwpr", "acml_vol", "acml_tr_pbmn"]]
    df.columns = ["date", "close", "open", "high", "low", "volume", "amount"]
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = pd.to_numeric(df[col])
    
    # 중복 날짜 제거 (API 응답 내 중복 방지)
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    conn = get_connection()
    # 1. 현재 DB에 있는 날짜들 가져오기
    existing_dates = pd.read_sql_query(f"SELECT date FROM daily_analysis WHERE code = '{code}'", conn)["date"].tolist()
    
    # 2. 새로운 데이터만 필터링 (DB에 없는 날짜만)
    new_df = df[~df["date"].isin(existing_dates)].copy()
    
    if new_df.empty:
        conn.close()
        return

    # 3. 지표 계산을 위해 기존 데이터와 합치기 (최대 300일치 버퍼)
    past_df = pd.read_sql_query("SELECT * FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 300", conn, params=(code,))
    conn.close()

    if not past_df.empty:
        past_df = past_df.sort_values("date").reset_index(drop=True)
        # 컬럼명 맞추기
        past_df_core = past_df[["date", "close", "open", "high", "low", "volume", "amount"]]
        full_df = pd.concat([past_df_core, new_df]).drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    else:
        full_df = new_df

    # 4. 지표 재계산
    full_df["sma_20"] = full_df["close"].rolling(window=20).mean()
    full_df["sma_50"] = full_df["close"].rolling(window=50).mean()
    full_df["sma_150"] = full_df["close"].rolling(window=150).mean()
    full_df["sma_200"] = full_df["close"].rolling(window=200).mean()
    full_df["volume_sma_50"] = full_df["volume"].rolling(window=50).mean()
    full_df["vol_std_10d"] = full_df["close"].rolling(window=10).std()
    full_df["vol_std_50d"] = full_df["close"].rolling(window=50).std()
    full_df["high_52w"] = full_df["close"].rolling(window=250, min_periods=1).max()
    full_df["low_52w"] = full_df["close"].rolling(window=250, min_periods=1).min()
    
    # 배당수익률 계산: master_info의 DPS(per_stock_dvdn_amt) 활용
    conn = get_connection()
    dps_row = conn.execute("SELECT per_stock_dvdn_amt FROM master_info WHERE code = ?", (code,)).fetchone()
    conn.close()
    dps = dps_row[0] if dps_row and dps_row[0] else 0
    full_df["dividend_yield"] = full_df["close"].apply(lambda c: (dps / c * 100) if c > 0 else 0.0)
    
    full_df["rs_score"] = 0.0

    # 5. 새로 추가될 행만 추출
    save_df = full_df[full_df["date"].isin(new_df["date"])].copy()
    save_df["code"] = code
    
    db_df = save_df[
        [
            "date", "code", "open", "high", "low", "close", "volume", "amount", 
            "sma_20", "sma_50", "sma_150", "sma_200",
            "high_52w", "low_52w", "rs_score", "vol_std_10d", "vol_std_50d", 
            "dividend_yield", "volume_sma_50",
        ]
    ].copy()
    db_df["market_cap"] = None

    # 6. 저장 (새로운 데이터만 append)
    conn = get_connection()
    try:
        db_df.to_sql("daily_analysis", conn, if_exists="append", index=False)
    except Exception as e:
        print(f"\n[DB 저장 오류] {code}: {e}")
    finally:
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
