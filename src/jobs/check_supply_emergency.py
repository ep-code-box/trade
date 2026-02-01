"""주요 종목의 최근 수급(외인/기관)을 긴급 조회하여 '수급 이탈' 여부를 검증합니다."""
import time
from src.kis_api import kis_get_raw
from datetime import datetime

target_stocks = [
    ("140670", "알에스오토메이션"),
    ("008830", "대동기어"),
    ("094820", "일진파워"),
    ("126340", "비나텍"),
    ("389030", "지니너스"),
    ("298830", "슈어소프트테크")
]

def check_supply(code, name):
    path = "/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": "20260126", # 최근 5일
        "FID_INPUT_DATE_2": "20260201",
        "FID_PERIOD_DIV_CODE": "D"
    }
    
    # TR ID: FHKST01010900 (종목별 투자자)
    res = kis_get_raw(path, params=params, tr_id="FHKST01010900")
    
    if not res or "output" not in res:
        # [디버깅] 실패 시 응답 내용 출력
        print(f"[{name}] 데이터 수신 실패: {res}")
        return

    print(f"\n===== [{name} ({code})] 수급 긴급 점검 ====")
    print(f"날짜       | 개인      | 외국인    | 기관      | 종가")
    print("-" * 60)
    
    total_frgn = 0
    total_orgn = 0
    
    for row in res['output'][:5]: # 최근 5일치만
        date = row['stck_bsop_date']
        # 매수: 빨강, 매도: 파랑 표시를 위해 부호 확인
        prsn = int(row['prsn_ntby_qty']) # 개인
        frgn = int(row['frgn_ntby_qty']) # 외국인
        orgn = int(row['orgn_ntby_qty']) # 기관
        close = int(row['stck_clpr'])
        
        total_frgn += frgn
        total_orgn += orgn
        
        print(f"{date} | {prsn:>9,} | {frgn:>9,} | {orgn:>9,} | {close:,}")

    print("-" * 60)
    print(f"★ 5일 누적 | 외인: {total_frgn:>9,} | 기관: {total_orgn:>9,}")
    
    if total_frgn < 0 and total_orgn < 0:
        print("🚨 [위험] 외인/기관 양매도 (수급 이탈)")
    elif total_frgn < 0:
        print("⚠️ [주의] 외인 이탈 중")
    elif total_orgn < 0:
        print("⚠️ [주의] 기관 이탈 중")
    else:
        print("✅ [양호] 메이저 수급 유입 중")
    
    time.sleep(0.3)

if __name__ == "__main__":
    print("스승님의 명령대로 수급 정밀 타격을 시작합니다...\n")
    for code, name in target_stocks:
        check_supply(code, name)
