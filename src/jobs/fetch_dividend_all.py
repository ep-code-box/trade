"""배당순위 API로 코드 보정·연간 DPS 합산 후 DB 반영. 실행: python -m src.jobs.fetch_dividend_all"""
import time

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_rank(market_gb, dividend_gb):
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d")
    # [최신 2년 타겟팅] 2023년부터 오늘까지의 모든 배당 기록 수집
    f_dt = "20230101"
    
    params = {
        "CTS_AREA": "", "GB1": market_gb, "UPJONG": "0001",
        "GB2": "0", "GB3": "2", "F_DT": f_dt, "T_DT": now, "GB4": dividend_gb,
    }
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True, delay=0.1)
    return (data.get("output") or []) if data else []


def run_dividend_sync():
    if not get_access_token():
        print("Token Error")
        return
    print("--- 배당 데이터 코드 보정 및 업데이트 시작 ---")
    all_raw_data = []
    for m in ["1", "3"]:
        for d in ["1", "2"]:
            data = fetch_dividend_rank(m, d)
            if data:
                all_raw_data.extend(data)
            time.sleep(0.1)

    summary = {}
    for item in all_raw_data:
        code = item.get("sht_cd", "").strip()
        # [보정] 배당 기준일(Base Date)을 키로 사용하여 중복 합산 방지
        base_dt = item.get("stck_dvdn_base_dt", "").strip()
        dps = int(item.get("per_sto_divi_amt", 0))
        
        if not code or not base_dt or dps <= 0:
            continue
            
        if code not in summary:
            summary[code] = {}
        
        # 동일한 기준일의 배당은 가장 큰 값 하나만 인정 (혹은 중복 제거)
        if base_dt not in summary[code]:
            summary[code][base_dt] = dps
        else:
            summary[code][base_dt] = max(summary[code][base_dt], dps)

    conn = get_connection()
    cur = conn.cursor()
    updated_count = 0
    
    for code, base_dates in summary.items():
        # [최종] 서로 다른 기준일의 배당금만 합산
        total_dps = sum(base_dates.values())
        
        cur.execute("UPDATE master_info SET per_stock_dvdn_amt = ? WHERE code = ?", (total_dps, code))
        # 최신 날짜의 daily_analysis에 배당 수익률 반영
        cur.execute("""
            UPDATE daily_analysis 
            SET dividend_yield = (CAST(? AS REAL) / close) * 100 
            WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)
        """, (total_dps, code, code))
        if cur.rowcount > 0:
            updated_count += 1
    conn.commit()
    conn.close()
    print(f"총 {updated_count}개 종목의 배당 정보가 DB에 정상 반영되었습니다.")


if __name__ == "__main__":
    run_dividend_sync()
