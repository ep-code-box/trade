from fastapi import APIRouter, HTTPException
import sqlite3
import os
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.kis_api import place_order_cash, get_current_price_async
from src.account import get_account_balance
from src.utils.notifier import notifier
from src.auth import load_config_from_db
from src.analysis.screen_market import get_tick_size, adjust_to_tick, get_breakout_price

router = APIRouter(tags=["basket"])

@router.get("/basket")
def get_basket():
    """바구니(매수대기) + 보유종목(매도감시) 통합 조회 (v25.34)"""
    try:
        conn = get_connection()
        # [v25.34] Ultra-Stable Query with Real-time P/L support
        query = """
            WITH target_symbols AS (
                SELECT symbol FROM account_positions_audit WHERE qty > 0
                UNION
                SELECT code as symbol FROM trade_plan WHERE status = 'MONITORING'
                UNION
                SELECT symbol FROM basket
            ),
            latest_plan AS (
                SELECT code, name, entry_price, stop_price, status,
                       ROW_NUMBER() OVER (PARTITION BY code ORDER BY (CASE WHEN status = 'MONITORING' THEN 0 ELSE 1 END), date DESC, id DESC) as rn
                FROM trade_plan
            ),
            latest_price AS (
                SELECT code, close, ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) as rn
                FROM daily_analysis
            )
            SELECT 
                s.symbol,
                COALESCE(NULLIF(m.name, ''), s.symbol) as official_name,
                COALESCE(NULLIF(p.name, ''), '') as plan_name,
                COALESCE(NULLIF(b.name, ''), '') as basket_name,
                COALESCE(a.qty, 0) as current_qty,
                COALESCE(a.entry_price, 0) as avgPrice,
                COALESCE(p.entry_price, b.target_price, 0) as targetPrice,
                COALESCE(a.manual_shield, p.stop_price, b.stop_price, 0) as stopLossPrice,
                COALESCE(pr.close, 0) as price,
                COALESCE(p.status, 'READY') as plan_status
            FROM target_symbols s
            LEFT JOIN master_info m ON TRIM(s.symbol) = TRIM(m.code)
            LEFT JOIN account_positions_audit a ON TRIM(s.symbol) = TRIM(a.symbol)
            LEFT JOIN basket b ON TRIM(s.symbol) = TRIM(b.symbol)
            LEFT JOIN latest_plan p ON TRIM(s.symbol) = TRIM(p.code) AND p.rn = 1
            LEFT JOIN latest_price pr ON TRIM(s.symbol) = TRIM(pr.code) AND pr.rn = 1
            WHERE s.symbol IS NOT NULL
            ORDER BY (CASE WHEN COALESCE(a.qty, 0) > 0 THEN 0 WHEN COALESCE(p.status, '') = 'MONITORING' THEN 1 ELSE 2 END) ASC
        """
        
        df = pd.read_sql_query(query, conn)
        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
        df = df.drop_duplicates(subset=['symbol'])
        
        # 하드코딩 매핑 (최종 방어선)
        MASTER_MAP = {"015760": "한국전력", "034020": "두산에너빌리티", "005930": "삼성전자", "000660": "SK하이닉스"}
        
        total_asset = 0
        try:
            balance = get_account_balance()
            if balance and 'summary' in balance:
                total_asset = int(balance['summary'].get('total_asset', 0))
        except: pass

        results = []
        for _, row in df.iterrows():
            symbol = str(row['symbol']).strip()
            
            # 1. 이름 결정
            final_name = MASTER_MAP.get(symbol)
            if not final_name:
                official = str(row['official_name'])
                plan = str(row['plan_name'])
                basket_n = str(row['basket_name'])
                final_name = official
                if official == symbol or official.isdigit():
                    if plan and not plan.isdigit(): final_name = plan
                    elif basket_n and not basket_n.isdigit(): final_name = basket_n
            
            # 2. 수치 데이터
            qty = int(row['current_qty'] or 0)
            curr_price = int(row['price'] or 0)
            avg_price = float(row['avgPrice'] or 0)
            target = float(row['targetPrice'] or 0)
            stop = float(row['stopLossPrice'] or 0)
            
            # 3. 계산
            profit = int((curr_price - avg_price) * qty) if qty > 0 else 0
            profit_rate = round(((curr_price - avg_price) / avg_price * 100), 2) if avg_price > 0 else 0
            dist_to_target = round(((curr_price - target) / target * 100), 2) if target > 0 else 0
            
            # 상태 결정
            if qty > 0: status = 'BOUGHT'
            elif str(row['plan_status']) == 'MONITORING': status = 'MONITORING'
            else: status = 'READY'
            
            if target == 0: target = curr_price
            if stop == 0 and target > 0: stop = int(target * 0.93)
            
            results.append({
                "symbol": symbol, "name": final_name, "price": int(curr_price),
                "avgPrice": int(avg_price), "profit": profit, "profitRate": profit_rate,
                "targetPrice": int(target), "distToTarget": dist_to_target,
                "stopLossPrice": int(stop), "status": status, "recommendedQty": int(qty or 1),
                "estimatedAmount": int((qty or 1) * (target if status != 'BOUGHT' else curr_price))
            })
        
        conn.close()
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/basket")
def add_to_basket(item: dict):
    conn = get_connection()
    cur = conn.cursor()
    target = item.get('targetPrice', 0)
    stop = item.get('stopLossPrice', 0)
    try:
        cur.execute("INSERT OR REPLACE INTO basket (symbol, name, target_price, stop_price) VALUES (?, ?, ?, ?)", 
                    (item['symbol'], item['name'], target, stop))
    except:
        cur.execute("INSERT OR REPLACE INTO basket (symbol, name) VALUES (?, ?)", (item['symbol'], item['name']))
    conn.commit(); conn.close()
    return {"status": "success"}

@router.post("/order/cancel")
async def cancel_monitoring(req: dict):
    symbol = req.get("symbol") or req.get("code")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE trade_plan SET status = 'READY' WHERE code = ? AND status = 'MONITORING'", (symbol,))
        conn.commit(); conn.close()
        return {"status": "success", "message": "실시간 감시가 중단되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.delete("/basket/{symbol}")
def remove_from_basket(symbol: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM basket WHERE symbol = ?", (symbol,))
    cur.execute("UPDATE trade_plan SET status = 'READY' WHERE code = ? AND status = 'MONITORING'", (symbol,))
    conn.commit(); conn.close()
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
        
        cur.execute("SELECT entry_price, stop_price FROM trade_plan WHERE code = ? ORDER BY date DESC, id DESC LIMIT 1", (symbol,))
        row = cur.fetchone()
        target_date = datetime.now().strftime('%Y%m%d')
        
        if not row:
            cur.execute("SELECT target_price, stop_price FROM basket WHERE symbol = ?", (symbol,))
            b_row = cur.fetchone()
            entry_price = b_row[0] if b_row and b_row[0] else 0
            stop_price = b_row[1] if b_row and b_row[1] else 0
            if entry_price == 0:
                cur.execute("SELECT close FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
                p_row = cur.fetchone()
                if p_row: entry_price = p_row[0]
            if stop_price == 0 and entry_price > 0: stop_price = int(entry_price * 0.93)
            cur.execute("INSERT INTO trade_plan (date, code, name, track, entry_price, stop_price, status, rationale) VALUES (?, ?, ?, 'MANUAL', ?, ?, 'MONITORING', 'Explorer 수동 등록')", (target_date, symbol, name, entry_price, stop_price))
        else:
            cur.execute("UPDATE trade_plan SET status = 'MONITORING', date = ? WHERE id = (SELECT id FROM trade_plan WHERE code = ? ORDER BY date DESC, id DESC LIMIT 1)", (target_date, symbol))
        conn.commit(); conn.close()
        
        now = datetime.now(); hm = now.hour * 100 + now.minute
        if now.weekday() < 5 and 900 <= hm < 1520:
            curr_price = await get_current_price_async(symbol)
            if curr_price and curr_price >= entry_price:
                qty = 1
                try:
                    balance = get_account_balance()
                    if balance and 'summary' in balance:
                        qty = max(1, int((balance['summary']['total_asset'] * 0.1) / curr_price))
                except: pass
                res = await place_order_cash(symbol, qty=qty, price=0, side="BUY", ord_dvsn="01")
                if res and res.get('rt_cd') == '0':
                    notifier.send_message(f"🎯 [즉시 매수 완료] {name}\n현재가({curr_price:,}원)가 목표가 이상입니다.")
                    return {"status": "success", "message": f"{name} 현재가 즉시 매수 완료!"}
        return {"status": "success", "message": f"{name} 실시간 감시 예약 완료!"}
    except Exception as e:
        return {"error": str(e), "message": str(e)}
