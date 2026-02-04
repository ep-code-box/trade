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

        positions = []
        for item in output1:
            qty = int(item.get('hldg_qty', 0) or 0)
            if qty > 0:
                avg_price = float(item.get('pchs_avg_pric', 0) or 0)
                positions.append({
                    "symbol": item.get('pdno'),
                    "name": item.get('prdt_name'),
                    "quantity": qty,
                    "currentPrice": int(item.get('prpr', 0) or 0),
                    "avgPrice": avg_price,
                    "profitRate": float(item.get('evlu_pfls_rt', 0) or 0),
                    "profit": int(item.get('evlu_pfls_amt', 0) or 0),
                    "status": "HEALTHY", "sector": "Unknown",
                    "initialStopLoss": int(avg_price * 0.9), "trailingStop": int(avg_price * 0.95),
                    "breakEvenPrice": int(avg_price), "targetPrice": int(avg_price * 1.2),
                    "daysHeld": 1, "rsTrend": "flat", "vitalityScore": 50,
                    "entryDate": datetime.now().strftime('%Y-%m-%d')
                })

        return {
            "totalAsset": total_asset, "cash": cash, "totalProfit": total_profit,
            "totalProfitRate": total_profit_rate, "buyingPower": cash,
            "riskPerTradePercent": 1.0, "positions": positions
        }
    except Exception as e:
        return {"totalAsset": 0, "cash": 0, "positions": [], "error": str(e)}
