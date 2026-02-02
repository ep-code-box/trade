#!/usr/bin/env python3
"""
리팩토링된 진입점: 공통 모듈(src) 사용.
사용법: python run.py <명령>
명령 없이 실행 시 사용 가능한 명령 목록 출력.
"""
import sys
import warnings

# Suppress annoying SSL warnings on macOS/LibreSSL
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

COMMANDS = {
    "init": "DB 테이블 생성 → python -m src.db.manager",
    "views": "Track1/Track2 뷰 생성 → python -m src.scripts.setup_views",
    "sync": "마스터 동기화(KOSPI/KOSDAQ) → python -m src.jobs.db_sync",
    "themes": "테마/업종 동기화 → python -m src.jobs.db_sync_themes",
    "daily": "일봉 수집 → python -m src.jobs.fetch_daily_price",
    "fundamentals": "펀더멘털 수집 → python -m src.jobs.fetch_stock_fundamentals",
    "dividend": "배당 DPS(실전) → python -m src.jobs.fetch_dividend_info_final",
    "dividend-all": "배당 순위 일괄 → python -m src.jobs.fetch_dividend_all",
    "dividend-rank": "고배당 순위 → python -m src.jobs.fetch_high_dividend_rank",
    "mine": "업종별 배당 마이닝 → python -m src.jobs.mine_dividend_data",
    "mine-sweep": "전 종목 배당 전수 → python -m src.jobs.mine_dividend_full_sweep",
    "tag": "배당 주기 태깅 → python -m src.jobs.tag_dividend_cycles",
    "tag-full": "예탁원 배당일정 태깅 → python -m src.jobs.tag_dividend_cycles_full",
    "tag-ultimate": "업종별 배당 태깅 → python -m src.jobs.tag_dividend_cycles_ultimate",
    "rs": "RS 점수 계산 → python -m src.analysis.calc_rs_score",
    "supply": "수급 데이터 수집 → python -m src.jobs.fetch_supply_history",
    "recalc": "지표 전량 재계산 → python -m src.analysis.recalc_indicators",
    "screen": "Track1/Track2 리포트 → python -m src.analysis.screen_market",
    "compare": "배당 소스 비교 → python -m src.scripts.compare_dividend_sources",
    "check": "샘플 검증 → python -m src.scripts.check_sample_calculation",
    "debug": "API 디버그 → python -m src.scripts.debug_api",
    "test-div": "배당 샘플 테스트 → python -m src.scripts.test_dividend_sample",
}


def main():
    if len(sys.argv) < 2:
        print("사용법: python run.py <명령>")
        print("\n가능한 명령:")
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd:16} {desc}")
        return 0
    cmd = sys.argv[1].lower()
    if cmd not in COMMANDS:
        print(f"알 수 없는 명령: {cmd}")
        print("가능한 명령:", ", ".join(COMMANDS))
        return 1
    # 실제 실행은 해당 모듈의 main/run 함수 호출
    runners = {
        "init": ("src.db.manager", "init_dbs"),
        "views": ("src.scripts.setup_views", "create_views"),
        "sync": ("src.jobs.db_sync", None),
        "themes": ("src.jobs.db_sync_themes", None),
        "daily": ("src.jobs.fetch_daily_price", "main"),
        "fundamentals": ("src.jobs.fetch_stock_fundamentals", "main"),
        "dividend": ("src.jobs.fetch_dividend_info_final", "main"),
        "dividend-all": ("src.jobs.fetch_dividend_all", "run_dividend_sync"),
        "dividend-rank": ("src.jobs.fetch_high_dividend_rank", "main"),
        "mine": ("src.jobs.mine_dividend_data", "run_mining"),
        "mine-sweep": ("src.jobs.mine_dividend_full_sweep", "main"),
        "tag": ("src.jobs.tag_dividend_cycles", "run_tagging"),
        "tag-full": ("src.jobs.tag_dividend_cycles_full", "run_full_tagging"),
        "tag-ultimate": ("src.jobs.tag_dividend_cycles_ultimate", "run_ultimate_tagging"),
        "rs": ("src.analysis.calc_rs_score", "calc_rs_scores_flexible"),
        "supply": ("src.jobs.fetch_supply_history", "main"),
        "recalc": ("src.analysis.recalc_indicators", "recalc_all"),
        "screen": ("src.analysis.screen_market", "generate_full_report"),
        "compare": ("src.scripts.compare_dividend_sources", "main"),
        "check": ("src.scripts.check_sample_calculation", "verify_sample"),
        "debug": ("src.scripts.debug_api", "debug_check"),
        "test-div": ("src.scripts.test_dividend_sample", "run_sample_test"),
    }
    mod_name, fn_name = runners[cmd]
    import importlib
    mod = importlib.import_module(mod_name)
    if fn_name is None:
        # __main__ 블록 실행 (db_sync, db_sync_themes)
        import runpy
        runpy.run_path(mod.__file__, run_name="__main__")
    else:
        getattr(mod, fn_name)()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
