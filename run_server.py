"""
[TrendHunter Backend Server]
React 프론트엔드에 주식 데이터를 제공하는 FastAPI 서버.
실행: uvicorn run_server:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from src.db import get_connection
from src.analysis.screen_market import get_trend_candidates_db, get_supply_quality, check_chart_pattern, get_breakout_price, adjust_to_tick, get_themes_for_stock

app = FastAPI()

# CORS 설정 (React 앱이 3000번 포트에서 요청할 수 있게 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용. 배포 시 구체적 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
def get_status():
    return {"status": "ok", "message": "TrendHunter API is running"}

@app.get("/api/candidates")
def get_candidates():
    """스크리닝된 주도주 리스트 반환"""
    try:
        # 1. DB에서 후보군 조회
        raw_df = get_trend_candidates_db()
        
        final_list = []
        for _, row in raw_df.iterrows():
            # 차트 및 수급 필터링
            if not check_chart_pattern(row['code']): continue
            quality = get_supply_quality(row['code'])
            if "이탈" in quality: continue
            
            # 테마 정보
            themes = get_themes_for_stock(row['code'])
            
            # 진입가/손절가 계산
            entry = get_breakout_price(row['high_52w'])
            stop = max(adjust_to_tick(entry * 0.93), int(row['sma_20']))
            
            stock_data = {
                "code": row['code'],
                "name": row['name'],
                "close": row['close'],
                "rs_score": round(row['rs_score'], 1),
                "sector": themes[0] if themes else "None",
                "themes": themes,
                "supply": quality,
                "entry_price": entry,
                "stop_loss": stop,
                "vcp_ratio": round(row['vcp_ratio'], 2) if row['vcp_ratio'] else 0
            }
            final_list.append(stock_data)
            
        return {"count": len(final_list), "data": final_list}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/dividends")
def get_dividends():
    """고배당주 리스트 반환"""
    try:
        conn = get_connection()
        max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
        query = f"""
        SELECT m.code, m.name, d.close, d.dividend_yield, m.roe 
        FROM daily_analysis d 
        JOIN master_info m ON d.code = m.code 
        WHERE d.date = '{max_date}' AND d.dividend_yield >= 7.0 AND m.thtr_ntin > 0 AND m.roe >= 10.0 
        ORDER BY d.dividend_yield DESC LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return {"count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}
