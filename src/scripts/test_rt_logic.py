import asyncio
import sqlite3
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.jobs.trade_bot_rt import RealTimeTradeBot
from src.db import get_connection

async def simulate_test():
    print("🧪 [TEST] 실시간 감시 엔진 가상 시뮬레이션 시작")
    
    # 1. 테스트용 데이터 준비 (삼성전자 005930 예시)
    symbol = "005930"
    target_price = 70000
    
    conn = get_connection()
    cur = conn.cursor()
    # 기존 계획 삭제 후 테스트용 계획 삽입
    cur.execute("DELETE FROM trade_plan WHERE code = ?", (symbol,))
    cur.execute("""
        INSERT INTO trade_plan (date, code, name, entry_price, stop_price, status)
        VALUES (strftime('%Y%m%d', 'now'), ?, '삼성전자', ?, 65000, 'MONITORING')
    """, (symbol, target_price))
    conn.commit()
    conn.close()
    
    print(f"✅ [TEST] {symbol} 종목을 {target_price}원에 감시 대상으로 등록했습니다.")

    # 2. 봇 초기화
    bot = RealTimeTradeBot()
    # 봇이 DB에서 리스트를 읽어오도록 유도
    await bot.update_monitoring_list()
    
    print(f"📡 [TEST] 현재 감시 리스트: {bot.managed_basket}")

    # 3. 돌파 시뮬레이션 (웹소켓 메시지 모사)
    # H0STCNT0|005930|...|현재가|... 형식
    mock_price = 70500
    mock_message = f"0|H0STCNT0|001|{symbol}^153000^{mock_price}^100^500^0.7^..."
    
    print(f"📈 [TEST] 현재가 {mock_price}원 발생! (목표가 {target_price}원 돌파 시도)")
    
    # 봇의 데이터 처리 함수 호출
    await bot.handle_realtime_data(mock_message)
    
    # 4. 결과 확인
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status FROM trade_plan WHERE code = ?", (symbol,))
    status = cur.fetchone()[0]
    conn.close()
    
    if status == 'ORDERED' or (bot.SAFETY_MODE and status == 'MONITORING'):
        print(f"🎉 [TEST] 성공! 봇이 가격 돌파를 감지하고 주문 로직을 트리거했습니다. (최종 상태: {status})")
    else:
        print(f"❌ [TEST] 실패. 상태가 변경되지 않았습니다. (현재 상태: {status})")

if __name__ == "__main__":
    asyncio.run(simulate_test())
