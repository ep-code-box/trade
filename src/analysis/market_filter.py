"""시장의 온도계를 체크합니다. (DB 기반 KOSPI/KOSDAQ 50/200일 이평선 필터 및 기울기 분석)"""
import pandas as pd
from src.db import get_connection

def check_market_health():
    """
    DB에 저장된 지수 데이터를 기반으로 시장 상태 진단.
    200일선의 위치뿐만 아니라 '기울기(상승세)'를 함께 판단합니다.
    """
    conn = get_connection()
    results = []
    
    for code, name in [("0001", "KOSPI"), ("1001", "KOSDAQ")]:
        # 최근 21거래일 데이터 조회 (기울기 계산용)
        query = "SELECT date, close, sma_50, sma_200 FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 21"
        df = pd.read_sql_query(query, conn, params=(code,))
        
        if df.empty or len(df) < 1:
            results.append({"name": name, "status": "UNKNOWN", "curr": 0, "sma200": 0, "msg": "데이터 없음"})
            continue
            
        latest = df.iloc[0]
        curr = latest["close"]
        sma200_curr = latest["sma_200"]
        
        # 1개월(20거래일) 전 200일선 값
        sma200_prev = df.iloc[-1]["sma_200"] if len(df) >= 21 else None
        
        status = "RED"
        msg = "하락추세"
        
        if pd.notna(sma200_curr) and pd.notna(sma200_prev):
            # 거장의 조건: 가격 > 200일선 AND 200일선이 상승 중
            is_above = curr > sma200_curr
            is_trending_up = sma200_curr > sma200_prev
            
            if is_above and is_trending_up:
                status = "GREEN"
                msg = "상승확정"
            elif is_above:
                status = "YELLOW"
                msg = "선 위 정체"
            else:
                status = "RED"
                msg = "선 아래(위험)"
        else:
            status = "UNKNOWN"
            msg = "지표부족"
            
        results.append({
            "name": name,
            "status": status,
            "curr": curr,
            "sma200": sma200_curr or 0,
            "msg": msg
        })
        
    conn.close()
    return results

if __name__ == "__main__":
    health = check_market_health()
    for h in health:
        print(f"[{h['name']}] 현재가: {h['curr']:,.2f} | 상태: {h['status']} ({h['msg']})")
