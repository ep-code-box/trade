#!/usr/bin/env python3
"""
[TrendHunter Daily v2.0] 매일의 완벽한 데이터 동기화 루틴.
시세 -> 수급 -> 펀더멘털(ROE) -> 배당마이닝 -> 지표갱신 -> 리포트.
"""
import time
from src.jobs.fetch_daily_price import main as fetch_price
from src.jobs.fetch_supply_history import main as fetch_supply
from src.jobs.fetch_stock_fundamentals import main as fetch_fundamentals
from src.jobs.mine_dividend_data import main as mine_dividend
from src.analysis.recalc_indicators import recalc_all
from src.analysis.calc_rs_score import calc_rs_scores_flexible
from src.analysis.screen_market import generate_full_report

def main():
    print("=" * 70)
    print(f" [TrendHunter] 일일 통합 데이터 분석 파이프라인 가동")
    print("=" * 70)

    # 파이프라인 단계 정의
    steps = [
        ("1. 오늘의 시세 업데이트", fetch_price),
        ("2. 오늘의 수급 업데이트", fetch_supply),
        ("3. 펀더멘털(ROE) 최신화", fetch_fundamentals),
        ("4. 배당 데이터 정밀 마이닝", mine_dividend),
        ("5. 전수 기술적 지표 재계산", recalc_all),
        ("6. RS 상대강도 랭킹 업데이트", calc_rs_scores_flexible),
    ]

    for name, func in steps:
        print(f"\n[진행] {name}...")
        start = time.time()
        try:
            func()
            print(f"   ✅ 완료 ({time.time()-start:.1f}초)")
        except Exception as e:
            print(f"   🚨 실패: {e}")

    print("\n" + "=" * 70)
    print(" [작전 결과 보고서]")
    print("=" * 70)
    try:
        generate_full_report()
    except Exception as e:
        print(f"   🚨 리포트 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
