"""
[TrendHunter v22.5] Quantitative Market Screener
Focus: Stage 2 Momentum, RIP/DIP Strategies, and Dividend Value.
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
    if price % tick == 0: return int(price)
    if method == 'up':
        return int((price // tick + 1) * tick)
    else:
        return int((price // tick) * tick)

def get_breakout_price(high_52w):
    target = high_52w * 1.005
    return adjust_to_tick(target, 'up')

def calculate_survival_trade(row, strategy='RIP'):
    if strategy == 'DIP':
        ma21 = row.get('sma_21') or row['close']
        struct_low = row.get('low_20d') or ma21 * 0.95
        entry = adjust_to_tick(ma21, 'up')
        stop = adjust_to_tick(max(entry * 0.92, struct_low, entry * 0.95), 'down')
        pivot = adjust_to_tick(entry * 0.98, 'down')
        profit = adjust_to_tick(entry * 1.10, 'up')
    else:
        entry = get_breakout_price(row['high_52w'])
        ma21 = row.get('sma_21') or 0
        struct_low = row.get('low_20d') or entry * 0.93
        stop = adjust_to_tick(max(entry * 0.92, min(struct_low, entry * 0.97), ma21), 'down')
        pivot = adjust_to_tick(row['high_52w'] * 1.002, 'up')
        profit = adjust_to_tick(entry * 1.15, 'up')
    
    risk_pct = (entry - stop) / entry if entry > stop else 0.07
    weight = min(20, int(1.2 / risk_pct)) if risk_pct > 0 else 10
    
    rs_t = row.get('rs_score', 0); rs_m = row.get('rs_score_master', 0)
    status = "UP" if rs_m > rs_t + 10 else ("DOWN" if rs_m < rs_t - 10 else "STABLE")
    return entry, stop, f"{weight}%", row['close'] < stop, status, pivot, profit

def print_stock_row(row):
    strategy = 'DIP' if 'DIP' in str(row.get('type','')) else 'RIP'
    e, s, w, brk, st, pv, pr = calculate_survival_trade(row, strategy)
    vdu = "*" if (row['volume'] / row['volume_sma_50'] if row['volume_sma_50'] > 0 else 1.0) <= 0.8 else " "
    clean_name = row['name'][:7] + ".." if len(row['name']) > 8 else row['name'].split(' ')[0]
    print(f" {vdu} {clean_name:<10} | RS(T:{row['rs_score']:2.0f} M:{row['rs_score_master']:2.0f}) | {row.get('type','TR'):<8} | E:{e:>8,} | S:{s:>8,}")

def save_to_db(conn, candidates, track_name, date):
    if not candidates: return
    data = []
    seen_symbols = set()
    for c in candidates:
        if c['code'] in seen_symbols: continue
        seen_symbols.add(c['code'])
        
        if track_name == 'TRACK2':
            entry = c['close']; stop = 0; weight = "10%"; rs = c['roe']; rs_m = 0; vcp = 0; rat = f"Yield {c['live_yield']:.1f}%"
            pivot = entry; profit = adjust_to_tick(entry * 1.2, 'up')
        else:
            strategy = 'DIP' if 'DIP' in str(c.get('type','')) else 'RIP'
            entry, stop, weight, _, _, pivot, profit = calculate_survival_trade(c, strategy)
            rs = c['rs_score']; rs_m = c['rs_score_master']; vcp = c.get('vcp_score', 0); rat = c.get('type', 'NORMAL')
        data.append((date, c['code'], c['name'], int(entry), int(stop), weight, 'READY', track_name, float(rs), float(rs_m), float(vcp), rat, int(pivot), int(profit)))
    conn.executemany("INSERT INTO trade_plan (date, code, name, entry_price, stop_price, weight, status, track, rs_score, rs_score_master, vcp_ratio, rationale, pivot_price, profit_target) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", data)

def get_candidates(conn, max_date):
    query = f"""
        WITH RecentData AS (
            SELECT *, 
                   MIN(low) OVER (PARTITION BY code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as low_20d
            FROM daily_analysis
        )
        SELECT d.*, m.name, m.roe 
        FROM RecentData d 
        JOIN master_info m ON d.code = m.code 
        WHERE d.date = '{max_date}' 
          AND d.amount >= 1000000000 
          AND d.close > d.sma_200 
          AND d.rs_score >= 80 
          AND d.rs_score_master >= 80
    """
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
        vcp = (row['high'] - row['low']) / row['close']
        rip_threshold = 0.90 if row['rs_score_master'] >= 96 else 0.95
        if row['close'] >= (row['high_52w'] * rip_threshold) and is_vcp_tight(vcp, row['rs_score_master']):
            entry, stop, _, is_broken, _, pivot, profit = calculate_survival_trade(row, 'RIP')
            if not is_broken:
                rip_row = row.copy(); rip_row['vcp_score'] = vcp; rip_row['type'] = "RIP"
                rip_candidates.append(rip_row)
            
        ma21 = row.get('sma_21') or 0
        vdu_ratio = row['volume'] / row['volume_sma_50'] if row['volume_sma_50'] > 0 else 1.0
        if ma21 > 0 and row['low'] <= ma21 * 1.02 and row['close'] >= ma21 * 0.98:
            entry, stop, _, is_broken, _, pivot, profit = calculate_survival_trade(row, 'DIP')
            if not is_broken:
                pattern = check_candle_pattern(row)
                if pattern or vdu_ratio <= 0.8:
                    dip_row = row.copy(); dip_row['vcp_score'] = vcp
                    dip_row['type'] = f"DIP"
                    dip_candidates.append(dip_row)

    print(f"\n [TrendHunter v22.5] Market Report | {max_date}")
    tg_msg = f"<b>TrendHunter Report ({max_date})</b>\n──────────────────\n"
    
    if rip_candidates:
        print("\n [RIP: BREAKOUT]"); rip_candidates = sorted(rip_candidates, key=lambda x: x['rs_score_master'], reverse=True)[:5]
        save_to_db(conn, rip_candidates, 'TRACK1_RIP', max_date)
        tg_msg += "\n<b>[RIP] BREAKOUT</b>\n"
        for s in rip_candidates: 
            print_stock_row(s)
            e, sl, w, _, _, _, _ = calculate_survival_trade(s, 'RIP')
            tg_msg += f"· {s['name']} | E {e:,} | S {sl:,} ({w})\n"
            
    if dip_candidates:
        print("\n [DIP: PULLBACK]"); dip_candidates = sorted(dip_candidates, key=lambda x: x['rs_score_master'], reverse=True)[:5]
        save_to_db(conn, dip_candidates, 'TRACK1_DIP', max_date)
        tg_msg += "\n<b>[DIP] PULLBACK</b>\n"
        for s in dip_candidates: 
            print_stock_row(s)
            e, sl, w, _, _, _, _ = calculate_survival_trade(s, 'DIP')
            tg_msg += f"· {s['name']} | E {e:,} | S {sl:,} ({w})\n"
    
    # [TRACK_EX] Masters' Leaderboard (Scoring System)
    # 1. 주도 섹터 추출 (Top 5로 확장)
    sector_query = "SELECT s.category_name, COUNT(*) as cnt FROM daily_analysis d JOIN sectors_themes s ON d.code = s.code WHERE d.date = ? AND d.rs_score_master >= 85 GROUP BY category_name ORDER BY cnt DESC LIMIT 5"
    top_sectors = [r[0] for r in conn.execute(sector_query, (max_date,)).fetchall()]
    
    # 2. 전 종목 스코어링 쿼리
    query_ex = f"""
        SELECT d.*, m.name, m.roe, s.category_name,
               (CASE WHEN s.category_name IN ({','.join(['?' for _ in top_sectors])}) THEN 20 ELSE 0 END) +
               (CASE WHEN d.volume < (d.volume_sma_50 * 0.8) THEN 20 ELSE 0 END) +
               (CASE WHEN d.close > d.sma_50 AND d.sma_50 > d.sma_150 AND d.sma_150 > d.sma_200 THEN 40 ELSE 0 END) +
               (CASE WHEN (d.high - d.low) / d.close < 0.04 THEN 20 ELSE 0 END) as match_score
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
        JOIN sectors_themes s ON d.code = s.code
        WHERE d.date = '{max_date}'
          AND d.close BETWEEN 1000 AND 50000
          AND d.rs_score_master >= 80
          AND d.amount >= 1000000000
        GROUP BY d.code
        ORDER BY match_score DESC, d.rs_score_master DESC
        LIMIT 5
    """
    ex_df = pd.read_sql_query(query_ex, conn, params=top_sectors)
    
    if not ex_df.empty:
        print(f"\n [TRACK EX: MASTERS' LEADERBOARD] - Top Sectors: {', '.join(top_sectors[:3])}")
        tg_msg += f"\n<b>[EX] MASTERS' LEADERBOARD</b>\n"
        ex_candidates = []
        for _, row in ex_df.iterrows():
            e, sl, w, _, _, _, _ = calculate_survival_trade(row, 'RIP')
            ex_row = row.copy()
            ex_row['vcp_score'] = (row['high'] - row['low']) / row['close']
            ex_row['type'] = f"EX({int(row['match_score'])}pt)"
            ex_candidates.append(ex_row)
            
            # 리포트 출력
            vdu = "*" if row['volume'] < row['volume_sma_50'] * 0.8 else " "
            print(f" {vdu} {row['name']:<10} | Score:{int(row['match_score']):>3} | RS:{row['rs_score_master']:2.0f} | E:{e:>8,} | S:{sl:>8,}")
            tg_msg += f"· {row['name']} | Score {int(row['match_score'])} | E {e:,} (RS {row['rs_score_master']:.0f})\n"
        
        save_to_db(conn, ex_candidates, 'TRACK_EX', max_date)

    # Track 2
    div_df = pd.read_sql_query(f"SELECT m.code, m.name, d.close, (CAST(m.per_stock_dvdn_amt AS REAL)/NULLIF(d.close,0))*100 as live_yield, m.roe, m.eps, m.per_stock_dvdn_amt FROM daily_analysis d JOIN master_info m ON d.code = m.code WHERE d.date='{max_date}' AND m.eps!=0", conn)
    div_df['payout'] = (div_df['per_stock_dvdn_amt'] / div_df['eps']) * 100
    div_res = div_df[(div_df['live_yield'].between(3.0, 12.0)) & (div_df['payout'].between(10, 100)) & (div_df['roe']>=8)].copy()
    if not div_res.empty:
        div_res['magic_score'] = div_res['live_yield'] * 0.7 + div_res['roe'] * 0.3
        div_res = div_res.sort_values(by='magic_score', ascending=False).head(5)
        save_to_db(conn, div_res.to_dict('records'), 'TRACK2', max_date)
        print("\n [TRACK 2: DIVIDEND MAGIC]")
        tg_msg += "\n<b>[DIV] DIVIDEND MAGIC</b>\n"
        for _, r in div_res.iterrows(): 
            print(f" ▶ {r['name']:<12} | Yield:{r['live_yield']:>5.1f}% | Score:{r['magic_score']:.2f}")
            tg_msg += f"· {r['name']} | Yield {r['live_yield']:.1f}% | ROE {r['roe']:.1f}%\n"

    tg_msg += "\n──────────────────\nDetailed data on Dashboard."
    conn.commit(); conn.close()
    notifier.send_message(tg_msg, sync=True)
    print("\n✅ Report complete.")

if __name__ == "__main__": generate_full_report()
