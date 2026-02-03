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

@app.get("/api/dates")
def get_available_dates():
    """사용 가능한 리포트 날짜 목록 반환"""
    conn = get_connection()
    query = "SELECT DISTINCT date FROM trade_plan ORDER BY date DESC"
    cursor = conn.cursor()
    cursor.execute(query)
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dates

@app.get("/api/stocks")
def get_stock_analysis(date: str = None):
    """스크리너 결과 반환 (날짜 필터링 지원)"""
    try:
        conn = get_connection()
        
        # 날짜 지정이 없으면 최신 날짜 사용
        if not date:
            date_query = "SELECT MAX(date) FROM trade_plan"
            cursor = conn.cursor()
            cursor.execute(date_query)
            date = cursor.fetchone()[0]
            
        query = """
            SELECT 
                t.date, t.code as symbol, t.name, t.track, t.rs_score as rsScore, t.vcp_ratio as vcpRatio,
                t.entry_price as price, t.stop_price as stopLossPrice, t.weight, t.rationale,
                d.close as curr_price, d.open, d.high_52w, d.dividend_yield as dividendYield,
                m.roe, m.bsop_prfi, m.thtr_ntin, m.sale_account, m.stck_fcam
            FROM trade_plan t
            LEFT JOIN (
                SELECT * FROM daily_analysis 
                WHERE date = ?
            ) d ON t.code = d.code
            LEFT JOIN master_info m ON t.code = m.code
            WHERE t.date = ?
            ORDER BY t.rs_score DESC
        """
        # 일일 시세 조인 시에도 해당 날짜(혹은 그 이전 최신)를 써야 정확하지만, 
        # 구조상 trade_plan date와 daily_analysis date가 일치한다고 가정하고 심플하게 구현.
        # 만약 주말/공휴일 trade_plan 생성시엔 daily 데이터가 금요일것일 수 있음 -> 복잡도 증가.
        # 우선 1:1 매칭으로 진행.
        
        df = pd.read_sql_query(query, conn, params=(date, date))
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
                    "date": str(row['date']),
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

from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, MODE
import requests
import json

# ... (existing code)

@app.get("/api/account")
async def get_account_summary():
    """계좌 요약 (KIS API 실시간 연동)"""
    cano = os.getenv("CANO")
    acnt_prdt_cd = os.getenv("ACNT_PRDT_CD", "01")

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
            "CANO": cano,
            "ACNT_PRDT_CD": acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance", headers=headers, params=params, timeout=10)
        data = res.json()

        if data.get('rt_cd') != '0':
            print(f"KIS API Error: {data.get('msg1')}")
            # 에러 시 모의 데이터 fallback 혹은 에러 반환
            # 여기선 에러 상황을 표시하기 위해 빈 객체 반환하거나 기존 모의 데이터 반환
            return {
                "totalAsset": 0, "cash": 0, "totalProfit": 0, "totalProfitRate": 0, 
                "buyingPower": 0, "riskPerTradePercent": 1.0, "positions": [],
                "error": data.get('msg1')
            }

        output1 = data.get('output1', [])
        output2 = data.get('output2', [])
        
        summary = output2[0] if output2 else {}
        
        total_asset = int(summary.get('tot_evlu_amt', 0) or 0)
        total_profit = int(summary.get('evlu_pfls_smtl_amt', 0) or 0)
        cash = int(summary.get('dnca_tot_amt', 0) or 0) # 예수금총금액
        
        # 수익률 계산 (자산이 0이면 0)
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
                    "status": "HEALTHY",
                    "sector": "Unknown",
                    "initialStopLoss": int(avg_price * 0.9),
                    "trailingStop": int(avg_price * 0.95),
                    "breakEvenPrice": int(avg_price),
                    "targetPrice": int(avg_price * 1.2),
                    "daysHeld": 1,
                    "violations": [],
                    "rsTrend": "flat",
                    "vitalityScore": 50,
                    "entryDate": datetime.now().strftime('%Y-%m-%d')
                })

        return {
            "totalAsset": total_asset,
            "cash": cash,
            "totalProfit": total_profit,
            "totalProfitRate": total_profit_rate,
            "buyingPower": cash, # 추후 주문가능금액 조회 API 연동 필요할 수 있음
            "riskPerTradePercent": 1.0,
            "positions": positions
        }

    except Exception as e:
        print(f"Account API Error: {e}")
        return {
            "totalAsset": 0,
            "cash": 0,
            "totalProfit": 0,
            "totalProfitRate": 0,
            "buyingPower": 0,
            "riskPerTradePercent": 1.0,
            "positions": [],
            "error": str(e)
        }

# 만약 대시보드를 빌드했다면 정적 파일 서빙 (GCP 배포용)
# if os.path.exists("dashboard/dist"):
#     app.mount("/", StaticFiles(directory="dashboard/dist", html=True), name="static")

@app.get("/api/explore")
def explore_market(
    page: int = 1,
    limit: int = 50,
    sort_by: str = "rs_score",
    order: str = "desc",
    search: str = "",
    min_rs: float = 0,
    min_amount: int = 0
):
    """전체 시장 데이터 탐색 (Raw Data Explorer)"""
    try:
        conn = get_connection()
        
        # 1. 최신 날짜 확인
        date_query = "SELECT MAX(date) FROM daily_analysis"
        cursor = conn.cursor()
        cursor.execute(date_query)
        latest_date = cursor.fetchone()[0]
        
        if not latest_date:
            return {"items": [], "total": 0, "date": ""}

        # 2. 기본 쿼리 구성
        base_query = f"""
            SELECT 
                d.code, m.name, d.close, d.open, d.volume, d.amount,
                d.rs_score, d.sma_20, d.sma_50, d.sma_200,
                m.market_type, m.stck_fcam as market_cap
            FROM daily_analysis d
            JOIN master_info m ON d.code = m.code
            WHERE d.date = ?
        """
        params = [latest_date]

        # 3. 필터링 적용
        if search:
            base_query += " AND (m.name LIKE ? OR d.code LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if min_rs > 0:
            base_query += " AND d.rs_score >= ?"
            params.append(min_rs)
            
        if min_amount > 0:
            base_query += " AND d.amount >= ?"
            params.append(min_amount * 1000000) # 거래대금 단위 보정 (백만원 -> 원) 필요시 확인. 스키마엔 INTEGER. 보통 KIS는 원단위일수도, 백만일수도. 스키마 확인 결과 amount는 거래대금.
            # 스키마 주석엔 "Trading Value (KRW)"라고 되어있음. 
            # 만약 DB에 원단위로 저장되어 있다면 그대로 비교. 
            # 보통 Hantoo API는 원단위. DB 저장시 단위를 확인해야 함. 
            # 우선 원단위로 가정하고 파라미터는 '백만원' 단위로 받는게 편할 수 있음. 
            # 사용자가 100 입력 -> 1억. 여기선 그냥 raw value 비교로 가고 클라이언트에서 조정.
        
        # 4. 정렬 검증 및 적용
        valid_sort_cols = ["rs_score", "amount", "close", "volume", "market_cap"]
        if sort_by not in valid_sort_cols:
            sort_by = "rs_score"
        
        order = "ASC" if order.lower() == "asc" else "DESC"
        base_query += f" ORDER BY {sort_by} {order}"

        # 5. 전체 개수 조회 (페이징 전)
        count_query = f"SELECT COUNT(*) FROM ({base_query})"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # 6. 페이징 적용
        offset = (page - 1) * limit
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # 7. 데이터 조회
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            # 등락률 계산
            close = row[2]
            open_prc = row[3]
            change = 0
            if open_prc > 0:
                change = round((close - open_prc) / open_prc * 100, 2)
            
            results.append({
                "code": row[0],
                "name": row[1],
                "close": close,
                "change": change,
                "amount": row[5],
                "rsScore": row[6] or 0,
                "marketType": row[10],
                "marketCap": row[11], # 시가총액
                "volume": row[4]
            })
            
        conn.close()
        
        return {
            "items": results,
            "total": total_count,
            "page": page,
            "limit": limit,
            "date": latest_date
        }

    except Exception as e:
        print(f"Explore API Error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # 로컬 테스트 시: python src/api.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
