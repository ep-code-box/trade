"""daily_analysis 전량 SMA·vol_std·high_52w·volume_sma_50 재계산 후 덮어쓰기. 실행: python -m src.analysis.recalc_indicators"""
import pandas as pd

from src.db import get_connection


def recalc_all():
    conn = get_connection()
    print("DB에서 시세 데이터를 불러오는 중...")
    df = pd.read_sql_query("SELECT * FROM daily_analysis", conn)
    if df.empty:
        print("데이터가 없습니다.")
        conn.close()
        return
    df = df.sort_values(["code", "date"]).reset_index(drop=True)
    print("기술적 지표 재계산 중 (SMA, Volume SMA)...")
    group = df.groupby("code")
    df["volume_sma_50"] = group["volume"].transform(lambda x: x.rolling(window=50).mean())
    df["sma_20"] = group["close"].transform(lambda x: x.rolling(window=20).mean())
    df["sma_50"] = group["close"].transform(lambda x: x.rolling(window=50).mean())
    df["sma_150"] = group["close"].transform(lambda x: x.rolling(window=150).mean())
    df["sma_200"] = group["close"].transform(lambda x: x.rolling(window=200).mean())
    df["vol_std_10d"] = group["close"].transform(lambda x: x.rolling(window=10).std())
    df["vol_std_50d"] = group["close"].transform(lambda x: x.rolling(window=50).std())
    df["high_52w"] = group["close"].transform(lambda x: x.rolling(window=250, min_periods=1).max())
    print("DB에 데이터 저장 중 (이 작업은 수 분이 소요될 수 있습니다)...")
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_analysis")
    df.to_sql("daily_analysis", conn, if_exists="append", index=False, chunksize=5000)
    conn.commit()
    conn.close()
    print("재계산 및 저장 완료!")


if __name__ == "__main__":
    recalc_all()
