#!/usr/bin/env python3
"""
[TrendHunter Genesis] 시스템 완전 초기화 및 전수 데이터 수집.
이 스크립트 실행 후 즉시 매매가 가능한 상태가 됩니다.
"""
import os
import sys
import asyncio
import time
from src.db.manager import init_db
from src.jobs.db_sync import main as sync_master
from src.jobs.db_sync_themes import main as sync_themes
from src.jobs.fetch_daily_price import main as fetch_price
from src.jobs.fetch_supply_history import main as fetch_supply
from src.jobs.mine_dividend_data import main as mine_dividend
from src.jobs.fetch_stock_fundamentals import main as fetch_fundamentals
from src.analysis.recalc_indicators import recalc_all
from src.analysis.calc_rs_score import calc_rs_scores_flexible

def run_step(name, func):
    print(f"\n>>> [INIT STEP] {name} 실행 중...")
    start = time.time()
    try:
        func()
        print(f"    ✅ {name} 완료 ({time.time()-start:.1f}초)")
    except Exception as e:
        print(f"    🚨 {name} 실패: {e}")
        sys.exit(1)

def main():
    print("=" * 60)
    print(" [TrendHunter] 시스템 제네시스 프로토콜 가동")
    print("=" * 60)

    # 1. 인프라 구축
    run_step("DB 스키마 생성", init_db)
    run_step("종목 마스터 동기화", sync_master)
    run_step("테마/업종 동기화", sync_themes)

    # 2. 광속 데이터 적재 (30 TPS 엔진 사용)
    print("\n[주의] 대량의 데이터를 수집합니다. 약 10~15분 소요됩니다.")
    run_step("전 종목 시세 수집 (1년치)", fetch_price)
    run_step("전 종목 수급 수집 (1개월치)", fetch_supply)
    run_step("전 종목 배당 마이닝", mine_dividend)
    run_step("전 종목 펀더멘털 수집", fetch_fundamentals)

    # 3. 분석 데이터 생성
    run_step("전수 지표 재계산 (SMA/VCP/신고가)", recalc_all)
    run_step("RS Score 상대강도 산출", calc_rs_scores_flexible)

    print("\n" + "=" * 60)
    print(" [초기화 성공] 이제 모든 데이터가 준비되었습니다.")
    print(" 내일부터는 'python3 run_daily.py'만 실행하십시오.")
    print("=" * 60)

if __name__ == "__main__":
    main()
