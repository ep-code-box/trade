from fastapi import APIRouter, HTTPException
import sqlite3
from pydantic import BaseModel
from src.db import get_connection
from src.kis_api import kis_get_raw_async, kis_post_async
from src.auth import MODE, load_config_from_db
import os

router = APIRouter(tags=["basket"])

class BasketItem(BaseModel):
    symbol: str
    name: str

class OrderRequest(BaseModel):
    symbol: str
    price: int = 0  # 0이면 시장가 또는 현재가 기준

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
    """지정가/시장가 매수 주문 실행"""
    db_conf = load_config_from_db()
    cano = db_conf.get("KIS_CANO") or os.getenv("CANO")
    acnt_prdt_cd = db_conf.get("KIS_ACNT_PRDT_CD") or "01"
    
    if not cano:
        raise HTTPException(status_code=400, detail="Account configuration missing")

    # 1. 현재가 조회 (주문 가격이 0인 경우)
    price = req.price
    if price == 0:
        res = await kis_get_raw_async("/uapi/domestic-stock/v1/quotations/inquire-price", 
                                     params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": req.symbol})
        if res and res.get('rt_cd') == '0':
            price = int(res['output']['stck_prpr'])
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch current price")

    # 2. 가용 현금 조회 및 수량 계산 (간이 로직: 현금의 10% 또는 고정 비중)
    # 실제 구현시에는 계좌 잔고를 다시 조회하거나 프론트에서 전달받은 수량 사용
    # 여기서는 예시로 '시장가 1주' 주문을 기본으로 함
    
    tr_id = "TTTC0802U" if MODE == "real" else "VTTC0802U" # 현금 매수 주문
    
    body = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "PDNO": req.symbol,
        "ORD_DVSN": "01", # 00: 지정가, 01: 시장가
        "ORD_QTY": "1",
        "ORD_UNPR": "0" if price == 0 else str(price)
    }
    
    # 시장가 주문 시 가격은 0
    if body["ORD_DVSN"] == "01":
        body["ORD_UNPR"] = "0"

    res = await kis_post_async("/uapi/domestic-stock/v1/trading/order-cash", body=body, tr_id=tr_id)
    
    if res and res.get('rt_cd') == '0':
        # 주문 성공 시 바구니에서 제거 (옵션)
        remove_from_basket(req.symbol)
        return {"status": "success", "data": res.get('output')}
    else:
        return {"status": "error", "message": res.get('msg1') if res else "Unknown error"}
