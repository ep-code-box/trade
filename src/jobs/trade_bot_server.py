
import asyncio
import os
from datetime import datetime
from src.db import get_connection
from src.kis_api import register_auto_order, cancel_auto_order, kis_get_raw_async
from src.auth import MODE, load_config_from_db
from src.utils.notifier import notifier

# 실제 주문 실행을 위해 SAFETY_MODE를 False로 설정 (사용자 요청: 돌파 매매 필수)
SAFETY_MODE = False 

class ServerTradeBot:
    def __init__(self):
        self.config = load_config_from_db()
        self.cano = self.config.get("KIS_CANO")
        self.active_server_orders = {} # { symbol: order_sno }

    async def sync_auto_orders(self):
        """서버 감시 주문과 로컬 상태 동기화 (아침 09:00~15:30)"""
        now = datetime.now()
        hm = now.hour * 100 + now.minute
        if now.weekday() >= 5 or hm < 800 or hm > 1530:
            return # 장중이 아니면 서버 등록 불가

        print(f"[{now.strftime('%H:%M:%S')}] ⚙️ 돌파 매매(Stop) 서버 감시 동기화 중...")
        conn = get_connection()
        cur = conn.cursor()

        # 1. 매수 감시 대상 (Basket) 서버 등록
        cur.execute("""
            SELECT b.symbol, b.name, t.entry_price, t.stop_price 
            FROM basket b
            JOIN trade_plan t ON b.symbol = t.code
            WHERE t.date = (SELECT MAX(date) FROM trade_plan)
        """)
        for symbol, name, target, stop in cur.fetchall():
            if symbol not in self.active_server_orders:
                print(f"📡 [서버 돌파 예약] {name}({symbol}) 목표가 {target:,}원 감시 등록")
                if not SAFETY_MODE:
                    # 매수 스탑 등록
                    res = await register_auto_order(symbol, "BUY", target)
                    if res and res.get('rt_cd') == '0':
                        sno = res['output']['AUTO_ORD_SNO']
                        self.active_server_orders[symbol] = sno
                        # 손절 스탑도 함께 등록
                        if stop > 0:
                            await register_auto_order(symbol, "SELL", stop)
                        notifier.send_message(f"✅ <b>돌파 매매 서버 등록 완료</b>\n{name}\n- 진입: {target:,}원\n- 손절: {stop:,}원")
                    else:
                        print(f"❌ {name} 등록 실패: {res.get('msg1')}")
                else:
                    self.active_server_orders[symbol] = "DEBUG_SNO"
        
        conn.close()

    async def run(self):
        print(f"🚀 서버 사이드 돌파 매매 관리자 가동 (안전모드: {SAFETY_MODE})")
        while True:
            try:
                # 장 개시 직후(09:00) 빠르게 등록하기 위해 루프 주기를 조절
                await self.sync_auto_orders()
            except Exception as e:
                print(f"Sync Error: {e}")
            
            # 장중에는 1분마다, 장외에는 5분마다 체크
            now = datetime.now()
            sleep_time = 60 if 850 <= (now.hour * 100 + now.minute) <= 1530 else 300
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    bot = ServerTradeBot()
    asyncio.run(bot.run())
