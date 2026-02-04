from fastapi import APIRouter
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.api.utils import get_db_row_dict

router = APIRouter(tags=["stocks"])

@router.get("/plan")
def get_trade_plan():
    """오늘의 매매 계획 리스트 반환"""
    query = "SELECT * FROM trade_plan WHERE date = (SELECT MAX(date) FROM trade_plan) ORDER BY id DESC"
    return get_db_row_dict(query)

@router.get("/summary")
def get_market_summary():
    """시장 전체 분석 요약 정보 반환"""
    try:
        conn = get_connection()
        query = "SELECT * FROM market_summary ORDER BY date DESC LIMIT 1"
        res = conn.execute(query).fetchone()
        conn.close()
        if not res: return {"error": "No summary data found"}
        return {
            "stage2Ratio": res[3], "activeLeaders": res[2], "marketRS": res[4],
            "topSector": res[1], "riskLevel": res[5], "lastSync": res[0]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/dates")
def get_available_dates():
    """사용 가능한 리포트 날짜 목록 반환"""
    conn = get_connection()
    dates = [row[0] for row in conn.execute("SELECT DISTINCT date FROM trade_plan ORDER BY date DESC").fetchall()]
    conn.close()
    return dates

@router.get("/stocks")
def get_stock_analysis(date: str = None):
    """스크리너 결과 반환"""
    try:
        conn = get_connection()
        if not date:
            date = conn.execute("SELECT MAX(date) FROM trade_plan").fetchone()[0]
            
        query = """
            SELECT 
                t.date, t.code as symbol, t.name, t.track, t.rs_score as rsScore, t.vcp_ratio as vcpRatio,
                t.entry_price as price, t.stop_price as stopLossPrice, t.weight, t.rationale,
                d.close as curr_price, d.open, d.high_52w, d.dividend_yield as dividendYield,
                m.roe, m.bsop_prfi, m.thtr_ntin, m.sale_account
            FROM trade_plan t
            LEFT JOIN (SELECT * FROM daily_analysis WHERE date = ?) d ON t.code = d.code
            LEFT JOIN master_info m ON t.code = m.code
            WHERE t.date = ?
            ORDER BY t.rs_score DESC
        """
        df = pd.read_sql_query(query, conn, params=(date, date))
        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
        conn.close()

        results = []
        for _, row in df.iterrows():
            curr = float(row['curr_price'] or row['price'] or 0)
            oprc = float(row['open'] or curr or 0)
            bsop = float(row['bsop_prfi'] or 0)
            sales = float(row['sale_account'] or 0)
            op_margin = round((bsop / sales * 100), 1) if sales > 0 else 0

            results.append({
                "date": str(row['date']), "symbol": str(row['symbol']), "name": str(row['name']),
                "price": int(curr), "change": round(((curr - oprc) / oprc * 100), 2) if oprc > 0 else 0,
                "rsScore": float(row['rsScore'] or 0), "vcpRatio": float(row['vcpRatio'] or 0),
                "track": str(row['track']), "dividendYield": float(row['dividendYield'] or 0),
                "roe": round(float(row['roe'] or 0), 1), "opMargin": op_margin,
                "isStage2": 1, "sector": str(row['track']).split("(")[-1].replace(")", "") if "(" in str(row['track']) else "기타",
                "volumeDryUp": float(row['vcpRatio'] or 1.0) < 0.5,
                "targetPrice": int(row['price'] or 0), "stopLossPrice": int(row['stopLossPrice'] or 0),
                "rationale": [str(row['rationale'])], "weight": str(row['weight']),
                "template": { "priceAbove50": True, "sma200TrendingUp": True, "rsAbove70": True }
            })
        return results
    except Exception as e:
        return []

@router.get("/stocks/{code}/history")
def get_stock_history(code: str):
    """특정 종목의 최근 100일치 시세 및 SMA 21 반환"""
    conn = get_connection()
    query = "SELECT date, open, high, low, close, volume, sma_50, sma_150, sma_200 FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 150"
    df = pd.read_sql_query(query, conn, params=(code,))
    if df.empty: return []
    
    curr_price = df.iloc[0]['close']
    df['close'] = df['close'].apply(lambda x: curr_price if x > curr_price * 10 else x)
    # [v5.7] 기관 수급선 SMA 21 실시간 계산
    df = df.sort_values('date')
    df['sma_21'] = df['close'].rolling(window=21).mean()
    
    # NaN/Inf 처리 (JSON 직렬화 에러 방지)
    df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
    
    # 다시 최근 100개만 자름
    df = df.iloc[-100:]
    
    conn.close()
    return df.to_dict(orient="records")
