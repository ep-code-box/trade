from fastapi import APIRouter, HTTPException
import sqlite3
import os
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.kis_api import place_order_cash
from src.account import get_account_balance
from src.auth import load_config_from_db
from src.analysis.screen_market import get_tick_size, adjust_to_tick, get_breakout_price

router = APIRouter(tags=["basket"])

@router.get("/basket")
def get_basket():
    try:
        conn = get_connection()
        # [v25.16] 바구니 생존 쿼리: 바구니에 있으면 무조건 출력 (시세 데이터 누락 방어)
        query = """
            SELECT 
                b.symbol, b.name,
                d.close as price,
                t.entry_price as targetPrice, t.stop_price as stopLossPrice, 
                t.status
            FROM basket b
            LEFT JOIN (
                SELECT code, close, ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) as rn
                FROM daily_analysis
            ) d ON b.symbol = d.code AND d.rn = 1
            LEFT JOIN (
                SELECT code, entry_price, stop_price, status, ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC, id DESC) as rn
                FROM trade_plan
            ) t ON b.symbol = t.code AND t.rn = 1
        """
        df = pd.read_sql_query(query, conn)
        
        # 권장 수량 계산을 위한 자산 정보
        balance = get_account_balance()
        total_asset = balance['summary']['total_asset'] if balance and 'summary' in balance else 0
        conn.close()

        results = []
        for _, row in df.iterrows():
            target = float(row['targetPrice'] or 0)
            recommended_qty = max(1, int((total_asset * 0.1) / target)) if total_asset > 0 and target > 0 else 1
            
            results.append({
                "symbol": str(row['symbol']),
                "name": str(row['name']),
                "price": int(row['price'] or 0),
                "targetPrice": int(target),
                "stopLossPrice": int(row['stopLossPrice'] or 0),
                "status": str(row['status'] or "READY"),
                "recommendedQty": recommended_qty,
                "estimatedAmount": int(recommended_qty * target)
            })
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

@router.post("/basket")
def add_to_basket(item: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO basket (symbol, name) VALUES (?, ?)", (item['symbol'], item['name']))
    conn.commit()
    conn.close()
    return {"status": "success"}

@router.post("/order/cancel")
async def cancel_monitoring(req: dict):
    symbol = req.get("symbol") or req.get("code")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE trade_plan SET status = 'READY' WHERE code = ? AND status = 'MONITORING'", (symbol,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "실시간 감시가 중단되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.delete("/basket/{symbol}")
def remove_from_basket(symbol: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM basket WHERE symbol = ?", (symbol,))
    cur.execute("UPDATE trade_plan SET status = 'READY' WHERE code = ? AND status = 'MONITORING'", (symbol,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@router.post("/order/buy")
async def place_buy_order(req: dict):
    symbol = req.get("symbol") or req.get("code")
    name = req.get("name") or "Unknown"
    try:
        conn = get_connection()
        cur = conn.cursor()
        if name == "Unknown":
            cur.execute("SELECT name FROM master_info WHERE code = ?", (symbol,))
            n_row = cur.fetchone()
            if n_row: name = n_row[0]
        
        cur.execute("SELECT entry_price FROM trade_plan WHERE code = ? ORDER BY date DESC, id DESC LIMIT 1", (symbol,))
        row = cur.fetchone()
        entry_price = int(row[0]) if row else 0
        
        cur.execute("""
            UPDATE trade_plan SET status = 'MONITORING' 
            WHERE id = (SELECT id FROM trade_plan WHERE code = ? ORDER BY date DESC, id DESC LIMIT 1)
        """, (symbol,))
        conn.commit()
        conn.close()

        now = datetime.now()
        hm = now.hour * 100 + now.minute
        is_weekend = now.weekday() >= 5
        msg = f"{name} {entry_price:,}원 실시간 감시 예약 완료!"
        if is_weekend or hm < 900 or hm >= 1520:
            msg = f"{name} 내일 아침(09:00) 자동 감시 예약 완료!"
        return {"status": "success", "message": msg}
    except Exception as e:
        return {"status": "error", "message": str(e)}
