"""
[TrendHunter v22.0 Dual-Track]
RIP (Breakout) & DIP (Pullback) 통합 리포트 엔진
"""
import pandas as pd
import numpy as np
import sqlite3
from collections import Counter
from src.db import get_connection
from src.utils.notifier import notifier
from src.analysis.patterns import check_candle_pattern, is_vcp_tight

def get_tick_size(price):
    if price < 2000: return 1
    elif price < 5000: return 5
    elif price < 20000: return 10
    elif price < 50000: return 50
    elif price < 200000: return 100
    else: return 500

def adjust_to_tick(price, method='up'):
    tick = get_tick_size(price)
    return ((int(price) // tick) + (1 if method == 'up' else 0)) * tick

def get_breakout_price(high_52w):
    target = high_52w * 1.005
    return adjust_to_tick(target, 'up')

def calculate_survival_trade(row):
    entry = get_breakout_price(row['high_52w'])
    ma21 = row.get('sma_21') or 0
    stop = adjust_to_tick(max(entry * 0.93, ma21), 'down')
    risk_pct = (entry - stop) / entry if entry > stop else 0.07
    weight = min(20, int(1.0 / risk_pct))
    
    rs_t = row.get('rs_score', 0); rs_m = row.get('rs_score_master', 0)
    status = "🔥폭발" if rs_m > rs_t + 10 else ("🧊쇠퇴" if rs_m < rs_t - 10 else "✨유지")
    return entry, stop, f"{weight}%", row['close'] < stop, status

def print_stock_row(row):
    e, s, w, brk, st = calculate_survival_trade(row)
    vdu = "💎" if (row['volume'] / row['volume_sma_50'] if row['volume_sma_50'] > 0 else 1.0) <= 0.8 else "  "
    clean_name = row['name'][:7] + ".." if len(row['name']) > 8 else row['name'].split(' ')[0]
    print(f" {vdu} {clean_name:<10} | RS(T:{row['rs_score']:2.0f} M:{row['rs_score_master']:2.0f}) | {row.get('type','TR'):<8} | 🎯:{e:>8,} | 🛡️:{s:>8,}")

def save_to_db(conn, candidates, track_name, date):
    data = []
    for c in candidates:
        if track_name == 'TRACK2':
            entry = c['close']; stop = 0; weight = "10%"; rs = c['roe']; rs_m = 0; vcp = 0; rat = f"Yield {c['live_yield']:.1f}%"
        else:
            entry, stop, weight, _, _ = calculate_survival_trade(c)
            rs = c['rs_score']; rs_m = c['rs_score_master']; vcp = c.get('vcp_score', 0); rat = c.get('type', 'NORMAL')
        data.append((date, c['code'], c['name'], int(entry), int(stop), weight, 'READY', track_name, float(rs), float(rs_m), float(vcp), rat))
    conn.executemany("INSERT INTO trade_plan (date, code, name, entry_price, stop_price, weight, status, track, rs_score, rs_score_master, vcp_ratio, rationale) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", data)

def get_candidates(conn, max_date):
    query = f"SELECT d.*, m.name, m.roe FROM daily_analysis d JOIN master_info m ON d.code = m.code WHERE d.date = '{max_date}' AND d.amount >= 1000000000 AND d.close > d.sma_200 AND d.rs_score >= 80 AND d.rs_score_master >= 80"
    return pd.read_sql_query(query, conn)

def generate_full_report():
    conn = get_connection()
    res_date = conn.execute("SELECT date FROM daily_analysis GROUP BY date HAVING COUNT(*) > 100 ORDER BY date DESC LIMIT 1").fetchone()
    if not res_date: return
    max_date = res_date[0]
    conn.execute("DELETE FROM trade_plan WHERE date = ?", (max_date,))
    
    df = get_candidates(conn, max_date)
    rip_candidates, dip_candidates = [], []
    
    for _, row in df.iterrows():
        entry, stop, _, is_broken, _ = calculate_survival_trade(row)
        if is_broken or row['close'] < stop: continue
        
        vcp = (row['high'] - row['low']) / row['close'] # 실시간 VCP 근사치
        
        # [RIP] Breakout: 신고가 근처 응축
        rip_threshold = 0.90 if row['rs_score_master'] >= 96 else 0.95
        if row['close'] >= (row['high_52w'] * rip_threshold) and is_vcp_tight(vcp, row['rs_score_master']):
            rip_row = row.copy()
            rip_row['vcp_score'] = vcp; rip_row['type'] = "RIP"
            rip_candidates.append(rip_row)
            
        # [DIP] Pullback: 21일선 근처 지지 + VDU 또는 캔들패턴
        ma21 = row.get('sma_21') or 0
        vdu_ratio = row['volume'] / row['volume_sma_50'] if row['volume_sma_50'] > 0 else 1.0
        
        # 21일선 근처 (Low가 MA21 +2% 이내 && Close가 MA21 -2% 이상)
        if ma21 > 0 and row['low'] <= ma21 * 1.02 and row['close'] >= ma21 * 0.98:
            pattern = check_candle_pattern(row)
            if pattern or vdu_ratio <= 0.8:
                dip_row = row.copy()
                dip_row['vcp_score'] = vcp
                dip_row['type'] = f"DIP({pattern or 'VDU'})"
                dip_candidates.append(dip_row)

    # Output & Telegram
    print(f"\n [TrendHunter v22.0] DUAL-TRACK | {max_date}")
    if rip_candidates:
        print("\n [🚀 RIP: BREAKOUT]"); rip_candidates = sorted(rip_candidates, key=lambda x: x['rs_score_master'], reverse=True)[:5]
        save_to_db(conn, rip_candidates, 'TRACK1_RIP', max_date)
        for s in rip_candidates: print_stock_row(s)
    if dip_candidates:
        print("\n [💎 DIP: PULLBACK]"); dip_candidates = sorted(dip_candidates, key=lambda x: x['rs_score_master'], reverse=True)[:5]
        save_to_db(conn, dip_candidates, 'TRACK1_DIP', max_date)
        for s in dip_candidates: print_stock_row(s)
    
    # Track 2
    div_df = pd.read_sql_query(f"SELECT m.code, m.name, d.close, (CAST(m.per_stock_dvdn_amt AS REAL)/NULLIF(d.close,0))*100 as live_yield, m.roe, m.eps, m.per_stock_dvdn_amt FROM daily_analysis d JOIN master_info m ON d.code = m.code WHERE d.date='{max_date}' AND m.eps!=0", conn)
    div_df['payout'] = (div_df['per_stock_dvdn_amt'] / div_df['eps']) * 100
    div_res = div_df[(div_df['live_yield'].between(3,12)) & (div_df['payout'].between(10,100)) & (div_df['roe']>=8)].copy()
    if not div_res.empty:
        div_res['magic_score'] = div_res['live_yield'] * 0.7 + div_res['roe'] * 0.3
        div_res = div_res.sort_values(by='magic_score', ascending=False).head(5)
        save_to_db(conn, div_res.to_dict('records'), 'TRACK2', max_date)
        print("\n [🛡️ TRACK 2: MAGIC DIVIDEND]")
        for _, r in div_res.iterrows(): print(f" ▶ {r['name']:<12} | Yield:{r['live_yield']:>5.1f}% | Score:{r['magic_score']:.2f}")

    conn.commit(); conn.close()
    
    # Telegram Message (Simplified)
    tg_msg = f"🚀 <b>TrendHunter 주도주 리포트 ({max_date})</b>\n──────────────────\n"
    if rip_candidates:
        tg_msg += "\n<b>🚀 [RIP] BREAKOUT</b>\n"
        for s in rip_candidates: tg_msg += f"· {s['name']} | RS(T:{s['rs_score']:.0f} M:{s['rs_score_master']:.0f}) | 🎯{get_breakout_price(s['high_52w']):,}\n"
    if dip_candidates:
        tg_msg += "\n<b>💎 [DIP] PULLBACK</b>\n"
        for s in dip_candidates: 
            _, stop, _, _, _ = calculate_survival_trade(s)
            tg_msg += f"· {s['name']} | {s['type']} | RS(T:{s['rs_score']:.0f} M:{s['rs_score_master']:.0f}) | 🛡️{stop:,}\n"
    notifier.send_message(tg_msg, sync=True)

if __name__ == "__main__": generate_full_report()
