from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import sqlite3
import os
from datetime import datetime
from collections import Counter
from src.db import get_connection

app = FastAPI(title="TrendHunter API Server")

# CORS 설정: 로컬 개발 환경(Vite 등)에서 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_row_dict(query, params=()):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

@app.get("/api/plan")
def get_trade_plan():
    """오늘의 매매 계획 리스트 반환"""
    today = datetime.now().strftime('%Y-%m-%d')
    # 가장 최근 날짜의 플랜을 가져옴
    query = """
        SELECT * FROM trade_plan 
        WHERE date = (SELECT MAX(date) FROM trade_plan)
        ORDER BY id DESC
    """
    return get_db_row_dict(query)

@app.get("/api/summary")
def get_market_summary():
    """시장 전체 분석 요약 정보 반환 (미리 계산된 테이블 활용)"""
    try:
        conn = get_connection()
        # 가장 최근 요약 정보 조회
        query = "SELECT * FROM market_summary ORDER BY date DESC LIMIT 1"
        res = conn.execute(query).fetchone()
        conn.close()
        
        if not res:
            return {"error": "No summary data found"}
            
        return {
            "stage2Ratio": res[3],
            "activeLeaders": res[2],
            "marketRS": res[4],
            "topSector": res[1],
            "riskLevel": res[5],
            "lastSync": res[0]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/stocks")
def get_stock_analysis():
    """스크리너 결과 반환"""
    try:
        conn = get_connection()
        query = """
            SELECT 
                t.code as symbol, t.name, t.track, t.rs_score as rsScore, t.vcp_ratio as vcpRatio,
                t.entry_price as price, t.stop_price as stopLossPrice, t.weight, t.rationale,
                d.close as curr_price, d.open, d.high_52w, d.dividend_yield as dividendYield,
                m.roe, m.bsop_prfi, m.thtr_ntin, m.sale_account, m.stck_fcam
            FROM trade_plan t
            LEFT JOIN (
                SELECT * FROM daily_analysis 
                WHERE date = (SELECT MAX(date) FROM daily_analysis)
            ) d ON t.code = d.code
            LEFT JOIN master_info m ON t.code = m.code
            WHERE t.date = (SELECT MAX(date) FROM trade_plan)
            ORDER BY t.rs_score DESC
        """
        df = pd.read_sql_query(query, conn)
        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
        conn.close()

        results = []
        for _, row in df.iterrows():
            try:
                curr = float(row['curr_price'] or row['price'] or 0)
                oprc = float(row['open'] or curr or 0)
                change_pct = round(((curr - oprc) / oprc * 100), 2) if oprc > 0 else 0
                
                bsop = float(row['bsop_prfi'] or 0)
                sales = float(row['sale_account'] or 0)
                op_margin = round((bsop / sales * 100), 1) if sales > 0 else 0
                
                # [v3.9] 현실적인 범위 제한 (데이터 오류 방지)
                if op_margin > 100 or op_margin < -100:
                    op_margin = 0

                results.append({
                    "symbol": str(row['symbol']),
                    "name": str(row['name']),
                    "price": int(curr),
                    "change": change_pct,
                    "rsScore": float(row['rsScore'] or 0),
                    "vcpRatio": float(row['vcpRatio'] or 0),
                    "track": str(row['track']),
                    "dividendYield": float(row['dividendYield'] or 0),
                    "roe": round(float(row['roe'] or 0), 1),
                    "opMargin": op_margin,
                    "isStage2": 1,
                    "sector": str(row['track']).split("(")[-1].replace(")", "") if "(" in str(row['track']) else "기타",
                    "volumeDryUp": float(row['vcpRatio'] or 1.0) < 0.5,
                    "targetPrice": int(row['price'] or 0),
                    "stopLossPrice": int(row['stopLossPrice'] or 0),
                    "rationale": [str(row['rationale'])],
                    "weight": str(row['weight']),
                    "atr": 0,
                    "volatility": 0,
                    "template": {
                        "priceAbove50": True, "priceAbove150_200": True, 
                        "sma150Above200": True, "sma50Above150_200": True,
                        "sma200TrendingUp": True, "above52wLow25": True, 
                        "within52wHigh25": True, "rsAbove70": True
                    }
                })
            except Exception as e:
                print(f"Row processing error: {e}")
                continue

        return results
    except Exception as e:
        print(f"Global API Error: {e}")
        return []


@app.get("/api/stocks/{code}/history")
def get_stock_history(code: str):
    """특정 종목의 최근 100일치 시세 및 이평선 데이터 반환 (차트용)"""
    conn = get_connection()
    query = """
        SELECT date, open, high, low, close, volume, sma_50, sma_150, sma_200
        FROM daily_analysis
        WHERE code = ?
        ORDER BY date DESC
        LIMIT 100
    """
    df = pd.read_sql_query(query, conn, params=(code,))
    df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
    
    # [v3.7] 수정주가 이슈 대응: 주가가 급격히 튀는 첫 봉 등을 보정
    if not df.empty:
        curr_price = df.iloc[0]['close']
        df['close'] = df['close'].apply(lambda x: curr_price if x > curr_price * 10 else x)
        df['sma_50'] = df['sma_50'].apply(lambda x: curr_price if x > curr_price * 10 else x)

    conn.close()
    df = df.sort_values('date')
    return df.to_dict(orient="records")

@app.get("/api/account")
def get_account_summary():
    """계좌 요약 (현재는 모의 데이터, 추후 KIS API 연결)"""
    return {
        "totalAsset": 50000000,
        "cash": 15000000,
        "totalProfit": 2450000,
        "totalProfitRate": 5.2,
        "buyingPower": 35000000,
        "riskPerTradePercent": 1.0,
        "positions": [] # 추후 KIS 잔고 조회 연동
    }

# 만약 대시보드를 빌드했다면 정적 파일 서빙 (GCP 배포용)
# if os.path.exists("dashboard/dist"):
#     app.mount("/", StaticFiles(directory="dashboard/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # 로컬 테스트 시: python src/api.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
