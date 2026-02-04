from fastapi import APIRouter
import os
import requests
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, MODE, load_config_from_db

router = APIRouter(tags=["account"])

class ShieldUpdate(BaseModel):
    symbol: str
    price: int

@router.get("/account")
async def get_account_summary():
    """계좌 요약 (KIS API 실시간 연동 + DB 감사 데이터 매칭)"""
    db_conf = {}
    try:
        db_conf = load_config_from_db()
    except: pass

    cano = db_conf.get("KIS_CANO") or os.getenv("CANO")
    acnt_prdt_cd = db_conf.get("KIS_ACNT_PRDT_CD") or os.getenv("ACNT_PRDT_CD", "01")

    if not cano: return {"error": "Configuration missing"}

    try:
        token = get_access_token()
        tr_id = "TTTC8434R" if MODE == "real" else "VTTC8434R"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "CANO": cano, "ACNT_PRDT_CD": acnt_prdt_cd, "AFHR_FLPR_YN": "N",
            "OFL_YN": "N", "INQR_DVSN": "02", "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N", "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00", "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""
        }

        res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance", headers=headers, params=params, timeout=10)
        data = res.json()
        if data.get('rt_cd') != '0': return {"error": data.get('msg1')}

        output1, output2 = data.get('output1', []), data.get('output2', [])
        summary = output2[0] if output2 else {}
        total_asset = int(summary.get('tot_evlu_amt', 0) or 0)
        total_profit = int(summary.get('evlu_pfls_smtl_amt', 0) or 0)
        cash = int(summary.get('dnca_tot_amt', 0) or 0)

        DB_PATH = "TrendHunter/db/stock_info.db"
        positions = []
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            for item in output1:
                symbol = item.get('pdno')
                qty = int(item.get('hldg_qty', 0) or 0)
                if qty <= 0: continue

                sector, rs_score, manual_shield = "기타", 50, None
                try:
                    # 1. 섹터 조회
                    cur.execute("SELECT category_name FROM sectors_themes WHERE code = ? LIMIT 1", (symbol,))
                    row = cur.fetchone()
                    if row: sector = row['category_name']

                    # 2. RS 점수 조회
                    cur.execute("SELECT rs_score FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
                    row = cur.fetchone()
                    if row: rs_score = row['rs_score']

                    # 3. Shield 조회 (수동 테이블 -> 계획 테이블 순서)
                    cur.execute("SELECT manual_shield FROM account_positions_audit WHERE symbol = ?", (symbol,))
                    row = cur.fetchone()
                    if row and row['manual_shield']:
                        manual_shield = int(row['manual_shield'])
                    else:
                        # 계획 테이블(trade_plan)에서 stop_price 조회
                        cur.execute("SELECT stop_price FROM trade_plan WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
                        row = cur.fetchone()
                        if row: manual_shield = int(row['stop_price'])
                except: pass
                
                avg_price = float(item.get('pchs_avg_pric', 0) or 0)
                curr_price = int(item.get('prpr', 0) or 0)
                
                # Shield 결정: DB 값이 최우선 (28,000원 적용 지점)
                sl = manual_shield if manual_shield else int(avg_price * 0.95)

                positions.append({
                    "symbol": symbol, "name": item.get('prdt_name'), "quantity": qty,
                    "currentPrice": curr_price, "avgPrice": avg_price,
                    "profitRate": float(item.get('evlu_pfls_rt', 0) or 0),
                    "profit": int(item.get('evlu_pfls_amt', 0) or 0),
                    "status": "HEALTHY" if curr_price >= sl else "VIOLATED",
                    "sector": sector, "trailingStop": sl, "manualShield": manual_shield,
                    "vitalityScore": int(rs_score), "rsTrend": 'rising' if rs_score >= 80 else 'flat',
                    "entryDate": datetime.now().strftime('%Y-%m-%d')
                })
            conn.close()
        except: pass

        # 이번 주 실현 손익 조회
        from datetime import timedelta
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        realized_profit = 0
        if MODE == "real":
            try:
                r_headers = headers.copy()
                r_headers["tr_id"] = "TTTC8715R"
                r_params = {
                    "CANO": cano, "ACNT_PRDT_CD": acnt_prdt_cd,
                    "INQR_STRT_DT": monday.strftime('%Y%m%d'), "INQR_END_DT": today.strftime('%Y%m%d'),
                    "SLL_BUY_DVSN_CD": "00", "INQR_DVSN": "00", "PDNO": "", "SORT_DVSN": "01", "CBLC_DVSN": "00",
                    "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""
                }
                r_res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-period-trade-profit", headers=r_headers, params=r_params, timeout=10)
                r_data = r_res.json()
                if r_data.get('rt_cd') == '0':
                    realized_profit = int(r_data.get('output2', {}).get('tot_rlzt_pfls', 0))
            except: pass

        return {
            "totalAsset": total_asset, "cash": cash, "totalProfit": total_profit,
            "realizedPL": realized_profit, "maxRiskAmount": int(total_asset * 0.01), "positions": positions
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/account/shield")
async def update_manual_shield(data: ShieldUpdate):
    """특정 종목의 수동 쉴드(감시가) 업데이트"""
    try:
        DB_PATH = "TrendHunter/db/stock_info.db"
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO account_positions_audit (symbol, manual_shield, updated_at)
            VALUES (?, ?, datetime('now', 'localtime'))
        """, (data.symbol, data.price))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
