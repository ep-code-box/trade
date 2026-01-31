"""전 종목, 전 기간 지표 전수 재계산 (SMA, VCP, Vol_SMA)."""
import sqlite3
import pandas as pd
import numpy as np
from src.db import get_connection

def recalc_all():
    conn = get_connection()
    print("DB에서 전체 시세 데이터를 불러오는 중... (이 작업은 양이 많아 시간이 걸립니다)")
    
    # 전체 데이터를 불러옴 (date 순 정렬 필수)
    df = pd.read_sql_query("SELECT * FROM daily_analysis ORDER BY code, date", conn)
    
    if df.empty:
        print("데이터가 없습니다.")
        conn.close()
        return

    print(f"총 {len(df):,}행 데이터 처리 시작...")
    
    # 종목별 그룹화
    group = df.groupby('code')
    
    # 1. 이동평균선 전수 계산
    print("이동평균선(SMA 20, 50, 150, 200) 계산 중...")
    df['sma_20'] = group['close'].transform(lambda x: x.rolling(window=20).mean())
    df['sma_50'] = group['close'].transform(lambda x: x.rolling(window=50).mean())
    df['sma_150'] = group['close'].transform(lambda x: x.rolling(window=150).mean())
    df['sma_200'] = group['close'].transform(lambda x: x.rolling(window=200).mean())
    
    # 2. 거래량 평균 및 변동성 계산
    print("거래량 SMA 및 변동성(VCP) 지표 계산 중...")
    df['volume_sma_50'] = group['volume'].transform(lambda x: x.rolling(window=50).mean())
    df['vol_std_10d'] = group['close'].transform(lambda x: x.rolling(window=10).std())
    df['vol_std_50d'] = group['close'].transform(lambda x: x.rolling(window=50).std())
    
    # 3. 신고가/신저가 (전체 히스토리 기반)
    print("52주 신고가/신저가 계산 중...")
    df['high_52w'] = group['close'].transform(lambda x: x.rolling(window=250, min_periods=1).max())
    df['low_52w'] = group['close'].transform(lambda x: x.rolling(window=250, min_periods=1).min())

    # 4. DB 덮어쓰기 (전체 삭제 후 재생성)
    print("DB에 무결점 데이터 저장 중 (수 분이 소요될 수 있습니다)...")
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM daily_analysis")
        # 컬럼 순서 맞추기
        df.to_sql('daily_analysis', conn, if_exists='append', index=False, chunksize=5000)
        conn.commit()
        print("모든 지표의 전수 재계산 및 저장이 완료되었습니다.")
    except Exception as e:
        print(f"저장 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    recalc_all_history()