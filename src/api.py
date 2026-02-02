from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import sqlite3
import os
from datetime import datetime
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

@app.get("/api/stocks")
def get_stock_analysis():
    """스크리너 결과 및 주요 지표 반환 (프론트엔드 형식에 최적화)"""
    # 1. 가장 최근 날짜 확인
    conn = get_connection()
    res = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()
    if not res or not res[0]:
        conn.close()
        return []
    max_date = res[0]

    # 2. 데이터 조회
    query = """
        SELECT 
            d.code as symbol, m.name, d.close as price, d.open, d.rs_score as rsScore,
            d.vol_std_10d, d.vol_std_50d,
            d.sma_50 as sma50, d.sma_150 as sma150, d.sma_200 as sma200,
            d.high_52w as high52w, d.low_52w as low52w,
            d.dividend_yield as dividendYield,
            (SELECT category_name FROM sectors_themes WHERE code = d.code AND category_type = 'THEME' LIMIT 1) as sector
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
        WHERE d.date = ?
        ORDER BY d.rs_score DESC
    """
    df = pd.read_sql_query(query, conn, params=(max_date,))
    conn.close()

    # 3. 데이터 가공 (Mapping)
    results = []
    for _, row in df.iterrows():
        # 등락률 계산
        change_pct = round(((row['price'] - row['open']) / row['open'] * 100), 2) if row['open'] > 0 else 0
        
        # VCP 비율
        vcp_ratio = round(row['vol_std_10d'] / row['vol_std_50d'], 3) if row['vol_std_50d'] and row['vol_std_50d'] > 0 else 0

        # Track 분류 (TrackType Enum 값에 맞춤)
        track = "트랙 2: 뚜벅이 (고배당)"
        if row['rsScore'] and row['rsScore'] >= 80:
            if row['sector'] and row['sector'] != "미분류":
                track = "트랙 1: 추세 추종 (주도주)"
            else:
                track = "트랙 EX: 개별 모멘텀"

        # Template 조건 (TrendTemplateStatus 인터페이스에 맞춤)
        template = {
            "priceAbove50": row['price'] > row['sma50'] if row['sma50'] else False,
            "priceAbove150_200": (row['price'] > row['sma150'] and row['price'] > row['sma200']) if row['sma150'] and row['sma200'] else False,
            "sma150Above200": row['sma150'] > row['sma200'] if row['sma150'] and row['sma200'] else False,
            "sma50Above150_200": (row['sma50'] > row['sma150'] and row['sma50'] > row['sma200']) if row['sma50'] and row['sma150'] and row['sma200'] else False,
            "sma200TrendingUp": True, # 일단 기본값
            "above52wLow25": row['price'] >= (row['low52w'] * 1.25) if row['low52w'] else False,
            "within52wHigh25": row['price'] >= (row['high52w'] * 0.75) if row['high52w'] else False,
            "rsAbove70": (row['rsScore'] >= 70) if row['rsScore'] else False
        }

        results.append({
            "symbol": row['symbol'],
            "name": row['name'],
            "price": int(row['price']),
            "change": change_pct,
            "rsScore": round(row['rsScore'], 1) if row['rsScore'] else 0,
            "vcpRatio": vcp_ratio,
            "sma50": row['sma50'],
            "sma150": row['sma150'],
            "sma200": row['sma200'],
            "track": track,
            "dividendYield": row['dividendYield'],
            "isStage2": 1 if (template["priceAbove50"] and template["sma150Above200"]) else 0,
            "sector": row['sector'] or "미분류",
            "template": template,
            "volumeDryUp": vcp_ratio < 0.5,
            "targetPrice": int(row['high52w']) if row['high52w'] else 0,
            "stopLossPrice": int(row['price'] * 0.93), # 7% 손절 기본
            "rationale": [f"RS {round(row['rsScore'],1)}점의 강력한 모멘텀", f"{row['sector']} 섹터 주도주 후보"],
            "atr": 0,
            "volatility": 0
        })

    return results[:200] # 상위 200개만 반환

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
