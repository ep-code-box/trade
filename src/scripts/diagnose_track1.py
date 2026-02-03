
import pandas as pd
from src.db import get_connection
from src.analysis.screen_market import get_tick_size, adjust_to_tick, get_breakout_price, check_chart_pattern_score

def diagnose():
    conn = get_connection()
    res = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()
    max_date = res[0]
    print(f"Diagnosis Date: {max_date}")
    
    # 1. Base Pool (Amount > 3B)
    base_df = pd.read_sql_query(f"SELECT code FROM daily_analysis WHERE date='{max_date}' AND amount >= 3000000000", conn)
    print(f"1. Base Pool (Amount >= 3B): {len(base_df)}")
    
    # 2. Alignment (Perfect Order)
    align_query = f"""
    SELECT d.code FROM daily_analysis d 
    WHERE d.date='{max_date}' AND d.amount >= 3000000000
    AND d.close > d.sma_20 AND d.sma_20 > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
    """
    align_df = pd.read_sql_query(align_query, conn)
    print(f"2. Perfect Order (P>20>50>150>200): {len(align_df)}")
    
    # 3. VDU (Volume Dry Up)
    vdu_query = f"""
    SELECT d.code FROM daily_analysis d 
    WHERE d.date='{max_date}' AND d.amount >= 3000000000
    AND d.close > d.sma_20 AND d.sma_20 > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
    AND d.volume < (d.volume_sma_50 * 0.8)
    """
    vdu_df = pd.read_sql_query(vdu_query, conn)
    print(f"3. VDU (Vol < 50MA * 0.8): {len(vdu_df)}")
    
    # 4. Check VCP for VDU survivors
    print("\n[VCP Check for Top 5 RS survivors]")
    
    survivors_query = f"""
    SELECT d.code, m.name, d.rs_score, d.high_52w, d.close, d.sma_20
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date='{max_date}' AND d.amount >= 3000000000
    AND d.close > d.sma_20 AND d.sma_20 > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
    AND d.volume < (d.volume_sma_50 * 0.8)
    ORDER BY d.rs_score DESC
    LIMIT 10
    """
    survivors = pd.read_sql_query(survivors_query, conn)
    
    for _, row in survivors.iterrows():
        vcp = check_chart_pattern_score(row['code'])
        
        # Survival Logic
        entry = get_breakout_price(row['high_52w'])
        stop_fixed = entry * 0.93
        stop_sma20 = row['sma_20'] or 0
        stop = max(stop_fixed, stop_sma20)
        stop = adjust_to_tick(stop, 'down')
        is_broken = row['close'] < stop
        
        status = "PASS"
        if is_broken: status = "BROKEN (Stop Loss)"
        elif vcp > 0.06: status = f"FAIL (VCP {vcp:.2f} > 0.06)"
        elif vcp > 0.04: status = f"RELAXED (VCP {vcp:.2f})"
        else: status = f"STRICT (VCP {vcp:.2f})"
        
        print(f" - {row['name']} (RS {row['rs_score']}): {status}")

    conn.close()

if __name__ == "__main__":
    diagnose()
