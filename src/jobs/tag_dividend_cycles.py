"""배당순위 API(코스피/코스닥·결산/중간) → 빈도 카운트 → dividend_cycle/count. 실행: python -m src.jobs.tag_dividend_cycles"""
import time

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_records(market_gb, dividend_gb):
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    params = {
        "CTS_AREA": "", "GB1": market_gb, "UPJONG": "0001",
        "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": dividend_gb,
    }
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True, delay=0.1)
    return (data.get("output") or []) if data else []


def run_tagging():
    if not get_access_token():
        print("Token Error")
        return
    print("--- [TrendHunter] 배당 주기(월/분기/연) 분석 및 태깅 시작 ---")
    all_records = []
    for m in ["1", "3"]:
        for d in ["1", "2"]:
            print(f"시장 {m} 배당구분 {d} 데이터 수집 중...", end="\r")
            data = fetch_dividend_records(m, d)
            if data:
                all_records.extend(data)
            time.sleep(0.1)
    if not all_records:
        print("\n분석할 배당 데이터가 없습니다.")
        return
    counter = {}
    for item in all_records:
        code = item.get("sht_cd", "").strip()
        if not code:
            continue
        counter[code] = counter.get(code, 0) + 1
    conn = get_connection()
    cur = conn.cursor()
    tagged_count = 0
    for code, count in counter.items():
        cycle = "월배당" if count >= 10 else "분기배당" if count >= 4 else "반기배당" if count >= 2 else "연배당"
        cur.execute("UPDATE master_info SET dividend_cycle = ?, dividend_count = ? WHERE code = ?", (cycle, count, code))
        if cur.rowcount > 0:
            tagged_count += 1
    conn.commit()
    conn.close()
    print(f"\n태깅 완료: 총 {tagged_count}개 종목의 배당 주기가 분석되었습니다.")


if __name__ == "__main__":
    run_tagging()
