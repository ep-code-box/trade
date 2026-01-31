"""sectors_themes(SECTOR_MASTER) 기준 업종별 배당순위 수집 → dividend_cycle/count. 실행: python -m src.jobs.tag_dividend_cycles_ultimate"""
import time
import pandas as pd

from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_history_by_sector(market_gb, upjong_code):
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    params = {
        "CTS_AREA": "", "GB1": market_gb, "UPJONG": upjong_code,
        "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": "0",
    }
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True, delay=0.05)
    return (data.get("output") or []) if data else []


def run_ultimate_tagging():
    if not get_access_token():
        print("Token Error")
        return
    conn = get_connection()
    sectors = pd.read_sql_query("SELECT DISTINCT code FROM sectors_themes WHERE category_type='SECTOR_MASTER'", conn)
    conn.close()
    print(f"--- [Ultimate] {len(sectors)}개 전 업종 순회 배당 마이닝 시작 ---")
    global_counter = {}
    total_found = 0
    for idx, row in sectors.iterrows():
        s_code = row["code"]
        m_gb = "1" if str(s_code).startswith("0") else "3"
        print(f"[{idx+1}/{len(sectors)}] 업종 {s_code} 마이닝 중 (발견: {total_found})", end="\r")
        data = fetch_dividend_history_by_sector(m_gb, s_code)
        if data:
            for item in data:
                code = item.get("sht_cd", "").strip()
                if not code:
                    continue
                global_counter[code] = global_counter.get(code, 0) + 1
                total_found += 1
        time.sleep(0.05)
    if not global_counter:
        print("\n데이터 발견 실패.")
        return
    conn = get_connection()
    cur = conn.cursor()
    updated_count = 0
    for code, count in global_counter.items():
        final_count = min(count, 12)
        cycle = "분기/월" if final_count >= 4 else "반기배당" if final_count >= 2 else "연배당"
        cur.execute("UPDATE master_info SET dividend_cycle = ?, dividend_count = ? WHERE code = ?", (cycle, final_count, code))
        if cur.rowcount > 0:
            updated_count += 1
    conn.commit()
    conn.close()
    print(f"\n최종 완료: {updated_count}개 종목의 배당 주기 태깅 성공!")


if __name__ == "__main__":
    run_ultimate_tagging()
