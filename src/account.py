"""계좌 잔고 및 실시간 매도 감시(Stop-loss) 연동 모듈."""
import os
import requests
import json
import sqlite3
from src.auth import get_access_token, BASE_URL, APP_KEY, APP_SECRET, load_config_from_db, MODE

# DB 설정 로드
db_conf = {}
try:
    db_conf = load_config_from_db()
except:
    pass

CANO = (db_conf.get("KIS_CANO") or os.getenv("CANO", "")).replace("-", "").strip()
ACNT_PRDT_CD = db_conf.get("KIS_ACNT_PRDT_CD") or os.getenv("ACNT_PRDT_CD", "01")

# [v6.3] 절대 경로 확보
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "TrendHunter", "db", "stock_info.db")

def get_db_stop_prices():
    """DB(trade_plan)에서 설정된 감시가(stop_price)를 가져옴."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT code, stop_price 
            FROM trade_plan 
            WHERE stop_price > 0
        """
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        
        # [v6.1] 코드 문자열 처리 및 공백 제거 (타입 불일치 방지)
        stop_map = {str(row[0]).strip().zfill(6): row[1] for row in rows}
        return stop_map
    except Exception as e:
        return {}

def get_account_balance():
    """계좌 잔고 및 보유 종목 조회 (API 호출)."""
    token = get_access_token()
    if not token or not CANO: return None

    path = "/uapi/domestic-stock/v1/trading/inquire-balance"
    url = f"{BASE_URL}{path}"
    tr_id = "TTTC8434R" if MODE == "real" else "VTTC8434R"
    
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }
    
    params = {
        "CANO": CANO, "ACNT_PRDT_CD": ACNT_PRDT_CD, "AFHR_FLPR_YN": "N",
        "OFL_YN": "N", "INQR_DVSN": "02", "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N", "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00", "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""
    }
    
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        data = res.json()
        if data['rt_cd'] != '0': return None
        
        # [핵심] DB에서 수동/자동 설정된 감시가 가져오기
        stop_prices = get_db_stop_prices()
        return parse_balance(data, stop_prices)
    return None

def parse_balance(data, stop_prices):
    """API 응답 파싱 및 실질 수익/예상 손익 분리 계산."""
    output1 = data.get('output1', [])
    output2 = data.get('output2', [])
    
    summary = {}
    if output2:
        row = output2[0]
        summary = {
            "total_asset": int(row.get("tot_evlu_amt", 0)),
            "deposit": int(row.get("dnca_tot_amt", 0)),
            "total_buy": int(row.get("pchs_amt_smtl_amt", 0)),
        }
        
    holdings = []
    total_survival_profit = 0  # 감시가 기준 확정 수익 (Shield Profit)
    total_floating_profit = 0  # 현재가 기준 평가 수익 (Market Profit)
    
    for item in output1:
        qty = int(item.get("hldg_qty") or item.get("hldg_qty", 0))
        if qty == 0: continue
        
        # [v6.2] 필드명 다변화 대응 (pdno, prdt_no 등)
        code = str(item.get("pdno") or item.get("prdt_no") or "").strip()
        buy_price = float(item.get("pchs_avg_pric") or 0)
        curr_price = int(item.get("prpr") or 0)
        
        # 1. 감시가(Shield) 연동
        stop_price = stop_prices.get(code, 0)
        
        # 2. 생존 확정 수익 (Shield Profit) = (감시가 - 평단가) * 수량
        # 감시가가 평단보다 높으면 '확정 수익', 낮으면 '최대 허용 손실'
        survival_profit = int((stop_price - buy_price) * qty) if stop_price > 0 else 0
        total_survival_profit += survival_profit
        
        # 3. 현재 예상 수익 (Floating Profit) = (현재가 - 평단가) * 수량
        floating_profit = int((curr_price - buy_price) * qty)
        total_floating_profit += floating_profit
        
        holdings.append({
            "code": code,
            "name": item.get("prdt_name") or item.get("prdt_nm"),
            "qty": qty,
            "buy_price": buy_price,
            "curr_price": curr_price,
            "stop_price": stop_price,
            "survival_profit": survival_profit,
            "floating_profit": floating_profit,
            "return_rate": float(item.get("evlu_pfls_rt") or 0)
        })
        
    summary["total_survival_profit"] = total_survival_profit
    summary["total_floating_profit"] = total_floating_profit
    return {"summary": summary, "holdings": holdings}

def sync_account_positions():
    """KIS 실잔고를 DB(account_positions_audit)에 동기화. (매도 시 감시 해제용)"""
    balance = get_account_balance()
    if not balance: return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # 1. DB의 모든 종목 수량 0으로 초기화 (잔고에 없는 종목 제거용)
        cur.execute("UPDATE account_positions_audit SET qty = 0")
        
        for h in balance['holdings']:
            symbol = h['code']
            qty = h['qty']
            curr_price = h['curr_price']
            avg_price = h['buy_price']

            # 2. DB에 존재여부 확인 및 업데이트
            cur.execute("SELECT symbol, peak_price FROM account_positions_audit WHERE symbol = ?", (symbol,))
            row = cur.fetchone()
            if row:
                peak = max(row[1] or 0, curr_price)
                cur.execute("""
                    UPDATE account_positions_audit 
                    SET qty = ?, peak_price = ?, updated_at = datetime('now', 'localtime') 
                    WHERE symbol = ?
                """, (qty, peak, symbol))
            else:
                # 신규 종목 (수동 매수 등)
                cur.execute("""
                    INSERT INTO account_positions_audit (symbol, entry_price, peak_price, qty, manual_shield, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
                """, (symbol, avg_price, curr_price, qty, int(avg_price * 0.95)))
        
        # 3. 수량이 0인 종목 정리 (매도된 종목 삭제)
        cur.execute("DELETE FROM account_positions_audit WHERE qty <= 0")
        conn.commit()
        conn.close()
        print(f"✅ [Sync] Account positions synchronized with KIS.")
    except Exception as e:
        print(f"❌ [Sync] Error during account synchronization: {e}")

def print_account_info():
    """CLI 출력용 함수 (스승님의 생존 전략 반영)."""
    result = get_account_balance()
    if not result: return

    s = result['summary']
    print("=" * 90)
    print(f" 💰 TrendHunter 실전 생존 리포트 (MODE: {'실전' if MODE=='real' else '모의투자'})")
    print("=" * 90)
    print(f" ▶ 총 자산 : {s['total_asset']:>15,} 원 (매입: {s['total_buy']:,} 원)")
    print(f" ▶ 예수금  : {s['deposit']:>15,} 원")
    print("-" * 90)
    
    # 상단 요약 바: 장부상 이익 vs 생존 확정 이익
    color_f = "\033[92m" if s['total_floating_profit'] >= 0 else "\033[91m"
    color_s = "\033[96m" if s['total_survival_profit'] >= 0 else "\033[93m"
    reset = "\033[0m"
    
    print(f" 📈 현재가 기준 예상 손익 (Floating): {color_f}{s['total_floating_profit']:>12,} 원{reset}")
    print(f" 🛡️  감시가 기준 생존 수익 (Shield  ): {color_s}{s['total_survival_profit']:>12,} 원{reset}")
    print("-" * 90)
    
    # 텔레그램 메시지 구성 (스승님 취향 저격)
    tg_msg = f"<b>💰 TrendHunter 실전 생존 리포트</b>\n"
    tg_msg += f"────────────────\n"
    tg_msg += f"▶ 총 자산: {s['total_asset']:,}원\n"
    tg_msg += f"▶ 예수금: {s['deposit']:,}원\n"
    tg_msg += f"────────────────\n"
    tg_msg += f"📈 <b>현재가 예상 손익 (Floating):</b> {s['total_floating_profit']:,}원\n"
    tg_msg += f"🛡️ <b>감시가 생존 수익 (Shield):</b> {s['total_survival_profit']:,}원\n"
    tg_msg += f"────────────────\n"

    if not result['holdings']:
        print(" [!] 보유 종목이 없습니다.")
        tg_msg += " [!] 현재 보유 종목이 없습니다.\n"
    else:
        print(f" {'종목명':<12} | {'수량':>4} | {'평단가':>8} | {'현재가':>8} | {'Shield':>8} | {'이익쿠션':>10} | {'현재손익':>10}")
        print("-" * 90)
        for h in result['holdings']:
            shield_str = f"{int(h['stop_price']):,}" if h['stop_price'] > 0 else " 미설정 "
            profit_cushion = int((h['curr_price'] - h['stop_price']) * h['qty']) if h['stop_price'] > 0 else 0
            
            c_sl = "\033[93m" if profit_cushion > 0 else ""
            c_fp = "\033[92m" if h['floating_profit'] >= 0 else "\033[91m"
            
            print(f" {h['name']:<12} | {h['qty']:>4,} | {int(h['buy_price']):>8,} | {h['curr_price']:>8,} | {shield_str:>8} | {c_sl}{profit_cushion:>10,}{reset} | {c_fp}{h['floating_profit']:>10,}{reset}")
            
            # 텔레그램 메시지 구성
            shield_tg = f"{int(h['stop_price']):,}" if h['stop_price'] > 0 else "미설정"
            tg_msg += f"<b>[{h['name']}]</b>\n"
            tg_msg += f" • 현재가: {h['curr_price']:,}원 ({h['return_rate']}%)\n"
            tg_msg += f" • Shield: {shield_tg}원\n"
            tg_msg += f" • <b>이익 쿠션: {profit_cushion:,}원</b>\n\n"
    
    risk_amt = int(s['total_asset'] * 0.01)
    final_balance = s['total_asset'] - s['total_floating_profit'] + s['total_survival_profit']
    
    print("-" * 90)
    print(f" 🛡️  초결벽주의 리스크 관리 (1% Rule)")
    print(f"  • 원금 대비 1% 허용 손실: {risk_amt:,} 원")
    print(f"  • 감시가 체결 시 최종 잔고: {final_balance:,} 원")
    print("=" * 90)

    tg_msg += f"────────────────\n"
    tg_msg += f"⚠️ <b>리스크 관리 (1% Rule)</b>\n"
    tg_msg += f" • 이번 라운드 허용 손실: {risk_amt:,}원\n"
    tg_msg += f" • <b>감시가 체결 시 최종 잔고: {final_balance:,}원</b>"

    # 텔레그램 전송
    from src.utils.notifier import notifier
    notifier.send_message(tg_msg)

if __name__ == "__main__":
    print_account_info()