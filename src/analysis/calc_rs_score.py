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

    def get_rs_raw_score_flexible(series):
        if len(series) < 60: return -999.0
        curr = series.iloc[-1]
        count = len(series)
        
        # [v9.5] 데이터 기간별 존재 여부 확인 후 동적 비중 적용
        score = 0
        total_weight = 0
        
        # 3개월 (필수)
        m3 = max(0, count - 63)
        score += ((curr / series.iloc[m3]) - 1) * 2
        total_weight += 2
        
        # 6개월
        if count >= 126:
            m6 = count - 126
            score += (curr / series.iloc[m6]) - 1
            total_weight += 1
            
        # 9개월
        if count >= 189:
            m9 = count - 189
            score += (curr / series.iloc[m9]) - 1
            total_weight += 1
            
        # 12개월
        if count >= 252:
            m12 = count - 252
            score += (curr / series.iloc[m12]) - 1
            total_weight += 1
            
        # 비중 정규화 (가중치 합계가 5가 되도록 보정)
        return score * (5.0 / total_weight)

    rs_results = []
    for code, group in df.groupby("code"):
        score = get_rs_raw_score_flexible(group["close"])
        rs_results.append({"code": code, "raw_score": score})
    rs_df = pd.DataFrame(rs_results)
    valid_rs = rs_df[rs_df["raw_score"] > -900].copy()
    valid_rs["rs_score"] = valid_rs["raw_score"].rank(pct=True) * 99
    print(f"계산된 RS 점수(유효) 개수: {len(valid_rs)}")
    if len(valid_rs) == 0:
        print("RS 점수 계산 실패: 유효한 데이터가 없습니다.")
        return

    cur = conn.cursor()
    cur.execute("SELECT MAX(date) FROM daily_analysis")
    max_date = cur.fetchone()[0]

    print(f"DB에 RS 점수 업데이트 중... (기준일: {max_date})")
    
    updated_count = 0
    for _, row in valid_rs.iterrows():
        cur.execute("UPDATE daily_analysis SET rs_score = ? WHERE code = ? AND date = ?", (row["rs_score"], row["code"], max_date))
        updated_count += cur.rowcount
        
    conn.commit()
    conn.close()
    print(f"RS 점수 재계산 및 업데이트 완료 (총 {updated_count}건 업데이트됨)")


if __name__ == "__main__":
    calc_rs_scores_flexible()
