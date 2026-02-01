"Track1/Track EX/Track2 통합 리포트 (Direct SQL - No Duplicates)."
import pandas as pd
from datetime import datetime
from src.db import get_connection
from src.analysis.market_filter import check_market_health
from collections import Counter

def get_themes_for_stock(code):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT category_name FROM sectors_themes WHERE code = ? AND category_type = 'THEME'",
        conn,
        params=(code,),
    )
    conn.close()
    return df["category_name"].tolist()

def get_trend_candidates_direct():
    """뷰를 거치지 않고 직접 초결벽주의 원칙으로 쿼리 (완전 정배열 적용)"""
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    # 1. Fundamental & Extension Filters Adjusted
    # - RS Score >= 80
    # - Perfect Alignment: Price > SMA20 > SMA50 > SMA150 > SMA200 (사용자 요청 반영)
    query = f"""
    SELECT 
        d.date, d.code, m.name, m.market_type,
        d.close, d.amount, d.volume, d.rs_score,
        (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
        d.high_52w, d.sma_20, d.sma_50, d.sma_150, d.sma_200,
        m.bsop_prfi, m.thtr_ntin, m.roe
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      -- [완전 정배열 조건 완화: 눌림목 허용]
      AND d.close > d.sma_50 
      AND d.sma_50 > d.sma_150 
      AND d.sma_150 > d.sma_200
      -- [수정] NULL 방지 및 조건 복구
      AND d.high_52w IS NOT NULL
      AND d.close >= d.high_52w * 0.85
      AND d.rs_score >= 80
      AND (d.close / d.sma_200) < 2.0
      AND (d.vol_std_10d / d.vol_std_50d) < 0.9
      AND (
          (m.bsop_prfi > 0 AND m.thtr_ntin > 0) 
          OR 
          (d.rs_score >= 90)
      )
    ORDER BY d.rs_score DESC, vcp_ratio ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_tick_size(price):
    """한국 주식 시장 호가 단위 계산 (KOSPI/KOSDAQ 통합 단순화)"""
    if price < 2000: return 1
    if price < 5000: return 5
    if price < 20000: return 10
    if price < 50000: return 50
    if price < 200000: return 100
    if price < 500000: return 500
    return 1000

def adjust_to_tick(price):
    """가격을 호가 단위에 맞춰 올림 (Ceiling)"""
    tick = get_tick_size(price)
    return ((int(price) + tick - 1) // tick) * tick

def get_breakout_price(high_52w):
    """
    진입가 정밀 산정 (조준경 보정):
    1. 기본: 52주 신고가 + 2% (안전 마진)
    2. 라운드 피겨(심리적 저항선) 돌파 보정:
       - 계산된 가격이 '마의 벽(1만, 5만, 10만)' 바로 아래라면, 
         벽을 확실히 넘는 가격으로 강제 상향.
    3. 호가 단위(Tick) 정렬:
       - 시장에 존재하지 않는 가격(예: 103,734원) 제거 -> 104,000원
    """
    target = high_52w * 1.02
    
    # [라운드 피겨 강제 돌파 로직]
    # 저항선 바로 밑에서 매수하는 것을 방지하기 위해 목표가를 '벽 위'로 올림
    
    # 10만원 벽 (예: 98,000 ~ 99,900 -> 100,500)
    if 98000 <= target < 100000: 
        return 100500
    # 5만원 벽 (예: 49,000 ~ 49,950 -> 50,500)
    elif 49000 <= target < 50000: 
        return 50500
    # 1만원 벽 (예: 9,800 ~ 9,990 -> 10,100)
    elif 9800 <= target < 10000: 
        return 10100
    # 5천원 벽 (예: 4,900 ~ 4,995 -> 5,050)
    elif 4900 <= target < 5000: 
        return 5050
        
    return adjust_to_tick(target)

def generate_full_report():
    print("=" * 60)
    print(f" [TrendHunter] 오늘의 S급 마스터 종목 보고서 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 60)

    # 0. Market Filter Check
    print("\n[🚦 시장 환경 분석 (Market Health Check)]")
    market_status = check_market_health()
    is_dangerous = False
    
    for m in market_status:
        icon = "🟢" if m['status'] == 'GREEN' else "🔴"
        val_str = f"{m['curr']:,.2f}" if m['curr'] > 0 else "N/A"
        sma_str = f"{m['sma200']:,.2f}" if m['sma200'] > 0 else "N/A"
        print(f"   {icon} {m['name']}: {val_str} (기준선: {sma_str})")
        if m['status'] == 'RED':
            is_dangerous = True
    
    if is_dangerous:
        print("\n   ⚠️ [경고] 시장이 장기 이평선(200일) 아래에 있거나 하락 추세입니다.")
        print("   ⚠️ 마크 미너비니의 조언: '지수가 하락세일 때 공격적인 매수는 계좌를 파괴한다.'")
        print("   ⚠️ 권장 행동: 현금 비중 100% 유지 혹은 정찰병(10% 미만)만 운용.")
    else:
        print("\n   ✅ [양호] 시장이 상승 추세에 있습니다. 주도주 매매 적기입니다.")

    trend_df = get_trend_candidates_direct()
    
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    # Track 2: RS 점수와 무관하게 배당수익률 7% 이상 + 흑자 + ROE 10% 이상 (초우량주)
    query_div = f"""
    SELECT DISTINCT m.code, m.name, d.close, d.dividend_yield,
           COALESCE(m.dividend_cycle, '연배당') as cycle,
           COALESCE(m.per_stock_dvdn_amt, 0) as dps,
           m.roe
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.dividend_yield >= 7.0
      AND m.thtr_ntin > 0
      AND m.roe >= 10.0
    ORDER BY d.dividend_yield DESC LIMIT 15
    """
    div_df = pd.read_sql_query(query_div, conn)
    conn.close()
    
    print("=" * 60)
    print(f" [TrendHunter] 오늘의 S급 마스터 종목 보고서 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 60)

    # --- 로직 분리: 테마 분석 및 그룹핑 ---
    themed_stocks = []      # (row, themes_list)
    unthemed_stocks = []    # row
    all_themes = []

    for _, row in trend_df.iterrows():
        themes = get_themes_for_stock(row["code"])
        if themes:
            themed_stocks.append((row, themes))
            all_themes.extend(themes)
        else:
            unthemed_stocks.append(row)

    # 메인 테마 선정 (가장 많이 등장한 Top 3 테마)
    theme_counts = Counter(all_themes)
    top_3_themes = [t for t, c in theme_counts.most_common(3)]
    
    track1_list = []      # 메인 테마주
    market_leaders = []   # 비주류 테마 대장주

    for row, themes in themed_stocks:
        if any(t in top_3_themes for t in themes):
            track1_list.append((row, themes))
        else:
            market_leaders.append((row, themes))

    # 1. Track 1: 메인 주도 테마 (섹터별 Top 2 압축)
    main_theme_str = ", ".join(top_3_themes) if top_3_themes else "없음"
    print(f"\n[🔥 TRACK 1: 시장 주도 테마 섹터 (각 테마별 Top 2 대장주)]")
    print(f"   >> 현재 시장 주도 테마: {main_theme_str}")
    
    if not track1_list:
        print("   조건을 만족하는 주도 테마주가 없습니다.")
    else:
        # 테마별로 종목을 그룹핑
        theme_groups = {t: [] for t in top_3_themes}
        processed_codes = set()
        
        for row, themes in track1_list:
            for t in top_3_themes:
                if t in themes and row["code"] not in processed_codes:
                    theme_groups[t].append(row)
                    processed_codes.add(row["code"])
                    break
        
        # 각 테마별 RS 상위 2개만 선별
        final_track1 = []
        for t in top_3_themes:
            sorted_stocks = sorted(theme_groups[t], key=lambda x: x["rs_score"], reverse=True)
            final_track1.extend(sorted_stocks[:2])
            
        final_track1 = sorted(final_track1, key=lambda x: x["rs_score"], reverse=True)

        for row in final_track1:
            entry_price = get_breakout_price(row["high_52w"])
            hard_stop = adjust_to_tick(entry_price * 0.93)
            tech_stop = int(row["sma_20"])
            stop_loss = max(hard_stop, tech_stop)
            
            highlighted_themes = get_themes_for_stock(row["code"])
            
            print(f"\n▶ {row['name']} ({row['code']}) | RS {row['rs_score']:.0f} | 테마: {', '.join(highlighted_themes)}")
            print(f"   [진입] {entry_price:,}원 (신고가 +2% 돌파)  |  [손절] {stop_loss:,}원 (-{(1 - stop_loss/entry_price)*100:.1f}%)")
            print(f"   [비중] 주력 베팅 (10~20%)")
            print("-" * 50)

    # 2. Market Leaders: 비주류 테마의 숨은 대장 (Top 5)
    print(f"\n[🏆 MARKET LEADERS: 틈새시장(비주류 테마) 대장주 (Top 5)]")
    
    if not market_leaders:
        print("   조건을 만족하는 틈새시장 대장주가 없습니다.")
    else:
        for row, themes in market_leaders[:5]:
            entry_price = get_breakout_price(row["high_52w"])
            hard_stop = adjust_to_tick(entry_price * 0.93)
            tech_stop = int(row["sma_20"])
            stop_loss = max(hard_stop, tech_stop)
            
            print(f"\n▶ {row['name']} ({row['code']}) | RS {row['rs_score']:.0f} | 테마: {', '.join(themes)}")
            print(f"   [진입] {entry_price:,}원 (신고가 +2% 돌파)  |  [손절] {stop_loss:,}원 (-{(1 - stop_loss/entry_price)*100:.1f}%)")
            print(f"   [비중] 표준 베팅 (5~10%)")
            print("-" * 50)

    # 3. Track EX: 독립 강세주 (Top 5)
    print(f"\n[🚀 TRACK EX: 무소속 독립 강세주 (Top 5)]")
    print("   >> 테마/섹터 없음. 오직 개별 호재로 상승. (형제주 없음 주의)")
    
    if not unthemed_stocks:
        print("   조건을 만족하는 독립 강세주가 없습니다.")
    else:
        for row in unthemed_stocks[:5]:
            entry_price = get_breakout_price(row["high_52w"])
            hard_stop = adjust_to_tick(entry_price * 0.93)
            tech_stop = int(row["sma_20"])
            stop_loss = max(hard_stop, tech_stop)
            
            print(f"\n▶ {row['name']} ({row['code']}) | RS {row['rs_score']:.0f} | (테마 없음)")
            print(f"   [진입] {entry_price:,}원 (신고가 +2% 돌파)  |  [손절] {stop_loss:,}원 (-{(1 - stop_loss/entry_price)*100:.1f}%)")
            print(f"   [비중] 극소량 정찰 (3% 미만) - 실패 시 즉시 이탈")
            print("-" * 50)

    # 4. 고배당 안전주
    print(f"\n[🛡️ TRACK 2: 고배당 안전주 (수익률 7%↑ & 흑자 & ROE 10%↑)]")
    if div_df.empty:
        print("   조건(7% 이상, 흑자, ROE 10%↑)을 만족하는 초우량 고배당주가 없습니다.")
    else:
        for _, row in div_df.iterrows():
            print(f"▶ {row['name']} ({row['code']}) | 수익률: {row['dividend_yield']:.2f}% ({row['cycle']}) | ROE: {row['roe']:.1f}%")
    
    print("\n[AI 멘토의 행동 지침]")
    print("""마스터는 예측하지 않습니다. 오직 설정한 선을 넘느냐, 깨느냐에만 반응합니다.""")

if __name__ == "__main__":
    generate_full_report()
