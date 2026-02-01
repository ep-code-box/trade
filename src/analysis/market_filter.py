"""시장의 온도계를 체크합니다. (DB 기반 KOSPI/KOSDAQ 50/200일 이평선 필터)"""
import pandas as pd
from src.db import get_connection

def check_market_health():
    """
    DB에 저장된 지수 데이터를 기반으로 시장 상태 진단.
    0001: KOSPI, 1001: KOSDAQ
    """
    conn = get_connection()
    results = []
    
    for code, name in [("0001", "KOSPI"), ("1001", "KOSDAQ")]:
        # 최근 데이터 조회 (정렬 중요)
        query = "SELECT date, close, sma_50, sma_200 FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 1"
        df = pd.read_sql_query(query, conn, params=(code,))
        
        if df.empty:
            results.append({
                "name": name,
                "status": "UNKNOWN",
                "reason": "DB 데이터 없음",
                "curr": 0,
                "sma200": 0
            })
            continue
            
        row = df.iloc[0]
        curr = row["close"]
        sma200 = row["sma_200"]
        sma50 = row["sma_50"]
        
        # 200일선 데이터가 아직 계산 안 됐을 경우 (데이터 부족 시)
        if pd.isna(sma200):
            # 대안: 50일선이라도 있으면 그것으로 판단 (중기 추세)
            if pd.notna(sma50):
                is_safe = curr > sma50
                status = "GREEN" if is_safe else "RED"
                threshold_msg = "50일선"
                threshold_val = sma50
            else:
                status = "UNKNOWN"
                threshold_msg = "데이터 부족"
                threshold_val = 0
        else:
            # 정석: 200일선 기준
            is_safe = curr > sma200
            status = "GREEN" if is_safe else "RED"
            threshold_msg = "200일선"
            threshold_val = sma200
            
        results.append({
            "name": name,
            "status": status,
            "curr": curr,
            "sma200": threshold_val,
            "msg": threshold_msg
        })
        
    conn.close()
    return results

if __name__ == "__main__":
    health = check_market_health()
    for h in health:
        print(f"[{h['name']}] 현재가: {h['curr']:,.2f} | 기준선({h['msg']}): {h['sma200']:,.2f} | 상태: {h['status']}")
