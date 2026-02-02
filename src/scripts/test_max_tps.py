import asyncio
import time
import requests
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL

# 리미터 없이 순수하게 API를 호출하는 함수
def fetch_raw(url, headers, params):
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            return {"rt_cd": "0", "headers": dict(res.headers)}
        return {"rt_cd": str(res.status_code), "msg1": f"HTTP {res.status_code}", "body": res.text[:100]}
    except Exception as e:
        return {"rt_cd": "999", "msg1": str(e)}

async def test_max_speed(total_requests=100, concurrency=30):
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
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"} # 삼성전자
    
    print(f"🔥 KIS API 최대 한계 테스트 시작...")
    print(f"- 목표 요청수: {total_requests}")
    print(f"- 병렬 수준: {concurrency}")
    
    start_time = time.perf_counter()
    
    # 병렬로 요청 실행
    tasks = []
    for _ in range(total_requests):
        tasks.append(asyncio.to_thread(fetch_raw, url, headers, params))
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    success = [r for r in results if r.get("rt_cd") == "0"]
    # EGW00133 및 EGW00201 모두 제한으로 간주
    throttled = [r for r in results if any(code in (r.get("msg1", "") + r.get("body", "")) for code in ["EGW00133", "EGW00201"])]
    others = [r for r in results if r.get("rt_cd") != "0" and not any(code in (r.get("msg1", "") + r.get("body", "")) for code in ["EGW00133", "EGW00201"])]
    
    print(f"\n[테스트 결과 요약]")
    print(f"- 총 소요 시간: {duration:.4f}초")
    print(f"- 전체 요청: {len(results)}건")
    print(f"- 성공: {len(success)}건")
    print(f"- 제한됨(EGW00133): {len(throttled)}건")
    print(f"- 기타 에러: {len(others)}건")
    
    if success:
        print("\n[성공 응답 헤더 샘플]")
        # 첫 번째 성공건의 헤더 중 속도 관련 가능성 있는 것들 출력
        sample = success[0].get("headers", {})
        for k, v in sample.items():
            if any(x in k.lower() for x in ["limit", "rate", "remain", "count"]):
                print(f"- {k}: {v}")
        if not any(any(x in k.lower() for x in ["limit", "rate", "remain", "count"]) for k in sample):
            print("- 특이사항: 속도 제한 관련 명시적 헤더가 없습니다.")

    if others:
        print("\n[기타 에러 상세 (최대 5건)]")
        for error in others[:5]:
            print(f"- rt_cd: {error.get('rt_cd')}, msg: {error.get('msg1')}, body: {error.get('body')}")
    
    actual_tps = len(success) / duration
    print(f"\n📊 실질 TPS (성공건수/시간): {actual_tps:.2f}")
    
    if throttled:
        print(f"💡 분석: {len(success)+1}번째 근처 요청에서 제한이 걸리기 시작했습니다.")
    else:
        print(f"💡 분석: {total_requests}건을 {duration:.2f}초 동안 제한 없이 모두 처리했습니다. 한계치가 더 높을 수 있습니다.")

if __name__ == "__main__":
    asyncio.run(test_max_speed(500, 150))
