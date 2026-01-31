"""특정 종목(SK텔레콤) 배당 기록 조회·DPS 합산·DB dividend_yield 업데이트. 실행: python -m src.scripts.test_dividend_sample"""
from src.auth import get_access_token
from src.db import get_connection
from src.kis_api import kis_get_raw


def fetch_dividend_history(code):
    path = "/uapi/domestic-stock/v1/ranking/dividend-rate"
    params = {"CTS_AREA": "", "GB1": "0", "UPJONG": "0001", "GB2": "0", "GB3": "2", "F_DT": "20240101", "T_DT": "20241231", "GB4": "0"}
    data = kis_get_raw(path, params=params, tr_id="HHKDB13470100", use_real=True)
    if not data:
        return []
    output = data.get("output", [])
    return [item for item in output if item.get("sht_cd") == code]


def run_sample_test():
    code = "017670"
    print(f"--- {code} (SK텔레콤) 배당 샘플 테스트 시작 ---")
    if not get_access_token():
        print("Token Error")
        return
    history = fetch_dividend_history(code)
    if not history:
        print("배당 기록을 찾을 수 없습니다. (순위권 밖이거나 API 제한)")
        return
    total_dps = 0
    count = 0
    kinds = []
    for item in history:
        total_dps += int(item.get("per_sto_divi_amt", 0))
        count += 1
        kinds.append(item.get("divi_kind", ""))
    print(f"최근 1년 배당 횟수: {count}회 ({', '.join(set(kinds))})")
    print(f"최근 1년 총 배당금(DPS): {total_dps:,}원")
    conn = get_connection()
    res = conn.execute("SELECT close FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 1", (code,)).fetchone()
    current_price = res[0] if res else 0
    conn.close()
    if current_price > 0:
        real_yield = (total_dps / current_price) * 100
        print(f"현재 주가: {current_price:,}원")
        print(f"실시간 연환산 배당수익률: {real_yield:.2f}%")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE daily_analysis SET dividend_yield = ? WHERE code = ? AND date = (SELECT MAX(date) FROM daily_analysis WHERE code = ?)",
            (real_yield, code, code),
        )
        conn.commit()
        conn.close()
        print("DB 업데이트 완료.")


if __name__ == "__main__":
    run_sample_test()
