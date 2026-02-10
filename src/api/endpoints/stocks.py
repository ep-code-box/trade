from fastapi import APIRouter
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.api.utils import get_db_row_dict
from src.utils.notifier import notifier
import json

router = APIRouter(tags=["stocks"])

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def init_llm():
    """백엔드 통합 초기화 (현재는 로깅만 수행)"""
    print("--- [Stocks API] Google Gemini & Telegram Notifier Integrated ---")

@router.get("/stocks/{code}/ai-analysis")
def get_ai_analysis(code: str, persona: str = "LIVERMORE"):
    """특정 종목에 대한 사냥꾼의 관점 분석 및 텔레그램 전송"""
    try:
        conn = get_connection()
        query = """
            SELECT 
                m.name, d.close, d.rs_score, m.roe, m.eps, d.date, d.high_52w,
                d.sma_50, d.sma_150, d.sma_200, d.volume, d.volume_sma_50,
                (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
                d.low_52w
            FROM daily_analysis d
            JOIN master_info m ON d.code = m.code
            WHERE d.code = ?
            ORDER BY d.date DESC LIMIT 1
        """
        cur = conn.cursor()
        cur.execute(query, (code,))
        row = cur.fetchone()
        
        res = conn.execute("SELECT value FROM system_config WHERE key='th_ai_config'").fetchone()
        conn.close()

        if not row or not res:
            return {"analysis": "데이터 또는 AI 설정을 찾을 수 없습니다."}

        if not HAS_GENAI:
            return {"analysis": "AI 라이브러리(google-generativeai)가 설치되어 있지 않습니다. 서버 관리자에게 문의하세요."}

        config = json.loads(res[0])
        api_key = config.get('apiKey')
        
        # 데이터 정밀화 (AI가 장님이 되지 않도록)
        curr_price = int(row[1])
        high_52w = int(row[6]) if row[6] else curr_price
        vol_ratio = (row[10] / row[11]) if row[11] and row[11] > 0 else 1.0
        
        # 미너비니 Trend Template 5번 조건 (신고가 대비 -25% 이내 체크)
        dist_from_high = ((curr_price / high_52w) - 1) * 100
        
        # 진짜 사자의 눈으로 보는 증거 데이터
        evidence = {
            "name": row[0],
            "price_action": {
                "current": f"{curr_price:,d}원",
                "high_52w": f"{high_52w:,d}원",
                "correction_depth": f"{dist_from_high:.1f}% (조정 깊이)",
                "rs_engine": f"{row[2]:.1f} (상대강도)"
            },
            "structure": {
                "vcp_tightness": f"{row[12]:.2f} (1.0 미만 수축)",
                "ma_alignment": "Stage 2 (정배열)" if curr_price > row[7] > row[8] > row[9] else "Broken/Sideways",
                "volume_dryup": "YES" if vol_ratio < 0.8 else "NO"
            }
        }

        # Google Gemini 호출
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
당신은 전설적인 사냥꾼이자 퀀트 멘토입니다. '현금도 포지션'임을 명심하십시오.
다음 데이터를 보고 '테니스 공(주도주)'인지 '달걀(약세주)'인지 판별하십시오.

[분석 대상]
{json.dumps(evidence, ensure_ascii=False, indent=2)}

[사냥 원칙]
1. 완벽한 구조(VCP 수축 및 정배열)가 아니면 무조건 [SKIP] 혹은 [READY] 하십시오.
2. 맹목적인 BUY는 금지입니다. 손익비가 안 나오면 가차 없이 버리십시오.
3. 리포트는 마크다운으로 가독성 있게 작성하십시오.

[판결 선택지]
- BUY: 지금 당장 방아쇠를 당겨야 하는 통계적 필연의 구간
- READY: 주도주이나 아직 베이스 형성 중. 피벗 가격 돌파를 기다려야 함
- SKIP: 구조가 깨졌거나 달걀에 불과함. 관심종목에서 삭제
"""
        response = model.generate_content(prompt)
        analysis_result = response.text

        # 텔레그램 전송
        tg_msg = f"🧠 <b>TrendHunter AI Audit: {row[0]}</b>\n"
        tg_msg += f"────────────────\n"
        tg_msg += f"{analysis_result}\n"
        tg_msg += f"────────────────\n"
        notifier.send_message(tg_msg)

        return {"analysis": analysis_result}
    except Exception as e:
        return {"analysis": f"분석 실패: {str(e)}"}

@router.get("/dates")
def get_available_dates():
    try:
        conn = get_connection()
        dates = [row[0] for row in conn.execute("SELECT DISTINCT date FROM trade_plan ORDER BY date DESC").fetchall()]
        conn.close()
        return [f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else d for d in dates]
    except: return []

@router.get("/summary")
def get_market_summary():
    try:
        conn = get_connection()
        # 1. 기준일 확보
        max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
        if not max_date:
            conn.close()
            return {"error": "no data"}

        # 2. 시장 RS (KOSPI 기준)
        res_rs = conn.execute("SELECT rs_score FROM daily_analysis WHERE code = '0001' AND date = ?", (max_date,)).fetchone()
        market_rs = res_rs[0] if res_rs else 0

        # 3. Stage 2 비율 (정배열 종목 비율)
        total_cnt = conn.execute("SELECT COUNT(*) FROM daily_analysis WHERE date = ? AND close > 0", (max_date,)).fetchone()[0]
        stage2_cnt = conn.execute("""
            SELECT COUNT(*) FROM daily_analysis 
            WHERE date = ? AND close > sma_50 AND sma_50 > sma_200 AND sma_200 > 0
        """, (max_date,)).fetchone()[0]
        stage2_ratio = round((stage2_cnt / total_cnt * 100), 1) if total_cnt > 0 else 0

        # 4. 활성 주도주 수 (오늘의 trade_plan 종목 수)
        plan_date = conn.execute("SELECT MAX(date) FROM trade_plan").fetchone()[0]
        active_leaders = conn.execute("SELECT COUNT(*) FROM trade_plan WHERE date = ?", (plan_date,)).fetchone()[0] if plan_date else 0

        # 5. 주도 섹터 (가장 많이 포착된 테마)
        top_sector = "N/A"
        if plan_date:
            sector_res = conn.execute("""
                SELECT category_name, COUNT(*) as cnt 
                FROM trade_plan t
                JOIN sectors_themes s ON t.code = s.code
                WHERE t.date = ?
                GROUP BY category_name
                ORDER BY cnt DESC LIMIT 1
            """, (plan_date,)).fetchone()
            if sector_res: top_sector = sector_res[0]

        # 6. 리스크 레벨 산출 (Stage 2 비율 기준)
        if stage2_ratio > 40: risk_level = "SAFE"
        elif stage2_ratio > 20: risk_level = "NORMAL"
        else: risk_level = "CAUTION"

        conn.close()
        return {
            "stage2Ratio": stage2_ratio,
            "activeLeaders": active_leaders,
            "marketRS": market_rs,
            "topSector": top_sector,
            "riskLevel": risk_level,
            "lastSync": max_date
        }
    except Exception as e:
        print(f"Summary Error: {e}")
        return {"error": str(e)}

@router.get("/stocks")
def get_stock_analysis(date: str = None):
    try:
        conn = get_connection()
        if not date:
            res = conn.execute("SELECT MAX(date) FROM trade_plan").fetchone()
            date = res[0] if res else None
        if not date: return []
        target_date = date.replace('-', '')
        
        # 재무 지표를 포함한 정밀 쿼리
        query = """
            SELECT 
                t.date, t.code as symbol, t.name, t.track, t.rs_score as rsScore, t.vcp_ratio as vcpRatio,
                t.entry_price as price, t.stop_price as stopLossPrice, t.weight, t.rationale,
                d.close as curr_price, d.open, d.high_52w, d.dividend_yield as dividendYield,
                m.roe, m.bsop_prfi, m.thtr_ntin, m.sale_account
            FROM trade_plan t
            LEFT JOIN daily_analysis d ON t.code = d.code AND d.date = t.date
            LEFT JOIN master_info m ON t.code = m.code
            WHERE t.date = ?
            ORDER BY t.rs_score DESC
        """
        df = pd.read_sql_query(query, conn, params=(target_date,))
        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
        conn.close()

        results = []
        for _, row in df.iterrows():
            curr = float(row['curr_price'] or row['price'] or 0)
            oprc = float(row['open'] or curr or 0)
            bsop = float(row['bsop_prfi'] or 0)
            sales = float(row['sale_account'] or 0)
            op_margin = round((bsop / sales * 100), 1) if sales > 0 else 0

            # 트랙 표준화 (프론트엔드 App.tsx 필터와 100% 매칭)
            raw_track = str(row['track']).upper()
            if 'TRACK1' in raw_track: display_track = 'TRACK1'
            elif 'TRACK_EX' in raw_track: display_track = 'TRACK_EX'
            elif 'TRACK2' in raw_track: display_track = 'TRACK2'
            else: display_track = raw_track

            results.append({
                "date": f"{str(row['date'])[:4]}-{str(row['date'])[4:6]}-{str(row['date'])[6:8]}", 
                "symbol": str(row['symbol']), "name": str(row['name']),
                "price": int(curr), "change": round(((curr - oprc) / oprc * 100), 2) if oprc > 0 else 0,
                "rsScore": float(row['rsScore'] or 0), "vcpRatio": float(row['vcpRatio'] or 0),
                "track": display_track, "dividendYield": float(row['dividendYield'] or 0),
                "roe": round(float(row['roe'] or 0), 1), "opMargin": op_margin,
                "isStage2": 1, "sector": "주도주",
                "targetPrice": int(row['price'] or 0), "stopLossPrice": int(row['stopLossPrice'] or 0),
                "rationale": [str(row['rationale'])], "weight": str(row['weight']),
                "template": { 
                    "priceAbove50": True, "sma200TrendingUp": True, "rsAbove70": float(row['rsScore'] or 0) > 70 
                }
            })
        return results
    except Exception as e:
        print(f"Error in get_stock_analysis: {e}")
        return []

@router.get("/stocks/{code}/history")
def get_stock_history(code: str):
    try:
        conn = get_connection()
        query = "SELECT date, open, close, volume, volume_sma_50, sma_20, sma_50, sma_150, sma_200 FROM daily_analysis WHERE code = ? ORDER BY date DESC LIMIT 200"
        df = pd.read_sql_query(query, conn, params=(code,))
        conn.close()
        if df.empty: return []
        df = df.sort_values('date').rename(columns={'sma_20': 'sma_21'})
        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)
        return df.to_dict(orient="records")
    except: return []