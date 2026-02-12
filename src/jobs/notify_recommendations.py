"""텔레그램 추천 종목 브리핑 모듈: trade_plan의 최신 추천주 전송."""
import sqlite3
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 설정 (모듈 임포트용)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.notifier import notifier
from src.config import ROOT

DB_PATH = os.path.join(ROOT, "TrendHunter", "db", "stock_info.db")

def get_latest_recommendations():
    """DB에서 가장 최근 날짜의 추천 종목(READY/WATCH)을 가져옴."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # 1. 가장 최근 날짜 찾기
        cur.execute("SELECT MAX(date) FROM trade_plan")
        latest_date = cur.fetchone()[0]
        
        if not latest_date:
            return None, []

        # 2. 해당 날짜의 추천주 조회 (RS 내림차순)
        query = """
            SELECT name, code, track, rs_score, entry_price, stop_price, rationale
            FROM trade_plan 
            WHERE date = ? AND status IN ('READY', 'WATCH')
            ORDER BY rs_score DESC
        """
        cur.execute(query, (latest_date,))
        rows = cur.fetchall()
        conn.close()
        
        return latest_date, rows
    except Exception as e:
        print(f"[Error] DB 조회 실패: {e}")
        return None, []

def send_recommendation_report():
    date, rows = get_latest_recommendations()
    
    if not rows:
        print(" [!] 전송할 추천 종목이 없습니다.")
        return

    # 메시지 구성
    tg_msg = f"🚀 <b>TrendHunter 추천 브리핑 ({date})</b>\n"
    tg_msg += f"────────────────\n"
    
    track1_count = 0
    track2_count = 0
    
    # 상위 10개 전송
    top_picks = rows[:10]
    
    for name, code, track, rs, entry, shield, note in top_picks:
        icon = "💎" if "TRACK1" in track.upper() or "트랙 1" in track else "💰"
        
        tg_msg += f"<b>{icon} {name} ({code})</b>\n"
        tg_msg += f" • RS: <b>{rs:.0f}</b> | 🎯 <b>{entry:,}원</b>\n"
        tg_msg += f" • 🛡️ <b>Shield: {shield:,}원</b>\n"
        tg_msg += f" • 사유: {note}\n\n"
        
        if icon == "💎": track1_count += 1
        else: track2_count += 1

    tg_msg += f"────────────────\n"
    tg_msg += f"📊 <b>요약</b>: Trend {track1_count}종목 / Value {track2_count}종목\n"
    tg_msg += f"💡 <i>전체 리스트는 대시보드를 확인하세요.</i>"

    # 전송
    print(" >> 텔레그램으로 추천 리포트 전송 중...")
    notifier.send_message(tg_msg)
    print(" >> 전송 완료.")

if __name__ == "__main__":
    send_recommendation_report()
