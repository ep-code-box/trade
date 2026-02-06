from fastapi import APIRouter, HTTPException
import sqlite3
import os
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.kis_api import register_auto_order, register_reserved_order, place_stop_order
from src.account import get_account_balance
from src.auth import load_config_from_db
from src.analysis.screen_market import get_tick_size, adjust_to_tick, get_breakout_price

router = APIRouter(tags=["basket"])

@router.get("/basket")
def get_basket():
    try:
        conn = get_connection()
        res = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()
        latest_date = res[0] if res else None
        
        res_plan = conn.execute("SELECT MAX(date) FROM trade_plan").fetchone()
        plan_date = res_plan[0] if res_plan else None

        # [Step 1 고정] 각 종목별로 오늘 날짜의 여러 계획 중 최저 진입가(Step 1) 행만 골라냄
        query = """
            SELECT 
                b.symbol, b.name,
                d.close as price, d.open, d.rs_score as rsScore, 
                d.high_52w, d.low_52w, d.dividend_yield as dividendYield,
                d.sma_20, d.sma_50, d.sma_150, d.sma_200, d.vol_std_10d, d.vol_std_50d,
                m.roe, m.bsop_prfi, m.thtr_ntin, m.sale_account, m.market_type,
                t.entry_price as targetPrice, t.stop_price as stopLossPrice, 
                t.pivot_price, t.profit_target, t.track, t.rationale
            FROM basket b
            LEFT JOIN daily_analysis d ON b.symbol = d.code AND d.date = ?
            LEFT JOIN master_info m ON b.symbol = m.code
            LEFT JOIN (
                SELECT * FROM (
                    SELECT *, ROW_NUMBER() OVER (PARTITION BY code ORDER BY entry_price ASC) as rn
                    FROM trade_plan 
                    WHERE date = ?
                ) WHERE rn = 1
            ) t ON b.symbol = t.code
        """
        df = pd.read_sql_query(query, conn, params=(latest_date, plan_date))
        conn.close()

        numeric_cols = [
            'price', 'open', 'rsScore', 'high_52w', 'low_52w', 'dividendYield',
            'sma_20', 'sma_50', 'sma_150', 'sma_200', 'vol_std_10d', 'vol_std_50d',
            'roe', 'bsop_prfi', 'thtr_ntin', 'sale_account', 
            'targetPrice', 'stopLossPrice', 'pivot_price', 'profit_target'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        results = []
        for _, row in df.iterrows():
            symbol = str(row['symbol'])
            name = str(row['name'])
            curr = float(row['price'])
            oprc = float(row['open'] or curr or 0)
            
            target = float(row['targetPrice'])
            stop = float(row['stopLossPrice'])
            pivot = float(row['pivot_price'])
            profit = float(row['profit_target'])
            
            if target == 0 or pivot == 0 or profit == 0:
                h52 = float(row['high_52w'] or 0)
                if h52 > 0:
                    calc_target = get_breakout_price(h52)
                    if target == 0: target = calc_target
                    if stop == 0: stop = adjust_to_tick(target * 0.93, 'down')
                    if pivot == 0: pivot = adjust_to_tick(h52 * 1.002, 'up')
                    if profit == 0: profit = adjust_to_tick(target * 1.15, 'up')
                else:
                    if target == 0: target = curr
                    if stop == 0: stop = adjust_to_tick(curr * 0.93, 'down')
                    if pivot == 0: pivot = curr
                    if profit == 0: profit = adjust_to_tick(curr * 1.15, 'up')

            if pivot == 0: pivot = int(target * 0.98)
            if profit == 0: profit = int(target * 1.15)

            vcp_ratio = 0
            if row['vol_std_50d'] > 0:
                vcp_ratio = round(float(row['vol_std_10d'] / row['vol_std_50d']), 2)

            results.append({
                "symbol": symbol,
                "name": name,
                "price": int(curr),
                "change": round(((curr - oprc) / oprc * 100), 2) if oprc > 0 else 0,
                "rsScore": float(row['rsScore']),
                "vcpRatio": vcp_ratio,
                "track": str(row['track'] or "Explorer"),
                "dividendYield": float(row['dividendYield']),
                "roe": round(float(row['roe']), 1),
                "isStage2": 1,
                "sector": str(row['market_type'] or "기타"),
                "volumeDryUp": False,
                "targetPrice": int(target),
                "stopLossPrice": int(stop),
                "pivotPrice": int(pivot),
                "profitTarget": int(profit),
                "rationale": [str(row['rationale'] or "익스플로러 탐색 종목")],
                "template": {
                    "priceAbove50": curr > (row['sma_50']),
                    "sma200TrendingUp": True,
                    "rsAbove70": (row['rsScore']) >= 70
                }
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

@router.delete("/basket/{symbol}")
def remove_from_basket(symbol: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM basket WHERE symbol = ?", (symbol,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@router.post("/order/buy")
async def place_buy_order(req: dict):
    symbol = req.get("symbol") or req.get("code")
    name = req.get("name") or "Unknown"
    try:
        config = load_config_from_db()
        cano = config.get("KIS_CANO")
        conn = get_connection()
        cur = conn.cursor()
        
        # [이름 보정] Unknown으로 오면 DB에서 이름을 찾아옴
        if name == "Unknown":
            cur.execute("SELECT name FROM master_info WHERE code = ?", (symbol,))
            n_row = cur.fetchone()
            if n_row: name = n_row[0]
        
        # [정밀 교정] 최초 진입가(Step 1) 행을 정확히 매칭하여 가져옴
        cur.execute("""
            SELECT entry_price, stop_price 
            FROM trade_plan 
            WHERE code = ? AND date = (SELECT MAX(date) FROM trade_plan WHERE code = ?)
            ORDER BY entry_price ASC LIMIT 1
        """, (symbol, symbol))
        row = cur.fetchone()
        entry_price, stop_price = 0, 0
        if row: 
            entry_price = int(row[0])
            stop_price = int(row[1])
        else:
            cur.execute("SELECT high_52w, close FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
            d_row = cur.fetchone()
            if d_row: 
                entry_price = get_breakout_price(d_row[0]) if d_row[0] > 0 else d_row[1]
                stop_price = int(entry_price * 0.93) # 기본 7% 손절
        conn.close()
        
        balance = get_account_balance()
        qty = max(1, int((balance['summary']['total_asset'] * 0.1) / entry_price))
        
        # [TrendHunter Policy] 1. 장 중(09:00~15:30): 스탑(Breakout) 주문 사용 / 2. 장 외: 예약(Reserved) 주문 사용
        now = datetime.now()
        is_market_open = (now.hour > 9 or (now.hour == 9 and now.minute >= 0)) and (now.hour < 15 or (now.hour == 15 and now.minute <= 30))
        if now.weekday() >= 5: is_market_open = False

        if is_market_open:
            # 1단계: 매수 스탑 등록
            res_buy = await place_stop_order(symbol, qty=qty, stop_price=entry_price, side="BUY", cano=cano)
            if res_buy and res_buy.get('rt_cd') == '0':
                # 2단계: 성공 시 매도(손절) 스탑도 서버에 즉시 등록 (동시 감시)
                if stop_price > 0:
                    await place_stop_order(symbol, qty=qty, stop_price=stop_price, side="SELL", cano=cano)
                return {"status": "success", "message": f"{name} {entry_price}원 돌파 매수 & {stop_price}원 손절 감시 등록 완료!"}
            res = res_buy
            mode_name = "실시간 감시"
        else:
            # 장 외 시간일 경우 예약 주문으로 등록
            res = await register_reserved_order(symbol, side="BUY", price=entry_price, qty=qty, cano=cano)
            mode_name = "예약"
        
        if res and res.get('rt_cd') == '0':
            return {"status": "success", "message": f"{name} {entry_price}원 {mode_name} 등록 완료! (조건 도달 시 자동 매수)"}
        else:
            err_msg = res.get('msg1') or res.get('error') or "알 수 없는 오류"
            return {"status": "error", "message": f"{mode_name} 실패: {err_msg}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
