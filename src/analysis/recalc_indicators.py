"""지표 전수 재계산 (데이터 무결성 보존 버전)."""
import pandas as pd
import numpy as np
from src.db import get_connection

def recalc_all():
    conn = get_connection()
    print("DB에서 전체 시세 데이터를 불러오는 중 (모든 컬럼 보존)...")
    # 모든 컬럼(*)을 가져와야 함 (수급 데이터 유실 방지)
    df = pd.read_sql_query("SELECT * FROM daily_analysis ORDER BY code, date", conn)
    
    if df.empty:
        print("데이터가 없습니다."); conn.close(); return

    print(f"총 {len(df):,}행 처리 시작...")
    group = df.groupby('code')
    
    # 1. 이동평균선 (SMA)
    df['sma_20'] = group['close'].transform(lambda x: x.rolling(window=20).mean())
    df['sma_50'] = group['close'].transform(lambda x: x.rolling(window=50).mean())
    df['sma_150'] = group['close'].transform(lambda x: x.rolling(window=150).mean())
    df['sma_200'] = group['close'].transform(lambda x: x.rolling(window=200).mean())
    
    # 2. 거래량 및 변동성
    df['volume_sma_50'] = group['volume'].transform(lambda x: x.rolling(window=50).mean())
    df['vol_std_10d'] = group['close'].transform(lambda x: x.rolling(window=10).std())
    df['vol_std_50d'] = group['close'].transform(lambda x: x.rolling(window=50).std())
    
    # 3. 52주 신고가 (High 우선, 없으면 Close)
    # df['high']와 df['low']가 0인 경우를 방지하기 위해 fillna 처리
    high_ref = df['high'].replace(0, np.nan).fillna(df['close'])
    low_ref = df['low'].replace(0, np.nan).fillna(df['close'])
    df['high_52w'] = high_ref.groupby(df['code']).transform(lambda x: x.rolling(window=250, min_periods=1).max())
    df['low_52w'] = low_ref.groupby(df['code']).transform(lambda x: x.rolling(window=250, min_periods=1).min())

    # 4. DB 업데이트 (트랜잭션 보장)
    print("DB에 무결점 데이터 덮어쓰기 중...")
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM daily_analysis")
        # 모든 컬럼이 포함된 df를 그대로 저장하여 수급 데이터 보존
        df.to_sql('daily_analysis', conn, if_exists='append', index=False, chunksize=5000)
        conn.commit()
        print("모든 지표 재계산 및 보존 완료.")
    except Exception as e:
        print(f"🚨 저장 오류: {e}"); conn.rollback()
    finally: conn.close()

if __name__ == "__main__": recalc_all()
