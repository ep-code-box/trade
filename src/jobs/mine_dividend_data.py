"""업종별 배당순위 수집 후 DPS·주기·count DB 업데이트. 실행: python -m src.jobs.mine_dividend_data"""
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_by_sector(market_gb, sector_code):
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d")
    # 작년 1월 1일부터 오늘까지
    f_dt = str(int(now[:4]) - 1) + "0101"
    
    params = {
        "CTS_AREA": "", "GB1": market_gb, "UPJONG": sector_code,
        "GB2": "0", "GB3": "2", "F_DT": f_dt, "T_DT": now, "GB4": "0",
    }
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True, delay=0.05)
    return (data.get("output") or []) if data else []


def run_mining():
    if not get_access_token():
        print("Token Error")
        return
    print("--- [TrendHunter] 전 종목 배당 마이닝 및 주기 분석 시작 ---")
    sectors = [
        ("1", "0001"), ("1", "0002"), ("1", "0005"), ("1", "0006"), ("1", "0012"), ("1", "0027"),
        ("3", "1001"), ("3", "1002"), ("3", "1012"), ("3", "1030"), ("3", "1041"),
    ]
    all_data = []
    for m, s in sectors:
        print(f"업종 {s} 수집 중...", end="\r")
        data = fetch_dividend_by_sector(m, s)
        all_data.extend(data)
    if not all_data:
        print("수집된 데이터가 없습니다.")
        return
    summary = {}
    for item in all_data:
        code = item.get("sht_cd", "").strip()
        dps = int(item.get("per_sto_divi_amt", 0))
        if not code:
            continue
        if code not in summary:
            summary[code] = {"dps_list": [], "total_dps": 0}
        summary[code]["dps_list"].append(dps)
        summary[code]["total_dps"] += dps
    conn = get_connection()
    cur = conn.cursor()
    updated = 0
    for code, info in summary.items():
        count = len(info["dps_list"])
        total_dps = info["total_dps"]
        cycle = "월배당" if count >= 10 else "분기배당" if count >= 4 else "반기배당" if count >= 2 else "연배당"
        cur.execute(
            "UPDATE master_info SET per_stock_dvdn_amt = ?, dividend_cycle = ?, dividend_count = ? WHERE code = ?",
            (total_dps, cycle, count, code),
        )
        cur.execute(
            "UPDATE daily_analysis SET dividend_yield = (CAST(? AS REAL) / close) * 100 WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)",
            (total_dps, code, code),
        )
        if cur.rowcount > 0:
            updated += 1
    conn.commit()
    conn.close()
    print(f"\n마이닝 완료: 총 {updated}개 종목의 배당 주기 및 수익률 데이터가 정밀 업데이트되었습니다.")


if __name__ == "__main__":
    run_mining()
