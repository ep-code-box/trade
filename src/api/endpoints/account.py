from fastapi import APIRouter
import os
import requests
import sqlite3
from datetime import datetime, timedelta
from pydantic import BaseModel
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, MODE, load_config_from_db

router = APIRouter(tags=["account"])

class ShieldUpdate(BaseModel):
    symbol: str
    price: int

async def fetch_net_investment(tk, cano, acnt_prdt_cd):

    """연속 조회를 통해 최근 1년 모든 입출금 내역을 합산"""

    end_date = datetime.now().strftime('%Y%m%d')

    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

    

    tr_id = "CTSC9115R" if MODE == "real" else "VTSC9115R"

    headers = {

        "content-type": "application/json; charset=utf-8",

        "authorization": f"Bearer {tk}",

        "appkey": APP_KEY, "appsecret": APP_SECRET,

        "tr_id": tr_id, "custtype": "P"

    }

    

    net_amount = 0

    ctx_fk = ""

    ctx_nk = ""

    

    for _ in range(10):

        params = {

            "CANO": cano, "ACNT_PRDT_CD": acnt_prdt_cd,

            "INQR_STRT_DT": start_date, "INQR_END_DT": end_date,

            "SLL_BUY_DVSN_CD": "00", "INQR_DVSN": "00", "PDNO": "", "CCLD_DVSN": "00",

            "ORD_GNO_BRNO": "", "ODNO": "", "INQR_DVSN_3": "01", "INQR_DVSN_1": "",

            "CTX_AREA_FK100": ctx_fk, "CTX_AREA_NK100": ctx_nk

        }

        

        try:

            res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-daily-ccld", headers=headers, params=params, timeout=10)

            data = res.json()

            if data.get('rt_cd') == '0':

                for item in data.get('output1', []):

                    name = item.get('sll_buy_dvsn_cd_name', '')

                    amt = int(item.get('tot_ccld_amt', 0) or 0)

                    pdno = item.get('pdno', '').strip()

                    

                    is_deposit = any(k in name for k in ["입금", "입고", "수탁", "대체"])

                    is_withdrawal = any(k in name for k in ["출금", "출고", "이체"])

                    

                    if not pdno and not is_deposit and not is_withdrawal:

                        if amt > 0: is_deposit = True 



                    if is_deposit: net_amount += amt

                    elif is_withdrawal: net_amount -= amt

                

                ctx_fk = data.get('ctx_area_fk100', "").strip()

                ctx_nk = data.get('ctx_area_nk100', "").strip()

                if not ctx_fk and not ctx_nk: break

                if data.get('tr_cont') not in ['F', 'M']: break

            else:

                break

        except:

            break

            

    return net_amount





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
        if not token:
            return {"error": "Failed to obtain KIS access token. Check APP_KEY/APP_SECRET."}
            
        def fetch_balance(tk):
            tr_id = "TTTC8434R" if MODE == "real" else "VTTC8434R"
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {tk}",
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
            return requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance", headers=headers, params=params, timeout=10)

        # [v14.9] 공용 헤더 정의 (하위 API에서 사용)
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": APP_KEY, "appsecret": APP_SECRET,
            "custtype": "P"
        }

        res = fetch_balance(token)
        data = res.json()

        # [v14.3] 토큰 만료 시 1회 강제 갱신 후 재시도
        if data.get('msg_cd') == 'EGW00123' or '만료된 token' in data.get('msg1', ''):
            print("🔄 Detected expired token. Retrying with fresh token...")
            token = get_access_token(force_refresh=True)
            res = fetch_balance(token)
            data = res.json()

        if data.get('rt_cd') != '0': 
            print(f"KIS API Error: {data.get('msg1')} ({data.get('msg_cd')})")
            return {"error": f"KIS API Error: {data.get('msg1')}"}

        output1, output2 = data.get('output1', []), data.get('output2', [])
        if not output2:
            return {"error": "KIS API returned empty summary data (output2)."}
            
        summary = output2[0]
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

                sector, rs_score, manual_shield, highest_price = "기타", 50, None, 0
                try:
                    # 1. 섹터 조회
                    cur.execute("SELECT category_name FROM sectors_themes WHERE code = ? LIMIT 1", (symbol,))
                    row = cur.fetchone()
                    if row: sector = row['category_name']

                    # 2. RS 점수 조회
                    cur.execute("SELECT rs_score FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
                    row = cur.fetchone()
                    if row: rs_score = row['rs_score']

                    # 3. Shield 및 최고가 조회 (봇이 업데이트한 트레일링 스탑 포함)
                    cur.execute("SELECT manual_shield, highest_price FROM account_positions_audit WHERE symbol = ?", (symbol,))
                    row = cur.fetchone()
                    if row:
                        manual_shield = int(row['manual_shield']) if row['manual_shield'] else None
                        highest_price = int(row['highest_price']) if row['highest_price'] else 0
                    
                    if not manual_shield:
                        # 계획 테이블(trade_plan)에서 기본 stop_price 조회
                        cur.execute("SELECT stop_price FROM trade_plan WHERE code = ? ORDER BY date DESC LIMIT 1", (symbol,))
                        row = cur.fetchone()
                        if row: manual_shield = int(row['stop_price'])
                except Exception as db_e:
                    print(f"Database query error for {symbol}: {db_e}")
                
                avg_price = float(item.get('pchs_avg_pric', 0) or 0)
                curr_price = int(item.get('prpr', 0) or 0)
                
                # Shield 결정: DB 값이 최우선
                sl = manual_shield if manual_shield else int(avg_price * 0.95)

                positions.append({
                    "symbol": symbol, "name": item.get('prdt_name'), "quantity": qty,
                    "currentPrice": curr_price, "avgPrice": avg_price,
                    "profitRate": float(item.get('evlu_pfls_rt', 0) or 0),
                    "profit": int(item.get('evlu_pfls_amt', 0) or 0),
                    "status": "HEALTHY" if curr_price >= sl else "VIOLATED",
                    "sector": sector, "trailingStop": sl, "manualShield": manual_shield,
                    "highestPrice": highest_price,
                    "vitalityScore": int(rs_score), "rsTrend": 'rising' if rs_score >= 80 else 'flat',
                    "entryDate": datetime.now().strftime('%Y-%m-%d')
                })
            conn.close()
        except Exception as conn_e:
            print(f"Database connection error: {conn_e}")

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

        # [v15.2] 수익금 전용 차트 엔진 (실현 손익 기반)
        unrealized_profit = total_profit 
        realized_profit_total = 0
        daily_stats = []
        
        try:
            # 최근 1년치 실현 손익 조회 (TTTC8715R)
            history_start_1y = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            h_headers = headers.copy()
            h_headers["tr_id"] = "TTTC8715R" if MODE == "real" else "VTTC8715R"
            
            h_params = {
                "CANO": cano, "ACNT_PRDT_CD": acnt_prdt_cd,
                "INQR_STRT_DT": history_start_1y, "INQR_END_DT": datetime.now().strftime('%Y%m%d'),
                "SLL_BUY_DVSN_CD": "00", "INQR_DVSN": "00", "PDNO": "", "SORT_DVSN": "02", 
                "CBLC_DVSN": "00", "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""
            }
            h_res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-period-trade-profit", headers=h_headers, params=h_params, timeout=10)
            h_data = h_res.json()
            
            if h_data.get('rt_cd') == '0':
                # 1. 누적 실현 손익 합산
                realized_profit_total = int(h_data.get('output2', {}).get('tot_rlzt_pfls', 0))
                
                # 2. 일별 실현 손익 추출 (최근 30일로 확장)
                temp_daily = {}
                chart_limit_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                
                for item in h_data.get('output1', []):
                    dt = item.get('trad_dt') # 거래 일자
                    # rlzt_pfls: 실현 손익 (매도 시 확정된 금액)
                    pft = int(item.get('rlzt_pfls', 0) or 0)
                    
                    if not dt or pft == 0: continue
                    if dt >= chart_limit_date:
                        temp_daily[dt] = temp_daily.get(dt, 0) + pft
                
                # 차트 데이터 정렬
                for d in sorted(temp_daily.keys()):
                    daily_stats.append({"date": f"{d[4:6]}/{d[6:8]}", "profit": temp_daily[d]})
            else:
                print(f"Profit API Error: {h_data.get('msg1')}")
        except Exception as e:
            print(f"Profit Aggregation Error: {e}")

        pure_profit = unrealized_profit + realized_profit_total
        net_investment = total_asset - pure_profit

        return {
            "totalAsset": total_asset, "cash": cash, "totalProfit": total_profit,
            "realizedPL": realized_profit, 
            "netInvestment": net_investment,
            "pureProfit": pure_profit,
            "dailyHistory": daily_stats,
            "maxRiskAmount": int(total_asset * 0.01), "positions": positions
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
