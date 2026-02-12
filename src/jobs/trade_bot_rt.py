import asyncio
import json
import websockets
import sqlite3
import os
import sys
from datetime import datetime
from src.db import get_connection
from src.auth import APP_KEY, APP_SECRET, MODE, get_websocket_approval_key, get_access_token, load_config_from_db
from src.kis_api import place_order_cash
from src.utils.notifier import notifier
from src.account import get_account_balance
from src.analysis.screen_market import adjust_to_tick

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 안전 모드 설정 (실전 매매 시 False로 변경 필수!)
SAFETY_MODE = False

class RealTimeTradeBot:
    def __init__(self):
        self.approval_key = get_websocket_approval_key()
        self.ws_url = "ws://ops.koreainvestment.com:21000" if MODE == "real" else "ws://ops.koreainvestment.com:31000"
        self.managed_symbols = set()
        self.managed_basket = {}    # { symbol: {target, stop, name} }
        self.managed_positions = {} # { symbol: {shield, peak, entry, name} }
        self.is_running = True

    async def update_monitoring_list(self):
        """DB에서 감시 대상을 최신화 (매 1분마다 자동 호출)"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            # 1. 매수 감시 (status='MONITORING')
            cur.execute("""
                SELECT code, name, entry_price, stop_price 
                FROM trade_plan 
                WHERE status = 'MONITORING'
                AND date = (SELECT MAX(date) FROM trade_plan)
            """)
            self.managed_basket = {row[0]: {"name": row[1], "target": row[2], "stop": row[3]} for row in cur.fetchall()}

            # 2. 매도 감시 (보유 종목 및 트레일링 스탑)
            cur.execute("SELECT symbol, manual_shield, peak_price, entry_price FROM account_positions_audit WHERE qty > 0")
            new_positions = {}
            for row in cur.fetchall():
                symbol, shield, peak, entry = row
                new_positions[symbol] = {
                    "shield": shield or int(entry * 0.93),
                    "peak": max(peak or 0, entry or 0),
                    "entry": entry or 0,
                    "name": symbol 
                }
            self.managed_positions = new_positions
            
            conn.close()
            self.managed_symbols = set(self.managed_basket.keys()) | set(self.managed_positions.keys())
            return self.managed_symbols
        except Exception as e:
            print(f"❌ [RT] 리스트 업데이트 오류: {e}")
            return set()

    async def calculate_qty(self, price):
        """계좌 자산의 10%에 해당하는 수량 계산"""
        try:
            balance = get_account_balance()
            if balance and 'summary' in balance:
                total_asset = balance['summary']['total_asset']
                qty = max(1, int((total_asset * 0.1) / price))
                return qty
        except: pass
        return 1 # 기본값

    async def execute_real_order(self, symbol, name, side="BUY", price=0):
        """실제 주문 실행 및 DB 완결 처리"""
        global SAFETY_MODE
        qty = await self.calculate_qty(price) if side == "BUY" else 1 # 매도는 실제 보유수량 로직 필요(생략)

        if SAFETY_MODE:
            print(f"⚠️ [SAFETY] {side} 시뮬레이션: {name}({symbol}) {price:,}원")
            # 테스트를 위해 DB 상태는 변경
            conn = get_connection()
            if side == "BUY":
                conn.execute("UPDATE trade_plan SET status = 'ORDERED' WHERE code = ? AND status = 'MONITORING'", (symbol,))
                conn.execute("INSERT OR REPLACE INTO account_positions_audit (symbol, entry_price, peak_price, qty, updated_at) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))", (symbol, price, price, qty))
            else:
                conn.execute("DELETE FROM account_positions_audit WHERE symbol = ?", (symbol,))
            conn.commit(); conn.close()
            await self.update_monitoring_list()
            return True

        try:
            config = load_config_from_db()
            res = await place_order_cash(symbol, qty=qty, price=0, side=side, cano=config.get("KIS_CANO"), ord_dvsn="01")
            if res and res.get('rt_cd') == '0':
                conn = get_connection()
                if side == "BUY":
                    conn.execute("UPDATE trade_plan SET status = 'ORDERED' WHERE code = ? AND status = 'MONITORING'", (symbol,))
                    conn.execute("INSERT OR REPLACE INTO account_positions_audit (symbol, entry_price, peak_price, qty, updated_at) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))", (symbol, price, price, qty))
                else:
                    conn.execute("DELETE FROM account_positions_audit WHERE symbol = ?", (symbol,))
                conn.commit(); conn.close()
                await self.update_monitoring_list()
                return True
            return False
        except Exception as e:
            print(f"🚨 [RT] 주문 에러: {e}"); return False

    async def handle_realtime_data(self, data):
        if "|" not in data: return
        parts = data.split('|')
        if len(parts) < 4 or parts[1] != "H0STCNT0": return
        
        payload = parts[3].split('^')
        symbol, curr_price = payload[0], int(payload[2])
        
        # 1. 매수 (돌파 감시)
        if symbol in self.managed_basket:
            item = self.managed_basket[symbol]
            if curr_price >= item['target']:
                print(f"🚀 [BUY TRIGGER] {item['name']} {curr_price:,}원")
                if await self.execute_real_order(symbol, item['name'], "BUY", curr_price):
                    notifier.send_message(f"🎯 <b>[매수 체결]</b> {item['name']}\n가격: {curr_price:,}원\n이제 쉴드 감시를 시작합니다.")

        # 2. 매도 (쉴드 & 트레일링)
        if symbol in self.managed_positions:
            pos = self.managed_positions[symbol]
            if curr_price > pos['peak']:
                pos['peak'] = curr_price
                if curr_price > pos['entry']:
                    new_shield = adjust_to_tick(int(curr_price * 0.95), 'down')
                    if new_shield > pos['shield']:
                        pos['shield'] = new_shield
                        conn = get_connection(); conn.execute("UPDATE account_positions_audit SET manual_shield=?, peak_price=?, updated_at=datetime('now','localtime') WHERE symbol=?", (new_shield, curr_price, symbol)); conn.commit(); conn.close()
                        print(f"📈 [SHIELD UP] {symbol} -> {new_shield:,}")

            if curr_price <= pos['shield']:
                print(f"🛡️ [SHIELD TRIGGER] {symbol} {curr_price:,} <= {pos['shield']:,}")
                if await self.execute_real_order(symbol, pos['name'], "SELL", curr_price):
                    notifier.send_message(f"🛡️ <b>[수익 보존 매도]</b> {pos['name']}\n가격: {curr_price:,}원\n상황 종료.")

    async def run(self):
        print(f"🟢 RT Engine Standby... (Safety: {SAFETY_MODE})")
        while self.is_running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    await self.update_monitoring_list()
                    for s in self.managed_symbols:
                        await websocket.send(json.dumps({"header":{"approval_key":self.approval_key,"custtype":"P","tr_type":"1","content-type":"utf-8"},"body":{"input":{"tr_id":"H0STCNT0","tr_key":s}}}))
                    
                    async def update_loop():
                        while self.is_running:
                            await asyncio.sleep(60)
                            old = self.managed_symbols.copy()
                            new = await self.update_monitoring_list()
                            for s in (new - old):
                                await websocket.send(json.dumps({"header":{"approval_key":self.approval_key,"custtype":"P","tr_type":"1","content-type":"utf-8"},"body":{"input":{"tr_id":"H0STCNT0","tr_key":s}}}))
                    
                    asyncio.create_task(update_loop())
                    async for msg in websocket:
                        if not msg.startswith("{"): await self.handle_realtime_data(msg)
            except Exception as e:
                print(f"⚠️ Reconnecting: {e}"); await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(RealTimeTradeBot().run())