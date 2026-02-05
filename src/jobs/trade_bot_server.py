
import asyncio
import os
from datetime import datetime
from src.db import get_connection
from src.kis_api import register_auto_order, cancel_auto_order, kis_get_raw_async
from src.auth import MODE, load_config_from_db
from src.utils.notifier import notifier

# 안전 모드 설정 (True: 서버 등록 안함 / False: 실제 서버 감시 등록)
SAFETY_MODE = True 

class ServerTradeBot:
    def __init__(self):
        self.config = load_config_from_db()
        self.cano = self.config.get("KIS_CANO")
        self.active_server_orders = {} # { symbol: order_sno }

    async def sync_auto_orders(self):
        """서버 감시 주문과 로컬 상태 동기화"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚙️ 서버 감시 주문 동기화 중...")
        conn = get_connection()
        cur = conn.cursor()

        # 1. 매수 감시 대상 (Basket) 서버 등록
        cur.execute("""
            SELECT b.symbol, b.name, t.entry_price 
            FROM basket b
            JOIN trade_plan t ON b.symbol = t.code
            WHERE t.date = (SELECT MAX(date) FROM trade_plan)
        """)
        for symbol, name, target in cur.fetchall():
            if symbol not in self.active_server_orders:
                print(f"📡 [서버 예약] {name}({symbol}) 목표가 {target:,}원 매수 감시 등록")
                if not SAFETY_MODE:
                    res = await register_auto_order(symbol, "BUY", target)
                    if res and res.get('rt_cd') == '0':
                        sno = res['output']['AUTO_ORD_SNO']
                        self.active_server_orders[symbol] = sno
                        notifier.send_message(f"✅ <b>서버 매수 예약 완료</b>
{name} ({target:,}원 돌파 시)")
                else:
                    self.active_server_orders[symbol] = "DEBUG_SNO"
                    notifier.send_message(f"⚠️ <b>[안전모드] 서버 매수 예약 탐지</b>
{name} ({target:,}원)")

        # 2. 매도 감시 대상 (Trailing Stop) 서버 등록/갱신
        # (계좌 잔고 조회 로직과 연동하여 보유 종목 중 트랙 1/EX 종목 처리)
        # 이 부분은 KIS의 '자동주문조회' API를 통해 현재 서버에 걸린 상태를 먼저 읽어와야 정교해집니다.
        
        conn.close()

    async def run(self):
        print(f"🚀 서버 사이드 매매 관리자 가동 (안전모드: {SAFETY_MODE})")
        while True:
            try:
                await self.sync_auto_orders()
            except Exception as e:
                print(f"Sync Error: {e}")
            
            await asyncio.sleep(300) # 5분마다 동기화 관리

if __name__ == "__main__":
    bot = ServerTradeBot()
    asyncio.run(bot.run())
