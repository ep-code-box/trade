from fastapi import APIRouter, HTTPException
import sqlite3
from pydantic import BaseModel
from src.db import get_connection
from src.kis_api import kis_get_raw_async, kis_post_async, register_auto_order
from src.auth import MODE, load_config_from_db
import os

router = APIRouter(tags=["basket"])

class BasketItem(BaseModel):
    symbol: str
    name: str

class OrderRequest(BaseModel):
    symbol: str
    price: int = 0  # 0이면 DB의 entry_price 사용

@router.get("/basket")
def get_basket():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT symbol, name FROM basket")
    rows = cur.fetchall()
    conn.close()
    return [{"symbol": row[0], "name": row[1]} for row in rows]

@router.post("/basket")
def add_to_basket(item: BasketItem):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO basket (symbol, name) VALUES (?, ?)", (item.symbol, item.name))
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
async def place_buy_order(req: OrderRequest):
    """서버 자동주문 감시 예약 등록 (Buy Stop)"""
    db_conf = load_config_from_db()
    cano = db_conf.get("KIS_CANO") or os.getenv("CANO")
    
    if not cano:
        raise HTTPException(status_code=400, detail="Account configuration missing")

    # 1. DB에서 알고리즘이 설정한 목표가(entry_price) 조회
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT entry_price, name 
            FROM trade_plan 
            WHERE code = ? 
            ORDER BY date DESC LIMIT 1
        """, (req.symbol,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Trade plan not found for this stock")
        
        target_price = row[0]
        stock_name = row[1]
        
        if target_price <= 0:
            raise HTTPException(status_code=400, detail="Invalid target price in trade plan")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 2. 서버 자동주문 등록 (Buy Stop: 목표가 돌파 시 시장가 매수)
    res = await register_auto_order(req.symbol, "BUY", target_price, qty=1)
    
    if res and res.get('rt_cd') == '0':
        # 성공 시 바구니에서 제거
        remove_from_basket(req.symbol)
        return {
            "status": "success", 
            "message": f"[{stock_name}] {target_price:,}원 돌파 시 매수 예약 완료",
            "data": res.get('output')
        }
    else:
        error_msg = res.get('msg1') if res else "Unknown KIS API error"
        return {"status": "error", "message": error_msg}