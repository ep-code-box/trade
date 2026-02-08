import sys
import os
import json

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_connection
from src.utils.mlx_llm import TrendHunterLLM

def run_ai_audit():
    print("--- [AI Audit] Fetching Data ---")
    conn = get_connection()
    query = """
    SELECT m.code, m.name, d.close, d.rs_score, m.roe, m.eps, d.date 
    FROM daily_analysis d 
    JOIN master_info m ON d.code = m.code 
    WHERE d.rs_score IS NOT NULL 
    ORDER BY d.date DESC, d.rs_score DESC 
    LIMIT 1
    """
    cur = conn.cursor()
    cur.execute(query)
    target = cur.fetchone()
    conn.close()

    if not target:
        print("No data found.")
        return

    # 영문 키와 영문 텍스트만 사용하여 인코딩 문제 원천 차단
    stock_info = {
        "stock_name": "Sung-ho Electronics",
        "ticker": target[0],
        "current_price": target[2],
        "rs_score": target[3],
        "stop_loss_shield": int(target[2] * 0.95),
        "eps": target[5],
        "roe": target[4]
    }
    
    print(f"Loading LLM for Ticker: {target[0]}...")
    try:
        llm = TrendHunterLLM()
        print("Generating Analysis...")
        # JSON을 단순 문자열로 전달
        analysis = llm.analyze_stock(json.dumps(stock_info), "LIVERMORE")
        
        # 파일에 저장 (가장 안전)
        with open("analysis_result.txt", "w", encoding="utf-8") as f:
            f.write(analysis)
        
        print("\nSUCCESS: Analysis saved to analysis_result.txt")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    run_ai_audit()
