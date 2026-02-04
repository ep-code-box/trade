"Track1/Track EX/Track2 통합 리포트 v5.4 (Dynamic VCP: Strict 4% & Relaxed 6%)."
import pandas as pd
import numpy as np
from datetime import datetime
from src.db import get_connection
from src.analysis.market_filter import check_market_health
from collections import Counter, defaultdict

def get_themes_for_stock(code):
    conn = get_connection()
    df = pd.read_sql_query("SELECT category_name FROM sectors_themes WHERE code = ? AND category_type = 'THEME'", conn, params=(code,))
    conn.close()
    return df["category_name"].tolist()

def get_supply_quality(code):
    """수급 질적 분석: 쌍끌이(외인+기관) 및 매집 강도 체크"""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT close, open, frgn_net_buy, orgn_net_buy FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 5", conn)
    conn.close()
    if df.empty or df['frgn_net_buy'].isnull().all(): return "Unknown"
    
    for col in ['close', 'open', 'frgn_net_buy', 'orgn_net_buy']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 5일 합산 수급
    total_frgn = df['frgn_net_buy'].sum()
    total_orgn = df['orgn_net_buy'].sum()
    
    # 쌍끌이 체크
    is_both_buying = total_frgn > 0 and total_orgn > 0
    
    df['is_up'] = df['close'] > df['open']
    up_days = df[df['is_up']]
    down_days = df[~df['is_up']]
    up_supply = (up_days['frgn_net_buy'].sum() + up_days['orgn_net_buy'].sum()) if not up_days.empty else 0
    down_supply = abs(down_days['frgn_net_buy'].sum() + down_days['orgn_net_buy'].sum()) if not down_days.empty else 0
    
    status = ""
    if is_both_buying: status = "💎 쌍끌이매집"
    elif up_supply > down_supply * 1.5: status = "🌟 공격적매집"
    elif (total_frgn + total_orgn) > 0: status = "✅ 수급우량"
    elif (total_frgn + total_orgn) < 0: status = "🚨 수급이탈"
    else: status = "👤 개인주도"
    
    return status

def get_tick_size(price):
    if price < 2000: return 1
    elif price < 5000: return 5
    elif price < 20000: return 10
    elif price < 50000: return 50
    elif price < 200000: return 100
    else: return 500

def adjust_to_tick(price, method='up'):
    tick = get_tick_size(price)
    if method == 'up': return ((int(price) // tick) + 1) * tick
    else: return (int(price) // tick) * tick

def get_breakout_price(high_52w):
    """정조준 진입가: 52주 신고가 + 0.5% 돌파 & 라운드 피겨 보정"""
    target = high_52w * 1.005
    
    # 라운드 피겨(심리적 저항선) 보정 로직 복원
    if 98000 <= target < 100000: target = 100500
    elif 48000 <= target < 50000: target = 50500
    elif 9800 <= target < 10000: target = 10100
    elif 4900 <= target < 5000: target = 5050
    
    return adjust_to_tick(target, 'up')

def check_chart_pattern_score(code):
    """거장의 VCP 검증: 변동성 수축 수치(Tightness Score)를 반환"""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT high, low, close FROM daily_analysis WHERE code = '{code}' ORDER BY date DESC LIMIT 10", conn)
    conn.close()
    if len(df) < 10: return 999.0 # 데이터 부족
    
    for col in ['high', 'low', 'close']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['range_pct'] = (df['high'] - df['low']) / df['close']
    
    recent_5d = df.head(5)
    prev_5d = df.iloc[5:10]
    
    score = recent_5d['range_pct'].mean()
    
    # 변동성 추세 체크: 최근이 이전보다 크게 벌어졌으면 제외 (1.1배 허용)
    if score > prev_5d['range_pct'].mean() * 1.1: return 999.0
    
    return score

def get_trend_candidates_db():
    """정조준 필터 v5.2: 200일선 우상향 기울기 + 완전정배열 + VDU"""
    conn = get_connection()
    res = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()
    if not res or not res[0]:
        conn.close(); return pd.DataFrame()
    max_date = res[0]
    
    # 1개월(20거래일) 전 날짜 구하기
    prev_date_res = conn.execute(f"SELECT date FROM daily_analysis WHERE code='0001' AND date < '{max_date}' ORDER BY date DESC LIMIT 20, 1").fetchone()
    prev_date = prev_date_res[0] if prev_date_res else '00000000'
    
    query = f"""
    SELECT 
        d.date, d.code, m.name, m.market_type,
        d.close, d.amount, d.volume, d.rs_score,
        (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
        d.high_52w, d.low_52w, d.sma_20, d.sma_50, d.sma_150, d.sma_200,
        d.volume_sma_50, m.roe, m.bsop_prfi, m.thtr_ntin,
        (SELECT d2.sma_200 FROM daily_analysis d2 WHERE d2.code = d.code AND d2.date = '{prev_date}') as sma_200_prev
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND d.amount >= 3000000000
      -- [거장의 필터] 200일선이 최소 1개월 전보다 높아야 함 (상승 기울기)
      AND d.sma_200 > sma_200_prev
      -- [완전 정배열] 가격 > 20 > 50 > 150 > 200
      AND d.close > d.sma_20 AND d.sma_20 > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200
      -- [VDU 필터] 거래량 건조 (평균의 80% 미만)
      AND d.volume < (d.volume_sma_50 * 0.8)
      AND d.rs_score >= 80
      AND ((m.bsop_prfi > 0 AND m.thtr_ntin > 0) OR (d.rs_score >= 90))
    ORDER BY d.rs_score DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def calculate_survival_trade(row):
    entry = get_breakout_price(row['high_52w'])
    stop_fixed = entry * 0.93
    stop_sma20 = row['sma_20'] or 0
    stop = max(stop_fixed, stop_sma20)
    stop = adjust_to_tick(stop, 'down')
    is_broken = row['close'] < stop
    risk_pct = (entry - stop) / entry if entry > stop else 0.07
    weight = min(20, int(1.0 / risk_pct))
    return entry, stop, f"{weight}%", is_broken

def print_stock_row(row):
    e, s, w, brk = calculate_survival_trade(row)
    # 생존자 필터에 의해 brk인 종목은 여기까지 오지 않음
    p_vcp = row.get('vcp_score', 0)
    v_vcp = row.get('vcp_ratio', 0)
    mark = "⏳" if p_vcp > 0.04 else "🎯"
    
    quality = row.get('quality', 'Unknown')
    name_display = f"*{row['name']}" if "💎" in quality else row['name']
    
    # P-VCP(가격 긴밀함)와 R-VCP(변동성 비율) 병행 표기
    print(f" {mark} {name_display:<12} | RS {row['rs_score']:2.0f} | {quality} | P-VCP {p_vcp:.2f} | R-VCP {v_vcp:.2f} | 🎯:{e:>8,} | 🛡️:{s:>8,}")

def generate_full_report():
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    print("=" * 115)
    print(f" [TrendHunter v5.5 Survival Master] 거장의 생존 원칙 및 RS 주도주 리포트 | {max_date}")
    print("=" * 115)
    
    # 1. 시장 온도계
    kospi = conn.execute(f"SELECT close, sma_50, sma_200 FROM daily_analysis WHERE code='0001' AND date='{max_date}'").fetchone()
    kosdaq = conn.execute(f"SELECT close, sma_50, sma_200 FROM daily_analysis WHERE code='1001' AND date='{max_date}'").fetchone()
    
    if kospi and kosdaq:
        p_status = "UP" if kospi[0] > kospi[1] else "DOWN"
        q_status = "UP" if kosdaq[0] > kosdaq[1] else "DOWN"
        print(f" 🌡️ 시장 상태: KOSPI {p_status} ({kospi[0]:,.0f}) | KOSDAQ {q_status} ({kosdaq[0]:,.0f})")
    
    total_cnt = conn.execute(f"SELECT COUNT(*) FROM daily_analysis WHERE date='{max_date}' AND rs_score IS NOT NULL").fetchone()[0]
    stage2_cnt = conn.execute(f"SELECT COUNT(*) FROM daily_analysis WHERE date='{max_date}' AND close > sma_50 AND sma_50 > sma_150 AND sma_150 > sma_200").fetchone()[0]
    stage2_pct = (stage2_cnt / total_cnt * 100) if total_cnt > 0 else 0
    print(f" 🔥 시장 열기: Stage 2 비율 {stage2_pct:.1f}%")
    print("-" * 115)

    # 2. 시장 주도 섹터 사전 분석
    raw_df = get_trend_candidates_db()
    if not raw_df.empty:
        all_raw_themes = []
        for code in raw_df['code'].head(50):
            themes = get_themes_for_stock(code)
            all_raw_themes.extend(themes)
        common_themes = Counter(all_raw_themes).most_common(5)
        theme_str = " | ".join([f"#{t}({c})" for t, c in common_themes])
        print(f" 🚀 시장 주도 섹터: {theme_str}")
        print("-" * 115)

def save_to_db(conn, candidates, track_name, date):
    """스크리닝 결과를 trade_plan 테이블에 저장"""
    if not candidates: return
    
    data = []
    for c in candidates:
        # Track 2의 경우 필드명이 다를 수 있음
        if track_name == 'TRACK2':
            entry = 0
            stop = 0
            weight = "10%"
            rs = c.get('roe', 0) # Track 2는 RS 대신 ROE나 수익률을 중요 지표로 사용
            vcp = 0
            rationale = f"Live Yield {c['live_yield']:.1f}% / Payout {c['payout_ratio']:.0f}%"
        else:
            entry, stop, weight, _ = calculate_survival_trade(c)
            rs = c['rs_score']
            vcp = c.get('vcp_ratio', 0)
            rationale = c.get('quality', '')

        data.append((
            date, c['code'], c['name'], 
            int(entry), int(stop), weight, 
            'READY', track_name, 
            float(rs), float(vcp), rationale
        ))
    
    conn.executemany("""
        INSERT INTO trade_plan (date, code, name, entry_price, stop_price, weight, status, track, rs_score, vcp_ratio, rationale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

def generate_full_report():
    conn = get_connection()
    max_date = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()[0]
    
    # [v5.6] 기존 리포트 초기화 (중복 방지)
    conn.execute("DELETE FROM trade_plan WHERE date = ?", (max_date,))
    
    print("=" * 115)
    print(f" [TrendHunter v5.5 Survival Master] 거장의 생존 원칙 및 RS 주도주 리포트 | {max_date}")
    print("=" * 115)
    
    # ... (시장 온도계 등 기존 출력 로직 유지) ...
    kospi = conn.execute(f"SELECT close, sma_50, sma_200 FROM daily_analysis WHERE code='0001' AND date='{max_date}'").fetchone()
    kosdaq = conn.execute(f"SELECT close, sma_50, sma_200 FROM daily_analysis WHERE code='1001' AND date='{max_date}'").fetchone()
    
    if kospi and kosdaq:
        p_status = "UP" if kospi[0] > kospi[1] else "DOWN"
        q_status = "UP" if kosdaq[0] > kosdaq[1] else "DOWN"
        print(f" 🌡️ 시장 상태: KOSPI {p_status} ({kospi[0]:,.0f}) | KOSDAQ {q_status} ({kosdaq[0]:,.0f})")
    
    total_cnt = conn.execute(f"SELECT COUNT(*) FROM daily_analysis WHERE date='{max_date}' AND rs_score IS NOT NULL").fetchone()[0]
    stage2_cnt = conn.execute(f"SELECT COUNT(*) FROM daily_analysis WHERE date='{max_date}' AND close > sma_50 AND sma_50 > sma_150 AND sma_150 > sma_200").fetchone()[0]
    stage2_pct = (stage2_cnt / total_cnt * 100) if total_cnt > 0 else 0
    print(f" 🔥 시장 열기: Stage 2 비율 {stage2_pct:.1f}%")
    print("-" * 115)

    # 2. 시장 주도 섹터 사전 분석
    raw_df = get_trend_candidates_db()
    if not raw_df.empty:
        all_raw_themes = []
        for code in raw_df['code'].head(50):
            themes = get_themes_for_stock(code)
            all_raw_themes.extend(themes)
        common_themes = Counter(all_raw_themes).most_common(5)
        theme_str = " | ".join([f"#{t}({c})" for t, c in common_themes])
        print(f" 🚀 시장 주도 섹터: {theme_str}")
        print("-" * 115)

    # 3. 정밀 필터링 (Survival & Dynamic VCP)
    strict_candidates = []
    relaxed_candidates = []
    failed_logs = []  # 탈락 사유 수집
    
    if not raw_df.empty:
        for _, row in raw_df.iterrows():
            entry, stop, weight, is_broken = calculate_survival_trade(row)
            if is_broken: 
                failed_logs.append({'name': row['name'], 'rs': row['rs_score'], 'reason': f"🛡️ 손절선 이탈 ({int(row['close']):,} < {int(stop):,})"})
                continue
            
            vcp_score = check_chart_pattern_score(row['code'])
            row['vcp_score'] = vcp_score
            row['quality'] = get_supply_quality(row['code'])
            
            if "이탈" in row['quality']: 
                failed_logs.append({'name': row['name'], 'rs': row['rs_score'], 'reason': f"🚨 수급 이탈 ({row['quality']})"})
                continue
            
            row['themes'] = get_themes_for_stock(row['code'])
            
            if vcp_score <= 0.04:
                strict_candidates.append(row)
            elif vcp_score <= 0.06:
                relaxed_candidates.append(row)
            else:
                failed_logs.append({'name': row['name'], 'rs': row['rs_score'], 'reason': f"📈 변동성 초과 (VCP {vcp_score:.1%} > 6%)"})

    # 4. 결과 출력 및 DB 저장
    if strict_candidates:
        print(" [🎯 TRACK 1: 거장의 정조준 (Strict 4%)] - 가장 강한 놈부터 정렬")
        save_to_db(conn, strict_candidates, 'TRACK1_STRICT', max_date) # DB 저장
        for s in sorted(strict_candidates, key=lambda x: x['rs_score'], reverse=True):
            print_stock_row(s)
        print("-" * 115)
    
    if relaxed_candidates:
        print(" [⚠️ TRACK 1: 현실적 차선책 (Relaxed 6%)] - 상위 RS 3선")
        # Relaxed는 상위 3개만 저장
        top3_relaxed = sorted(relaxed_candidates, key=lambda x: x['rs_score'], reverse=True)[:3]
        save_to_db(conn, top3_relaxed, 'TRACK1_RELAXED', max_date) # DB 저장
        for s in top3_relaxed:
            print_stock_row(s)
        print("-" * 115)

    if not strict_candidates and not relaxed_candidates:
        print(" [!] 현재 진입 가능한 생존 종목이 없습니다. 관망하십시오.")
        if failed_logs:
            print("\n [🔍 관망 브리핑: 주요 후보 탈락 사유 (RS Top 5)]")
            failed_logs.sort(key=lambda x: x['rs'], reverse=True)
            for f in failed_logs[:5]:
                 print(f"  - {f['name']:<12} | RS {f['rs']:>3.0f} | {f['reason']}")
            print("-" * 115)

    # TRACK 2: 배당 마법공식
    query_div = f"""
    SELECT 
        m.code, m.name, d.close, 
        (CAST(m.per_stock_dvdn_amt AS REAL) / NULLIF(d.close, 0)) * 100 as live_yield,
        m.roe, m.eps, m.per_stock_dvdn_amt
    FROM daily_analysis d
    JOIN master_info m ON d.code = m.code
    WHERE d.date = '{max_date}'
      AND live_yield BETWEEN 3.0 AND 15.0
      AND (m.roe >= 8.0 OR m.eps > 0)
      AND m.eps > 0
    GROUP BY m.code
    """
    div_raw = pd.read_sql_query(query_div, conn)
    
    if not div_raw.empty:
        div_raw['payout_ratio'] = (div_raw['per_stock_dvdn_amt'] / div_raw['eps']) * 100
        div_df = div_raw[(div_raw['payout_ratio'] >= 10) & (div_raw['payout_ratio'] <= 100)].copy()
        
        if not div_df.empty:
            div_df['magic_score'] = div_df['live_yield'] * 0.7 + div_df['roe'].apply(lambda x: max(x, 0)) * 0.3
            div_df = div_df.sort_values(by='magic_score', ascending=False).head(5)
            
            # DB 저장 (DataFrame -> List of Dict 변환 필요)
            save_to_db(conn, div_df.to_dict('records'), 'TRACK2', max_date)
            
            print(f" [🛡️ TRACK 2: 배당 마법공식 Top 5 (Live Yield Quality)]")
            for _, r in div_df.iterrows():
                print(f" ▶ {r['name']:<12} | 수익률:{r['live_yield']:>5.1f}% | ROE:{r['roe']:>5.1f}% | 성향:{r['payout_ratio']:>4.0f}%")
            print("-" * 115)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    generate_full_report()
