#!/Users/lastep/Code/trade/venv/bin/python3
"""
[TrendHunter Daily v2.0] 매일의 완벽한 데이터 동기화 루틴.
시세 -> 수급 -> 펀더멘털(ROE) -> 배당마이닝 -> 지표갱신 -> 리포트.
"""
import time
from src.jobs.fetch_daily_price import main as fetch_price
from src.jobs.fetch_supply_history import main as fetch_supply
from src.jobs.fetch_stock_fundamentals import main as fetch_fundamentals
from src.jobs.mine_dividend_data import main as mine_dividend
from src.jobs.force_sync_index import sync_index as fetch_index_full # 지수 전용 추가
from src.analysis.recalc_indicators import recalc_all
from src.analysis.calc_rs_score import calc_rs_scores_flexible
from src.analysis.screen_market import generate_full_report

def cleanse_today():
    from datetime import datetime, timedelta
    from src.db import get_connection
    now = datetime.now()
    target_date = now.strftime("%Y%m%d") if now.hour >= 18 else (now - timedelta(days=1)).strftime("%Y%m%d")
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_analysis WHERE date = ?", (target_date,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        print(f"   🧹 클렌징 완료: {target_date} 데이터 {deleted}건 삭제")

def main():
    print("=" * 70)
    print(f" [TrendHunter] 일일 통합 데이터 분석 파이프라인 가동")
    print("=" * 70)

    # 0단계: 클렌징 작업 추가
    print("\n[진행] 0. 데이터 클렌징 (무결성 보장)...")
    cleanse_today()

    # 파이프라인 단계 정의
    steps = [
        ("1. 지수 데이터 무결성 확보", fetch_index_full),
        ("2. 오늘의 시세 업데이트", fetch_price),
        ("3. 오늘의 수급 업데이트", fetch_supply),
        ("4. 펀더멘털(ROE) 최신화", fetch_fundamentals),
        ("5. 배당 데이터 정밀 마이닝", mine_dividend),
        ("6. 전수 기술적 지표 재계산", recalc_all),
        ("7. RS 상대강도 랭킹 업데이트", calc_rs_scores_flexible),
    ]

    from src.utils.notifier import notifier
    
    tg_start_msg = "⚙️ <b>[TrendHunter] 일일 데이터 파이프라인 가동 시작</b>"
    notifier.send_message(tg_start_msg)

    for name, func in steps:
        print(f"\n[진행] {name}...")
        start = time.time()
        try:
            func()
            elapsed = time.time() - start
            print(f"   ✅ 완료 ({elapsed:.1f}초)")
            # 텔레그램 간략 보고 (너무 시끄럽지 않게 요약해서)
            # notifier.send_message(f"✅ {name} 완료 ({elapsed:.1f}s)")
        except Exception as e:
            error_msg = f"🚨 <b>[작전 실패] {name} 단계에서 오류 발생!</b>\n\n내용: <code>{str(e)}</code>"
            print(f"   {error_msg}")
            notifier.send_message(error_msg)
            return # 실패 시 중단

    print("\n" + "=" * 70)
    print(" [작전 결과 보고서]")
    print("=" * 70)
    try:
        generate_full_report()
        notifier.send_message("🏁 <b>모든 데이터 동기화 및 분석이 완료되었습니다.</b>")
    except Exception as e:
        final_err = f"🚨 <b>리포트 생성 중 최종 오류:</b> {str(e)}"
        print(f"   {final_err}")
        notifier.send_message(final_err)

if __name__ == "__main__":
    main()
