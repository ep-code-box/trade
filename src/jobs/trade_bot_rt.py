
import asyncio
import json
import websockets
import sqlite3
import os
from datetime import datetime
from src.db import get_connection
from src.auth import APP_KEY, APP_SECRET, MODE, get_websocket_approval_key, get_access_token
from src.kis_api import kis_post_async
from src.utils.notifier import notifier

# 안전 모드 설정 (테스트 완료 전까지 True 권장)
SAFETY_MODE = True

class RealTimeTradeBot:
    def __init__(self):
        self.approval_key = get_websocket_approval_key()
        self.ws_url = "ws://ops.koreainvestment.com:21000" if MODE == "real" else "ws://ops.koreainvestment.com:31000"
        self.subscribed_symbols = set()
        self.managed_positions = {} # { symbol: {shield, qty, name} }
        self.managed_basket = {}    # { symbol: {target, name} }

    async def update_monitoring_list(self):
        """계좌 잔고 및 바구니 정보를 읽어와서 감시 리스트 최신화"""
        conn = get_connection()
        cur = conn.cursor()
        
        # 1. 매수 감시 대상 (Basket)
        cur.execute("""
            SELECT b.symbol, b.name, t.entry_price 
            FROM basket b
            JOIN trade_plan t ON b.symbol = t.code
            WHERE t.date = (SELECT MAX(date) FROM trade_plan)
        """)
        new_basket = {row[0]: {"target": row[2], "name": row[1]} for row in cur.fetchall()}
        self.managed_basket = new_basket

        # 2. 매도 감시 대상 (Account Positions - Track 1/EX 전용)
        # (현 시점에서는 API 대신 DB에 기록된 포지션 정보를 우선 사용하거나, 별도 잔고 동기화 루프 필요)
        # 여기서는 편의상 account_positions_audit 테이블과 trade_plan을 조합
        cur.execute("""
            SELECT a.symbol, a.manual_shield, t.name 
            FROM account_positions_audit a
            JOIN trade_plan t ON a.symbol = t.code
            WHERE t.track NOT LIKE '%TRACK2%'
        """)
        new_positions = {row[0]: {"shield": row[1], "name": row[2]} for row in cur.fetchall()}
        self.managed_positions = new_positions
        
        conn.close()
        return set(self.managed_basket.keys()) | set(self.managed_positions.keys())

    async def execute_order(self, symbol, side="SELL", qty=1):
        """즉시 주문 실행"""
        if SAFETY_MODE:
            print(f"⚠️ [SAFETY] {side} 주문 차단: {symbol}")
            return True
        
        # 실제 주문 로직 (kis_post_async 활용)
        # ... (이전 TradeBot과 동일)
        return False

    async def handle_realtime_data(self, data):
        """웹소켓으로 들어온 체결 데이터 처리"""
        if data.startswith("0") or data.startswith("1"): # 체결 데이터인 경우
            parts = data.split('|')
            if len(parts) < 4: return
            
            payload = parts[3].split('^')
            symbol = payload[0]
            curr_price = int(payload[2])
            
            # 1. 매도(Shield) 감시
            if symbol in self.managed_positions:
                pos = self.managed_positions[symbol]
                if curr_price <= pos['shield']:
                    print(f"🚨 [RT SELL] {pos['name']} Shield 돌파! {curr_price} <= {pos['shield']}")
                    if await self.execute_order(symbol, "SELL"):
                        notifier.send_message(f"🛡️ <b>[실시간 손절 알림]</b>
{pos['name']} 이탈!
가격: {curr_price:,}원")
                        del self.managed_positions[symbol] # 중복 주문 방지

            # 2. 매수(Target) 감시
            if symbol in self.managed_basket:
                item = self.managed_basket[symbol]
                if curr_price >= item['target']:
                    print(f"🚀 [RT BUY] {item['name']} 목표가 돌파! {curr_price} >= {item['target']}")
                    if await self.execute_order(symbol, "BUY"):
                        notifier.send_message(f"🎯 <b>[실시간 매수 알림]</b>
{item['name']} 돌파!
가격: {curr_price:,}원")
                        del self.managed_basket[symbol]

    async def run(self):
        print(f"🚀 실시간 체결 엔진 가동 (안전모드: {SAFETY_MODE})")
        
        async with websockets.connect(self.ws_url) as websocket:
            # 초기 구독
            symbols = await self.update_monitoring_list()
            for sym in symbols:
                senddata = {
                    "header": { "approval_key": self.approval_key, "custtype": "P", "tr_type": "1", "content-type": "utf-8" },
                    "body": { "input": { "tr_id": "H0STCNT0", "tr_key": sym } }
                }
                await websocket.send(json.dumps(senddata))
                self.subscribed_symbols.add(sym)
                print(f"📡 {sym} 실시간 체결 구독 시작")

            while True:
                try:
                    data = await websocket.recv()
                    await self.handle_realtime_data(data)
                    
                    # 5분마다 감시 리스트 갱신 체크 (추가 구현 필요)
                except Exception as e:
                    print(f"WebSocket Error: {e}")
                    break

if __name__ == "__main__":
    bot = RealTimeTradeBot()
    asyncio.run(bot.run())
