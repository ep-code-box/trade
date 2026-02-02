"""KIS API 호출 속도 테스트 스크립트"""
import time
import requests
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, REAL_BASE_URL

def test_speed(limit=50):
    token = get_access_token()
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100", # 주식 현재가 시세
        "custtype": "P",
    }
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    url = f"{BASE_URL}{path}"
    
    print(f"🚀 API 속도 테스트 시작 (최대 {limit}건 연속 호출)...")
    start_time = time.time()
    success_count = 0
    error_msg = None
    
    for i in range(limit):
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"} # 삼성전자
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("rt_cd") == "0":
                success_count += 1
            else:
                # KIS에서 보내는 에러 메시지 (초당 제한 등)
                error_msg = data.get("msg1")
                break
        else:
            error_msg = f"HTTP {res.status_code}: {res.text}"
            break
            
        print(f"[{i+1}] 호출 성공...", end="\r")
        
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n\n[결과 리포트]")
    print(f"- 총 호출 시도: {i+1}건")
    print(f"- 성공 횟수: {success_count}건")
    print(f"- 소요 시간: {elapsed:.2f}초")
    print(f"- 초당 성공률: {success_count / elapsed:.2f} TPS")
    if error_msg:
        print(f"- 중단 사유: {error_msg}")

if __name__ == "__main__":
    test_speed(50)
