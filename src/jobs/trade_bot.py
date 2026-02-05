import time
import asyncio
import os
import requests
import sqlite3
from datetime import datetime
from src.db import get_connection
from src.kis_api import kis_get_raw_async, kis_post_async
from src.auth import MODE, load_config_from_db, APP_KEY, APP_SECRET, BASE_URL
from src.utils.notifier import notifier

# --- 설정 ---
SAFETY_MODE = False  # True: 실제 주문 안함, 알림만 전송 | False: 실제 주문 실행

class TradeBot:
    def __init__(self):
        self.config = load_config_from_db()
        self.cano = self.config.get("KIS_CANO")
        self.acnt_prdt_cd = "01"

    async def get_current_price(self, symbol):
        res = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", 
                                     params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol})
        if res and res.get('rt_cd') == '0':
            return int(res['output']['stck_prpr'])
        return None

    async def get_positions(self):
        from src.auth import get_access_token
        token = get_access_token()
        tr_id = "TTTC8434R" if MODE == "real" else "VTTC8434R"
        headers = {
            "content-type": "application/json", "authorization": f"Bearer {token}",
            "appkey": APP_KEY, "appsecret": APP_SECRET, "tr_id": tr_id, "custtype": "P"
        }
        params = {
            "CANO": self.cano, "ACNT_PRDT_CD": self.acnt_prdt_cd, "AFHR_FLPR_YN": "N",
            "OFL_YN": "N", "INQR_DVSN": "02", "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N", "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00", "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""
        }
        try:
            res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance", headers=headers, params=params, timeout=10)
            data = res.json()
            return data.get('output1', []) if data.get('rt_cd') == '0' else []
        except: return []

    async def execute_order(self, symbol, side="BUY", qty=1):
        if SAFETY_MODE:
            print(f"⚠️ [SAFETY MODE] {side} 주문 차단됨: {symbol} x {qty}주")
            return {"rt_cd": "0", "msg1": "SAFETY_MODE_ACTIVE"} # 성공으로 간주하여 알림 유도

        tr_id = "TTTC0802U" if MODE == "real" else "VTTC0802U"
        if side == "SELL": tr_id = "TTTC0801U" if MODE == "real" else "VTTC0801U"
        body = {
            "CANO": self.cano, "ACNT_PRDT_CD": self.acnt_prdt_cd, "PDNO": symbol,
            "ORD_DVSN": "01", "ORD_QTY": str(qty), "ORD_UNPR": "0"
        }
        return await kis_post_async("/uapi/domestic-stock/v1/trading/order-cash", body=body, tr_id=tr_id)

    async def monitor_and_trade(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚙️ 감시 중 (안전모드:{SAFETY_MODE})")
        conn = get_connection()
        cur = conn.cursor()
        
        # 1. 매수 감시
        cur.execute("""
            SELECT b.symbol, b.name, t.entry_price 
            FROM basket b
            JOIN trade_plan t ON b.symbol = t.code
            WHERE t.date = (SELECT MAX(date) FROM trade_plan)
        """)
        for symbol, name, target_price in cur.fetchall():
            curr = await self.get_current_price(symbol)
            if curr and curr >= target_price:
                print(f"🎯 [매수 신호] {name}({symbol}) 돌파! {curr} >= {target_price}")
                res = await self.execute_order(symbol, "BUY")
                if res and res.get('rt_cd') == '0':
                    prefix = "⚠️ <b>[매수 알림 (안전모드)]</b>" if SAFETY_MODE else "🚀 <b>[자동 매수 완료]</b>"
                    notifier.send_message(f"{prefix}\n종목: {name}({symbol})\n가격: {curr:,}원\n목표가: {target_price:,}원")
                    if not SAFETY_MODE:
                        conn.execute("DELETE FROM basket WHERE symbol = ?", (symbol,))
                        conn.commit()

        # 2. 매도 및 트레일링 스탑 감시
        positions = await self.get_positions()
        for pos in positions:
            symbol = pos['pdno']
            name = pos['prdt_name']
            qty = int(pos['hldg_qty'])
            curr = int(pos['prpr'])
            if qty <= 0: continue

            # [v9.3] 시스템 관리 종목 판별 (Track 1 / EX 만 해당)
            cur.execute("SELECT track FROM trade_plan WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
            tp_row = cur.fetchone()
            
            if not tp_row:
                continue # 시스템 추천 이력이 없으면 건드리지 않음
            
            track = tp_row[0].upper()
            if 'TRACK2' in track:
                continue # 트랙 2 (배당주)는 자동 매도에서 제외

            cur.execute("SELECT manual_shield, highest_price FROM account_positions_audit WHERE symbol = ?", (symbol,))
            row = cur.fetchone()
            manual_shield = row[0] if row else 0
            highest_price = row[1] if row else curr
            
            if curr > highest_price:
                highest_price = curr
                new_shield = int(highest_price * 0.95)
                if new_shield > manual_shield:
                    manual_shield = new_shield
                    cur.execute("""
                        INSERT OR REPLACE INTO account_positions_audit (symbol, manual_shield, highest_price, updated_at)
                        VALUES (?, ?, ?, datetime('now', 'localtime'))
                    """, (symbol, manual_shield, highest_price))
                    conn.commit()
                    print(f"📈 [Shield 상향] {name}: {manual_shield:,}원")

            if manual_shield == 0:
                cur.execute("SELECT stop_price FROM trade_plan WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
                tp_row = cur.fetchone()
                manual_shield = tp_row[0] if tp_row else int(curr * 0.93)

            if curr <= manual_shield:
                print(f"🚨 [매도 신호] {name} {curr} <= {manual_shield}")
                res = await self.execute_order(symbol, "SELL", qty=qty)
                if res and res.get('rt_cd') == '0':
                    prefix = "⚠️ <b>[매도 알림 (안전모드)]</b>" if SAFETY_MODE else "🛡️ <b>[자동 매도 완료]</b>"
                    notifier.send_message(f"{prefix}\n종목: {name}({symbol})\n가격: {curr:,}원\n사유: Shield({manual_shield:,}원) 이탈")
                    if not SAFETY_MODE:
                        conn.execute("DELETE FROM account_positions_audit WHERE symbol = ?", (symbol,))
                        conn.commit()

        conn.close()

    def run(self):
        async def loop():
            while True:
                now = datetime.now()
                if now.weekday() < 5:
                    current_min = now.hour * 100 + now.minute
                    if 930 <= current_min <= 1530:
                        try: await self.monitor_and_trade()
                        except Exception as e: print(f"Error: {e}")
                await asyncio.sleep(60)
        print(f"🚀 TradeBot 가동 (안전모드: {SAFETY_MODE})")
        asyncio.run(loop())

if __name__ == "__main__":
    TradeBot().run()