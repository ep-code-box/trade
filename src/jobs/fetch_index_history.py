"""KOSPI(0001), KOSDAQ(1001) 지수 데이터를 수집하여 daily_analysis에 적재합니다."""
import time
import pandas as pd
from datetime import datetime, timedelta
from src.db import get_connection
from src.kis_api import kis_get_raw

def fetch_index_chart(code, start_date, end_date):
    """
    업종/지수 일봉 조회 (FHKUP03500100) - 여러 번 호출하여 데이터 확보
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
    all_data = []
    current_end = end_date
    
    for i in range(4):  # 최대 400일치 (1회당 100개)
        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": current_end,
            "FID_PERIOD_DIV_CODE": "D"
        }
        time.sleep(0.2)
        res = kis_get_raw(path, params=params, tr_id="FHKUP03500100")
        
        if not res or "output2" not in res or not res["output2"]:
            break
            
        chunk = res["output2"]
        all_data.extend(chunk)
        
        if len(chunk) < 100:
            break
            
        # 다음 호출을 위해 종료일 조정 (마지막 날짜 - 1일)
        last_date_str = chunk[-1]["stck_bsop_date"]
        current_end = (datetime.strptime(last_date_str, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        if current_end < start_date:
            break
            
    return all_data

def save_index_to_db(code, data_list):
    if not data_list:
        return

    conn = get_connection()
    df = pd.DataFrame(data_list)
    
    # 필드명 매핑 (API -> DB)
    # API: stck_bsop_date(일자), bstp_nmix_prpr(현재가), acml_vol(거래량), acml_tr_pbmn(거래대금)
    # bstp_nmix_oprc(시가), bstp_nmix_hgpr(고가), bstp_nmix_lwpr(저가)
    
    rename_map = {
        "stck_bsop_date": "date",
        "bstp_nmix_prpr": "close",
        "bstp_nmix_oprc": "open",
        "bstp_nmix_hgpr": "high",
        "bstp_nmix_lwpr": "low",
        "acml_vol": "volume",
        "acml_tr_pbmn": "amount"
    }
    
    # 존재하는 컬럼만 선택하여 이름 변경
    cols_to_use = [c for c in rename_map.keys() if c in df.columns]
    df = df[cols_to_use].rename(columns=rename_map)
    
    # 숫자 변환
    numeric_cols = ["close", "open", "high", "low", "volume", "amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
    # 지표 계산 (SMA, Volatility)
    df = df.sort_values("date").reset_index(drop=True)
    
    # 기존 데이터와 병합 로직은 생략하고 단순 덮어쓰기/추가 (지수는 양이 적으므로)
    # 인덱스 계산을 위해 250일치 이상 필요
    
    df["sma_20"] = df["close"].rolling(window=20).mean()
    df["sma_50"] = df["close"].rolling(window=50).mean()
    df["sma_150"] = df["close"].rolling(window=150).mean()
    df["sma_200"] = df["close"].rolling(window=200).mean()
    df["volume_sma_50"] = df["volume"].rolling(window=50).mean()
    df["vol_std_10d"] = df["close"].rolling(window=10).std()
    df["vol_std_50d"] = df["close"].rolling(window=50).std()
    df["high_52w"] = df["close"].rolling(window=250, min_periods=1).max()
    df["low_52w"] = df["close"].rolling(window=250, min_periods=1).min()
    df["rs_score"] = 0 # 지수 자체는 RS 0 처리
    df["dividend_yield"] = 0
    
    # DB 저장용 컬럼 준비
    df["code"] = code
    final_df = df[[
        "date", "code", "close", "volume", "amount",
        "sma_20", "sma_50", "sma_150", "sma_200",
        "high_52w", "low_52w", "rs_score",
        "vol_std_10d", "vol_std_50d", "dividend_yield", "volume_sma_50"
    ]].copy()
    
    # 중복 방지를 위해 삭제 후 삽입 (지수는 데이터 양이 적음)
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_analysis WHERE code = ?", (code,))
    final_df.to_sql("daily_analysis", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"Saved {len(final_df)} rows for Index {code}")

def main():
    targets = [("0001", "KOSPI"), ("1001", "KOSDAQ")]
    
    # [TrendHunter Policy] 18:00 이전에는 어제를 기준일로 삼음
    now = datetime.now()
    if now.hour < 18:
        end_date = (now - timedelta(days=1)).strftime("%Y%m%d")
    else:
        end_date = now.strftime("%Y%m%d")
        
    # 2년치 데이터 확보 (200일선 계산용)
    start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=730)).strftime("%Y%m%d")
    
    print(f"Updating Index History ({start_date} ~ {end_date})...")
    
    for code, name in targets:
        print(f"Fetching {name} ({code})...")
        data = fetch_index_chart(code, start_date, end_date)
        if data:
            save_index_to_db(code, data)
        else:
            print(f"Failed to get data for {name}")

if __name__ == "__main__":
    main()
