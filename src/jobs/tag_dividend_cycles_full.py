"""예탁원 배당일정 API(기간별) → 전수 이벤트 카운트 → dividend_cycle/count. 실행: python -m src.jobs.tag_dividend_cycles_full"""
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_schedule(start_date, end_date):
    path = "/uapi/domestic-stock/v1/ksdinfo/dividend"
    params = {"F_DT": start_date, "T_DT": end_date, "CTS_AREA": ""}
    data = kis_get_raw(path, params=params, tr_id="HHKDB669102C0", use_real=True, delay=0.1)
    return (data.get("output") or []) if data else []


def run_full_tagging():
    if not get_access_token():
        print("Token Error")
        return
    print("--- [TrendHunter] 전 종목 배당 주기 전수 마이닝 시작 ---")
    periods = [
        ("20240101", "20240331"), ("20240401", "20240630"),
        ("20240701", "20240930"), ("20241001", "20241231"),
    ]
    all_events = []
    for start, end in periods:
        print(f"기간 {start} ~ {end} 데이터 수집 중...", end="\r")
        data = fetch_dividend_schedule(start, end)
        if data:
            all_events.extend(data)
    if not all_events:
        print("\n데이터를 가져오지 못했습니다. (권한 또는 기간 오류)")
        return
    counter = {}
    for ev in all_events:
        code = ev.get("sht_cd", "").strip()
        if not code:
            continue
        counter[code] = counter.get(code, 0) + 1
    conn = get_connection()
    cur = conn.cursor()
    tagged = 0
    for code, count in counter.items():
        cycle = "월배당" if count >= 10 else "분기배당" if count >= 4 else "반기배당" if count >= 2 else "연배당"
        cur.execute("UPDATE master_info SET dividend_cycle = ?, dividend_count = ? WHERE code = ?", (cycle, count, code))
        if cur.rowcount > 0:
            tagged += 1
    conn.commit()
    conn.close()
    print(f"\n전수 태깅 완료: 총 {tagged}개 종목의 배당 주기가 DB에 영구 저장되었습니다.")


if __name__ == "__main__":
    run_full_tagging()
