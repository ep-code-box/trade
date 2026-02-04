import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "TrendHunter/db/stock_info.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def check_chart_pattern_score(conn, code):
    """VCP 검증: 변동성 수축 수치(Tightness Score) 계산"""
    df = pd.read_sql_query(f"SELECT high, low, close FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 10", conn)
    if len(df) < 10: return 999.0
    
    for col in ['high', 'low', 'close']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['range_pct'] = (df['high'] - df['low']) / df['close']
    
    recent_5d = df.head(5)
    prev_5d = df.iloc[5:10]
    score = recent_5d['range_pct'].mean()
    
    # 변동성 확대되면 탈락 (1.1배 허용)
    if score > prev_5d['range_pct'].mean() * 1.1: return 999.0
    return score

def get_supply_quality(conn, code):
    """수급 분석"""
    df = pd.read_sql_query(f"SELECT frgn_net_buy, orgn_net_buy FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 5", conn)
    if df.empty: return "Unknown"
    
    total_frgn = df['frgn_net_buy'].sum()
    total_orgn = df['orgn_net_buy'].sum()
    
    if total_frgn > 0 and total_orgn > 0: return "💎 쌍끌이"
    if (total_frgn + total_orgn) > 0: return "✅ 양호"
    return "- 일반"

def calculate_sma10_and_filter():
    conn = get_connection()
    
    # 1개월 전 날짜 (200일선 기울기용)
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    prev_date_res = conn.execute(f"SELECT date FROM daily_analysis WHERE code='0001' AND date < '{max_date}' ORDER BY date DESC LIMIT 20, 1").fetchone()
    prev_date = prev_date_res[0] if prev_date_res else '00000000'

    print("🔍 1차 필터링 (Full Option)...")
    # 조건: 
    # 1. 거래대금 30억+ & VDU
    # 2. 정배열 (20>50>200) & 이격도 20% 이내
    # 3. 200일선 상승 기울기
    # 4. 흑자 기업 (RS 90 이상은 면제)
    query = f"""
    SELECT d.code, m.name, d.close, d.rs_score, 
           d.sma_20, d.sma_50, d.sma_200, d.volume, d.volume_sma_50,
           m.bsop_prfi, m.thtr_ntin,
           (SELECT d2.sma_200 FROM daily_analysis d2 WHERE d2.code = d.code AND d2.date = '{prev_date}') as sma_200_prev
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      AND d.volume < (d.volume_sma_50 * 0.8)
      AND d.sma_20 > d.sma_50
      AND d.sma_50 > d.sma_200
      AND d.close >= d.sma_200
      AND d.close <= (d.sma_200 * 1.2)
      AND d.sma_200 > sma_200_prev
      AND ((m.bsop_prfi > 0 AND m.thtr_ntin > 0) OR (d.rs_score >= 90))
    """
    
    df = pd.read_sql(query, conn)
    print(f"   👉 1차 통과: {len(df)}개 종목")
    
    if len(df) == 0:
        print("   🚨 조건에 맞는 종목이 없습니다.")
        return

    # 2. 2차 정밀 필터링 (SMA10 / VCP / 수급)
    print("🔍 2차 정밀 필터링 (SMA10 / VCP / 수급)...")
    final_candidates = []
    
    codes = tuple(df['code'].tolist())
    placeholders = ',' .join('?' for _ in codes)
    dates_query = "SELECT DISTINCT date FROM daily_analysis ORDER BY date DESC LIMIT 15"
    valid_dates = [row[0] for row in conn.execute(dates_query).fetchall()]
    min_date = valid_dates[-1]
    
    hist_query = f"""
    SELECT code, close FROM daily_analysis 
    WHERE code IN ({placeholders}) AND date >= '{min_date}'
    ORDER BY date ASC
    """
    hist_df = pd.read_sql(hist_query, conn, params=codes)
    
    for idx, row in df.iterrows():
        # 1. SMA 10 Check
        sub_hist = hist_df[hist_df['code'] == row['code']]
        if len(sub_hist) < 10: continue
        sma_10 = sub_hist['close'].tail(10).mean()
        
        if sma_10 <= row['sma_20']: continue # 탈락
        
        # 2. VCP Check
        vcp_score = check_chart_pattern_score(conn, row['code'])
        # Strict 4% or Relaxed 6%
        if vcp_score > 0.06: continue # 탈락
        
        # 3. Supply Check
        supply_status = get_supply_quality(conn, row['code'])
        
        row_dict = row.to_dict()
        row_dict['sma_10'] = sma_10
        row_dict['vcp_score'] = vcp_score
        row_dict['supply'] = supply_status
        final_candidates.append(row_dict)

    final_df = pd.DataFrame(final_candidates)
    
    if len(final_df) == 0:
        print("   🚨 최정예 필터(SMA10+VCP) 통과 종목이 0개입니다. 전멸!")
        return

    print(f"   👉 최종 생존: {len(final_df)}개 종목")
    
    # 3. RS Score 내림차순 정렬
    final_df = final_df.sort_values(by='rs_score', ascending=False)
    
    print("\n" + "="*100)
    print(f" [시뮬레이션] Full Option (정배열+이격도20%+VCP+수급+흑자) 결과")
    print("="*100)
    print(f" {'종목명':<10} | {'현재가':>8} | {'RS':>3} | {'이격도':>6} | {'VCP':>5} | {'수급':<6} | {'SMA10':>8} | {'SMA20':>8}")
    print("-" * 100)
    
    count = 0
    for idx, row in final_df.iterrows():
        if count >= 20: break
        
        disparity = ((row['close'] - row['sma_200']) / row['sma_200']) * 100
        vcp_pct = row['vcp_score'] * 100
        print(f" {row['name']:<10} | {row['close']:>8,} | {row['rs_score']:>3.0f} | {disparity:>5.1f}% | {vcp_pct:>4.1f}% | {row['supply']:<6} | {int(row['sma_10']):>8,} | {int(row['sma_20']):>8,}")
        count += 1
    print("="*100)

if __name__ == "__main__":
    calculate_sma10_and_filter()
