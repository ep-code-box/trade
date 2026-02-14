
import asyncio
import os
from datetime import datetime
from src.db import get_connection
from src.kis_api import register_auto_order, cancel_auto_order, get_current_price_async, place_order_cash
from src.auth import MODE, load_config_from_db
from src.utils.notifier import notifier

# 실제 주문 실행을 위해 SAFETY_MODE를 False로 설정 (사용자 요청: 돌파 매매 필수)
SAFETY_MODE = False 

class ServerTradeBot:
    def __init__(self):
        self.config = load_config_from_db()
        self.cano = self.config.get("KIS_CANO")
        self.active_server_orders = {} # { symbol: order_no }

    async def sync_auto_orders(self):
        """서버 감시 주문과 로컬 상태 동기화 (아침 08:40~15:30)"""
        now = datetime.now()
        hm = now.hour * 100 + now.minute
        if now.weekday() >= 5 or hm < 840 or hm > 1530:
            return # 장중이 아니면 서버 등록 불가

        print(f"[{now.strftime('%H:%M:%S')}] ⚙️ 돌파 매매 서버 감시 동기화 중...")
        
        # [v16.9] 중복 매수 방지: 현재 보유 종목 확인
        owned_symbols = []
        try:
            from src.account import get_account_balance
            balance = get_account_balance()
            if balance and 'holdings' in balance:
                owned_symbols = [h['code'] for h in balance['holdings']]
        except: pass

        conn = get_connection()
        cur = conn.cursor()

        # 1. 매수 감시 대상 (trade_plan에서 MONITORING 인 모든 종목)
        cur.execute("""
            SELECT DISTINCT code, name, entry_price, stop_price 
            FROM trade_plan 
            WHERE status = 'MONITORING'
            AND date = (SELECT MAX(date) FROM trade_plan)
        """)
        for symbol, name, target, stop in cur.fetchall():
            if symbol in owned_symbols:
                continue # 이미 보유 중이면 감시 제외
                
            if symbol not in self.active_server_orders:
                # [v22.3] 현재가 확인: 이미 돌파했으면 시장가로 즉시 진입
                curr_price = await get_current_price_async(symbol)
                if curr_price and curr_price >= target:
                    print(f"🚀 [돌파 확인] {name}({symbol}) 현재가({curr_price:,}원) >= 목표가({target:,}원) -> 시장가 진입")
                    if not SAFETY_MODE:
                        qty = 1 # 기본값, 필요시 calculate_qty 호출
                        try:
                            balance = get_account_balance()
                            if balance and 'summary' in balance:
                                total_asset = balance['summary']['total_asset']
                                qty = max(1, int((total_asset * 0.1) / curr_price))
                        except: pass
                        
                        res = await place_order_cash(symbol, qty=qty, price=0, side="BUY", cano=self.cano, ord_dvsn="01")
                        if res and res.get('rt_cd') == '0':
                            self.active_server_orders[symbol] = res['output'].get('ODNO', 'MARKET_ORDER')
                            conn.execute("UPDATE trade_plan SET status = 'ORDERED' WHERE code = ? AND status = 'MONITORING'", (symbol,))
                            conn.commit()
                            notifier.send_message(f"🎯 <b>돌파 즉시 매수 완료</b>\n{name}\n현재가: {curr_price:,}원\n수량: {qty:,}주")
                    else:
                        self.active_server_orders[symbol] = "DEBUG_MARKET"
                    continue

                # 아직 돌파 전이면 서버 스탑 등록
                print(f"📡 [서버 스탑 예약] {name}({symbol}) 목표가 {target:,}원 감시 등록")
                if not SAFETY_MODE:
                    res = await register_auto_order(symbol, "BUY", target)
                    if res and res.get('rt_cd') == '0':
                        # [v22.4] 응답 구조 안전하게 추출 (리스트/딕셔너리 대응)
                        output = res.get('output', {})
                        if isinstance(output, list): output = output[0] if output else {}
                        
                        order_no = output.get('ODNO') or output.get('AUTO_ORD_SNO')
                        if not order_no:
                            print(f"⚠️ {name} 주문번호 추출 실패: {res}")
                            continue

                        self.active_server_orders[symbol] = order_no
                        if stop > 0:
                            await register_auto_order(symbol, "SELL", stop)
                        notifier.send_message(f"✅ <b>돌파 서버 감시 등록</b>\n{name}\n- 진입: {target:,}원\n- 손절: {stop:,}원")
                    else:
                        print(f"❌ {name} 등록 실패: {res.get('msg1')}")
                else:
                    self.active_server_orders[symbol] = "DEBUG_STOP"
        
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
