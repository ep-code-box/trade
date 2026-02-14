"""RS 점수 계산 후 daily_analysis 최신일만 업데이트. 실행: python -m src.analysis.calc_rs_score"""
import pandas as pd
import numpy as np

from src.db import get_connection


def calc_rs_scores_flexible():
    conn = get_connection()
    print("DB에서 시세 데이터를 불러오는 중 (유연한 RS 계산)...")
    df = pd.read_sql_query("SELECT date, code, close FROM daily_analysis ORDER BY code, date", conn)
    if df.empty:
        conn.close()
        return

def calc_rs_scores_flexible():
    conn = get_connection()
    print("DB에서 시세 데이터를 불러오는 중 (RS 정화 로직 가동)...")
    
    # [v13.0] 거래대금이 어느정도 되는 종목들만 RS 경쟁에 참여시킴 (잡초 제거)
    # [v13.1] 지수(0001, 1001)는 거래대금에 상관없이 무조건 포함
    # [v13.2] 지수만 업데이트된 경우를 대비해, 100개 이상의 종목이 있는 최신 날짜를 찾음
    query_max_date = """
        SELECT date FROM daily_analysis 
        GROUP BY date HAVING COUNT(*) > 100 
        ORDER BY date DESC LIMIT 1
    """
    cur = conn.cursor()
    cur.execute(query_max_date)
    res_date = cur.fetchone()
    if not res_date:
        print("RS 계산을 수행할 충분한 데이터가 없습니다.")
        conn.close()
        return
    max_date = res_date[0]

    query = f"""
        SELECT date, code, close, amount 
        FROM daily_analysis 
        WHERE date = '{max_date}'
          AND (amount >= 1000000000 OR code IN ('0001', '1001') OR code IN (SELECT symbol FROM account_positions_audit WHERE qty > 0))
    """
    valid_codes_df = pd.read_sql_query(query, conn)
    valid_codes = valid_codes_df['code'].tolist()
    
    # 전체 시세 데이터 로드
    df = pd.read_sql_query("SELECT date, code, close FROM daily_analysis ORDER BY code, date", conn)
    if df.empty:
        conn.close()
        return

    def get_rs_raw_score_master(series):
        if len(series) < 21: return -999.0, -999.0
        curr = series.iloc[-1]
        count = len(series)
        
        # 1. 정통 RS (IBD Style)
        # RS = [(3m*2) + 6m + 9m + 12m] / 5 (Price Ratio 기반)
        m3 = max(0, count - 63); m6 = max(0, count - 126); m9 = max(0, count - 189); m12 = max(0, count - 252)
        score_trad = ((curr / series.iloc[m3]) * 2) + (curr / series.iloc[m6]) + (curr / series.iloc[m9]) + (curr / series.iloc[m12])
        
        # 2. 마스터 RS (Sniper Style)
        # RS_Master = [(1m*4) + (3m*2) + 6m] / 7 (Price Ratio 기반)
        m1 = max(0, count - 21)
        score_mast = ((curr / series.iloc[m1]) * 4) + ((curr / series.iloc[m3]) * 2) + (curr / series.iloc[m6])

        return score_trad / 5.0, score_mast / 7.0

    rs_results = []
    for code, group in df.groupby("code"):
        # 거래대금 미달 종목은 계산은 하되 랭킹 경쟁에서 불이익
        trad, mast = get_rs_raw_score_master(group["close"])
        if code in valid_codes:
            rs_results.append({"code": code, "raw_trad": trad, "raw_mast": mast, "is_valid": True})
        else:
            rs_results.append({"code": code, "raw_trad": trad, "raw_mast": mast, "is_valid": False})
    
    rs_df = pd.DataFrame(rs_results)
    
    # [핵심] 우량 종목(is_valid=True)들끼리만 먼저 랭킹을 매김
    valid_rs = rs_df[rs_df["is_valid"] == True].copy()
    valid_rs["rs_score"] = valid_rs["raw_trad"].rank(pct=True) * 99
    valid_rs["rs_score_master"] = valid_rs["raw_mast"].rank(pct=True) * 99
    
    print(f"계산 완료 - 우량 주도주 {len(valid_rs)}건 정밀 랭킹 산정")

    print(f"DB에 정제된 RS 점수 업데이트 중... (기준일: {max_date})")
    
    # 나머지 종목은 0점 처리하고 우량주만 업데이트
    cur = conn.cursor()
    cur.execute("UPDATE daily_analysis SET rs_score = 0, rs_score_master = 0 WHERE date = ?", (max_date,))
    
    updated_count = 0
    for _, row in valid_rs.iterrows():
        cur.execute("UPDATE daily_analysis SET rs_score = ?, rs_score_master = ? WHERE code = ? AND date = ?", 
                    (row["rs_score"], row["rs_score_master"], row["code"], max_date))
        updated_count += cur.rowcount
        
    conn.commit()
    conn.close()
    print(f"RS 점수 재계산 및 업데이트 완료 (총 {updated_count}건 업데이트됨)")


if __name__ == "__main__":
    calc_rs_scores_flexible()
