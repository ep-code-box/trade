"""특정 종목 SMA20·배당수익률 직접 계산 vs DB 검증. 실행: python -m src.scripts.check_sample_calculation"""
import pandas as pd
from src.db import get_connection


def verify_sample(code="005930"):
    conn = get_connection()
    df = conn.execute(
        "SELECT date, close, sma_20, dividend_yield FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 20",
        (code,),
    ).fetchall()
    if not df:
        print(f"[{code}] 데이터가 DB에 없습니다. 먼저 시세 수집이 필요합니다.")
        conn.close()
        return
    res_m = conn.execute("SELECT name, per_stock_dvdn_amt FROM master_info WHERE code = ?", (code,)).fetchone()
    conn.close()
    name = res_m[0] if res_m else ""
    dps = res_m[1] if res_m and res_m[1] else 0
    df = pd.DataFrame(df, columns=["date", "close", "sma_20", "dividend_yield"])
    print(f"=== [{name}({code})] 데이터 검증 리포트 ===")
    latest_close = df.iloc[0]["close"]
    stored_sma20 = df.iloc[0]["sma_20"]
    actual_sma20 = df["close"].mean()
    print(f"1. 이동평균선(SMA 20) 검증:")
    print(f"   - 직접 계산값: {actual_sma20:,.2f}")
    print(f"   - DB 저장값:   {stored_sma20:,.2f}")
    print(f"   - 일치 여부:   {'SUCCESS' if abs(actual_sma20 - stored_sma20) < 1 else 'FAIL'}")
    stored_yield = df.iloc[0]["dividend_yield"]
    calculated_yield = (dps / latest_close) * 100 if latest_close > 0 else 0
    print(f"\n2. 배당수익률 검증 (연간 DPS: {dps:,}원 기준):")
    print(f"   - 직접 계산값: {calculated_yield:.2f}%")
    print(f"   - DB 저장값:   {stored_yield:.2f}%")
    print(f"   - 일치 여부:   {'SUCCESS' if abs(calculated_yield - (stored_yield or 0)) < 0.1 else 'FAIL'}")


if __name__ == "__main__":
    verify_sample()
