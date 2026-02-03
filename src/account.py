"""계좌 잔고 및 보유 종목 조회 모듈."""
import os
import requests
import json
from dotenv import load_dotenv
from src.config import ROOT
from src.auth import get_access_token, BASE_URL, APP_KEY, APP_SECRET, load_config_from_db

# [v5.7] DB 설정 우선 로드
db_conf = {}
try:
    db_conf = load_config_from_db()
except:
    pass

# DB -> ENV 순서로 로드
CANO = (db_conf.get("KIS_CANO") or os.getenv("CANO", "")).replace("-", "").strip()
ACNT_PRDT_CD = db_conf.get("KIS_ACNT_PRDT_CD") or os.getenv("ACNT_PRDT_CD", "01")
MODE = db_conf.get("KIS_MODE") or os.getenv("MODE", "vts")

def get_account_balance():
    """계좌 잔고 및 보유 종목 조회 (API 호출)."""
    token = get_access_token()
    if not token:
        print("🚨 토큰 발급 실패")
        return None

    if not CANO:
        print("🚨 .env에 계좌번호(CANO)가 설정되지 않았습니다.")
        return None

    path = "/uapi/domestic-stock/v1/trading/inquire-balance"
    url = f"{BASE_URL}{path}"
    
    # TR ID 설정 (실전/모의 구분)
    tr_id = "TTTC8434R" if MODE == "real" else "VTTC8434R"
    
    print(f"🔍 DEBUG Info:")
    print(f"   - URL: {url}")
    print(f"   - TR_ID: {tr_id}")
    print(f"   - CANO: '{CANO}' (Length: {len(CANO)})")
    print(f"   - PRDT: '{ACNT_PRDT_CD}'")
    
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P" # 개인 고객 명시
    }
    
    # 디버깅을 위해 파라미터 구성 정보 출력 (값 자체는 가림)
    # print(f"DEBUG: CANO Length={len(CANO)}, ACNT_PRDT_CD={ACNT_PRDT_CD}")
    
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
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
    
    res = requests.get(url, headers=headers, params=params)
    
    if res.status_code == 200:
        data = res.json()
        if data['rt_cd'] != '0':
            print(f"🚨 API Error: {data['msg1']} ({data['msg_cd']})")
            print(f"   ℹ️  현재 실행 모드: {MODE.upper()}")
            print(f"   💡 팁: 실전 계좌는 MODE=real, 모의투자는 MODE=vts여야 합니다. .env를 확인하세요.")
            return None
        return parse_balance(data)
    else:
        print(f"🚨 HTTP Error: {res.status_code} {res.text}")
        return None

def parse_balance(data):
    """API 응답 파싱."""
    output1 = data.get('output1', []) # 보유 종목 리스트
    output2 = data.get('output2', []) # 계좌 요약 (리스트로 오지만 1건)
    
    summary = {}
    if output2:
        row = output2[0]
        summary = {
            "total_asset": int(row.get("tot_evlu_amt", 0)),      # 총평가금액
            "total_buy": int(row.get("pchs_amt_smtl_amt", 0)),   # 매입금액합계
            "total_pl": int(row.get("evlu_pfls_smtl_amt", 0)),   # 평가손익합계
            "total_return": float(row.get("evlu_pfls_rt", 0)),   # 수익률
            "deposit": int(row.get("dnca_tot_amt", 0)),          # 예수금
            "d2_deposit": int(row.get("prvs_rcdl_excc_amt", 0))  # D+2 예수금
        }
        
    holdings = []
    for item in output1:
        # 보유수량이 0인 경우(전량매도 후 잔여) 제외
        qty = int(item.get("hldg_qty", 0))
        if qty == 0: continue
        
        holdings.append({
            "code": item.get("pdno"),
            "name": item.get("prdt_name"),
            "qty": qty,
            "buy_price": float(item.get("pchs_avg_pric", 0)),    # 매입평균가
            "curr_price": int(item.get("prpr", 0)),              # 현재가
            "total_pl": int(item.get("evlu_pfls_amt", 0)),       # 평가손익
            "return_rate": float(item.get("evlu_pfls_rt", 0))    # 수익률
        })
        
    return {"summary": summary, "holdings": holdings}

def print_account_info():
    """CLI 출력용 함수."""
    result = get_account_balance()
    if not result: return

    s = result['summary']
    print("=" * 60)
    print(f" 💰 내 계좌 현황 ({'실전' if MODE=='real' else '모의투자'})")
    print("=" * 60)
    print(f" ▶ 총 자산 : {s['total_asset']:>15,} 원")
    print(f" ▶ 예수금  : {s['deposit']:>15,} 원")
    print(f" ▶ 총 손익 : {s['total_pl']:>15,} 원")
    
    # 수익률 색상 처리 (터미널용)
    color = "\033[91m" if s['total_return'] > 0 else "\033[94m" # 빨강/파랑
    reset = "\033[0m"
    print(f" ▶ 수익률  : {color}{s['total_return']:>14.2f} %{reset}")
    print("-" * 60)
    
    if not result['holdings']:
        print(" [!] 보유 종목이 없습니다.")
    else:
        print(f" {'종목명':<12} | {'수량':>4} | {'평단가':>8} | {'현재가':>8} | {'수익률':>7}")
        print("-" * 60)
        for h in result['holdings']:
            color = "\033[91m" if h['return_rate'] > 0 else "\033[94m"
            print(f" {h['name']:<12} | {h['qty']:>4,} | {int(h['buy_price']):>8,} | {h['curr_price']:>8,} | {color}{h['return_rate']:>6.2f}%{reset}")
    print("=" * 60)

if __name__ == "__main__":
    print_account_info()
