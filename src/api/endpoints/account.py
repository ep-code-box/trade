from fastapi import APIRouter
import os
import requests
from datetime import datetime
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, MODE, load_config_from_db

router = APIRouter(tags=["account"])

@router.get("/account")
async def get_account_summary():
    """계좌 요약 (KIS API 실시간 연동)"""
    # DB 설정 로드
    db_conf = {}
    try:
        db_conf = load_config_from_db()
    except:
        pass

    cano = db_conf.get("KIS_CANO") or os.getenv("CANO")
    acnt_prdt_cd = db_conf.get("KIS_ACNT_PRDT_CD") or os.getenv("ACNT_PRDT_CD", "01")

    # 설정 없으면 모의 데이터 반환
    if not cano:
        return {
            "totalAsset": 50000000,
            "cash": 15000000,
            "totalProfit": 2450000,
            "totalProfitRate": 5.2,
            "buyingPower": 35000000,
            "riskPerTradePercent": 1.0,
            "positions": [] 
        }

    try:
        token = get_access_token()
        if not token:
            raise Exception("Token generation failed")

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

        if data.get('rt_cd') != '0':
            return {"totalAsset": 0, "cash": 0, "positions": [], "error": data.get('msg1')}

        output1 = data.get('output1', [])
        output2 = data.get('output2', [])
        summary = output2[0] if output2 else {}
        
        total_asset = int(summary.get('tot_evlu_amt', 0) or 0)
        total_profit = int(summary.get('evlu_pfls_smtl_amt', 0) or 0)
        cash = int(summary.get('dnca_tot_amt', 0) or 0)
        
        total_profit_rate = 0.0
        invested = total_asset - total_profit
        if invested > 0:
            total_profit_rate = round((total_profit / invested) * 100, 2)

        # [v5.9] DB에서 종목 정보(섹터, RS 등) 가져오기
        import sqlite3
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

                # [v5.9] 올바른 테이블명과 컬럼명으로 정보 조회
                sector = "기타"
                rs_score = 50
                try:
                    cur.execute("""
                        SELECT s.category_name 
                        FROM sectors_themes s 
                        WHERE s.code = ? AND s.category_type = 'sector' 
                        LIMIT 1
                    """, (symbol,))
                    row = cur.fetchone()
                    if row: sector = row['category_name']

                    cur.execute("""
                        SELECT rs_score FROM daily_analysis 
                        WHERE code = ? 
                        ORDER BY date DESC LIMIT 1
                    """, (symbol,))
                    row = cur.fetchone()
                    if row: rs_score = row['rs_score']
                except:
                    pass # DB 조회 실패해도 계속 진행
                
                avg_price = float(item.get('pchs_avg_pric', 0) or 0)
                curr_price = int(item.get('prpr', 0) or 0)
                profit_rate = float(item.get('evlu_pfls_rt', 0) or 0)
                
                # RS 트렌드 결정 (점수 기준)
                rs_trend = 'rising' if rs_score >= 80 else 'flat'
                vitality = int(rs_score)
                curr_eval_amount = curr_price * qty

                positions.append({
                    "symbol": symbol,
                    "name": item.get('prdt_name'),
                    "quantity": qty,
                    "currentPrice": curr_price,
                    "avgPrice": avg_price,
                    "profitRate": profit_rate,
                    "profit": int(item.get('evlu_pfls_amt', 0) or 0),
                    "evalAmount": curr_eval_amount, # 비중 계산용 추가
                    "status": "HEALTHY" if profit_rate > -3 else "CAUTION",
                    "sector": sector,
                    "initialStopLoss": int(avg_price * 0.95),
                    "trailingStop": int(curr_price * 0.92),
                    "breakEvenPrice": int(avg_price),
                    "targetPrice": int(avg_price * 1.2),
                    "daysHeld": 1, 
                    "rsTrend": rs_trend,
                    "vitalityScore": vitality,
                    "entryDate": datetime.now().strftime('%Y-%m-%d')
                })
            conn.close()
        except Exception as db_e:
            print(f"DB Enrichment Error: {db_e}")

        return {
            "totalAsset": total_asset,
            "cash": cash,
            "totalProfit": total_profit,
            "totalProfitRate": total_profit_rate,
            "buyingPower": cash,
            "riskPerTradePercent": 1.0,
            "maxRiskAmount": int(total_asset * 0.01),
            "positions": positions
        }
    except Exception as e:
        return {"totalAsset": 0, "cash": 0, "positions": [], "error": str(e)}
