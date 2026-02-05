from fastapi import APIRouter, HTTPException
import sqlite3
import os
from src.db import get_connection
from src.kis_api import register_auto_order
from src.account import get_account_balance
from src.auth import load_config_from_db

router = APIRouter(tags=["basket"])

@router.get("/basket")
def get_basket():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT symbol, name FROM basket")
    rows = cur.fetchall()
    conn.close()
    return [{"symbol": row[0], "name": row[1]} for row in rows]

@router.post("/basket")
def add_to_basket(item: dict):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO basket (symbol, name) VALUES (?, ?)", (item['symbol'], item['name']))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/basket/{symbol}")
def remove_from_basket(symbol: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM basket WHERE symbol = ?", (symbol,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order/buy")
async def place_buy_order(req: dict):
    """
    [v6.9] 바스켓 종목에 대해 실전 매수 예약 등록 (Hashkey 보강 완료).
    """
    # 프론트엔드에서 넘겨주는 필드명 확인 (symbol 또는 code)
    symbol = req.get("symbol") or req.get("code")
    name = req.get("name") or "Unknown"
    
    print(f"[ORDER] 주문 프로세스 시작: {name}({symbol})")
    
    if not symbol:
        return {"status": "error", "message": "종목 코드가 누락되었습니다."}

    try:
        # 1. API 설정 로드
        config = load_config_from_db()
        cano = config.get("KIS_CANO")
        cano_pwd = config.get("KIS_CANO_PWD")
        
        if not cano:
            return {"status": "error", "message": "계좌 설정(CANO)이 없습니다."}

        # 2. trade_plan에서 최신 매수 목표가(entry_price) 조회
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT entry_price FROM trade_plan WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return {"status": "error", "message": f"'{name}'의 매매 계획이 없습니다."}
        
        entry_price = int(row[0])

        # 3. 계좌 잔고 확인 및 수량 계산 (10% 비중)
        balance = get_account_balance()
        if not balance:
            return {"status": "error", "message": "잔고 조회 실패"}
            
        total_asset = balance['summary']['total_asset']
        target_amt = total_asset * 0.1
        qty = max(1, int(target_amt / entry_price))
        
        # 4. KIS 현금 주문 호출 (이제 예약이 아닌 즉시 주문 시도)
        from src.kis_api import place_order_cash
        print(f"[TRACE] KIS 현금 주문 호출 직전 (수량: {qty})...")
        res = await place_order_cash(symbol, qty, cano=cano)
        print(f"[TRACE] KIS 주문 응답 수신: {res}")
        
        if res and res.get('rt_cd') == '0':
            return {"status": "success", "message": f"{name} {qty}주 주문 성공!"}
        else:
            err_msg = res.get('msg1', 'API 응답 에러') if res else '응답 없음'
            return {"status": "error", "message": f"KIS 실패: {err_msg}"}
            
    except Exception as e:
        print(f"[ERROR] 주문 처리 중 예외 발생: {str(e)}")
        return {"status": "error", "message": f"시스템 오류: {str(e)}"}