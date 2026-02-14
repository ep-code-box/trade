import time
import asyncio
import os
import requests
import sqlite3
from datetime import datetime
from src.db import get_connection
from src.account import get_account_balance, sync_account_positions
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
        # [v16.10] 실시간 체결가 조회를 위해 TR_ID 명시 (FHKST01010100)
        res = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", 
                                     params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
                                     tr_id="FHKST01010100")
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
            return {"rt_cd": "0", "msg1": "SAFETY_MODE_ACTIVE"} 

        now = datetime.now()
        hm = now.hour * 100 + now.minute
        
        # 15:30~15:40 사이에는 장후 시간외 종가(03) 사용
        ord_dvsn = "01"
        if 1530 <= hm < 1540:
            ord_dvsn = "03"
        elif hm >= 1540:
            # 15:40 이후에는 예약 주문으로 전환하는 것이 좋으나, 봇 특성상 15:35에 종료되므로 일단 03 유지 또는 에러 처리
            ord_dvsn = "03"

        tr_id = "TTTC0802U" if MODE == "real" else "VTTC0802U"
        if side == "SELL": tr_id = "TTTC0801U" if MODE == "real" else "VTTC0801U"
        
        body = {
            "CANO": self.cano, "ACNT_PRDT_CD": self.acnt_prdt_cd, "PDNO": symbol,
            "ORD_DVSN": ord_dvsn, "ORD_QTY": str(qty), "ORD_UNPR": "0"
        }
        return await kis_post_async("/uapi/domestic-stock/v1/trading/order-cash", body=body, tr_id=tr_id)

    async def monitor_and_trade(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚙️ 감시 중 (안전모드:{SAFETY_MODE})")
        
        # [v22.1] 매도 후 자동 감시 해제: KIS 실잔고와 DB 동기화 강제 실행
        sync_account_positions()

        # [v16.8] 중복 매수 방지: 현재 보유 종목 리스트 확보
        positions = await self.get_positions()
        owned_symbols = [p['pdno'] for p in positions]

        conn = get_connection()
        cur = conn.cursor()
        
        # 1. 매수 감시 (장바구니 또는 trade_plan에서 MONITORING 인 종목)
        # [v16.4] 통합 매수 감시: 경로와 상관없이 MONITORING 상태면 사격 준비
        cur.execute("""
            SELECT DISTINCT code, name, entry_price 
            FROM trade_plan 
            WHERE status = 'MONITORING'
            AND date = (SELECT MAX(date) FROM trade_plan)
        """)
        for symbol, name, target_price in cur.fetchall():
            if symbol in owned_symbols:
                continue # 이미 보유 중이면 패스
                
            curr = await self.get_current_price(symbol)
            print(f"   [Checking] {name}({symbol}): Curr={curr}, Target={target_price}")
            if curr and curr >= target_price:
                print(f"🎯 [매수 신호] {name}({symbol}) 돌파! {curr} >= {target_price}")
                
                # [v16.6] 자산 기반 수량 계산 (10% Rule)
                qty = 1
                try:
                    from src.account import get_account_balance
                    balance = get_account_balance()
                    if balance and 'summary' in balance:
                        total_asset = balance['summary']['total_asset']
                        # 한 종목당 총 자산의 10% 배정
                        qty = max(1, int((total_asset * 0.1) / curr))
                except: pass

                res = await self.execute_order(symbol, "BUY", qty=qty)
                if res and res.get('rt_cd') == '0':
                    prefix = "⚠️ <b>[매수 알림 (안전모드)]</b>" if SAFETY_MODE else "🚀 <b>[자동 매수 완료]</b>"
                    notifier.send_message(f"{prefix}\n종목: {name}({symbol})\n가격: {curr:,}원\n수량: {qty:,}주\n목표가: {target_price:,}원")
                    if not SAFETY_MODE:
                        # 매수 완료 후 상태 변경 (중복 매수 방지)
                        conn.execute("UPDATE trade_plan SET status = 'ORDERED' WHERE code = ? AND status = 'MONITORING'", (symbol,))
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
            
            # [v16.3] 시스템 추천 이력이 없더라도 account_positions_audit에 있으면 감시 대상 포함
            cur.execute("SELECT manual_shield, highest_price, peak_price FROM account_positions_audit WHERE symbol = ?", (symbol,))
            audit_row = cur.fetchone()

            if not tp_row and not audit_row:
                continue 
            
            track = tp_row[0].upper() if tp_row else "MANUAL"
            if 'TRACK2' in track:
                continue # 트랙 2 (배당주)는 자동 매도에서 제외

            manual_shield = audit_row[0] if audit_row else 0
            # highest_price와 peak_price 혼용 대응
            highest_price = max(audit_row[1] or 0, audit_row[2] or 0, curr)
            
            if curr > highest_price:
                highest_price = curr
                # 트레일링 스탑: 최고점 대비 -5%
                new_shield = int(highest_price * 0.95)
                if new_shield > manual_shield:
                    manual_shield = new_shield
                    cur.execute("""
                        INSERT OR REPLACE INTO account_positions_audit (symbol, manual_shield, highest_price, peak_price, updated_at)
                        VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
                    """, (symbol, manual_shield, highest_price, highest_price))
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
                    # 15:35까지 감시하여 종가 확인 및 장후 시간외 처리 허용
                    if 900 <= current_min <= 1535:
                        try: await self.monitor_and_trade()
                        except Exception as e: print(f"Error: {e}")
                await asyncio.sleep(60)
        print(f"🚀 TradeBot 가동 (안전모드: {SAFETY_MODE})")
        asyncio.run(loop())

if __name__ == "__main__":
    TradeBot().run()