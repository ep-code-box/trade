import requests
import json

# 테스트 데이터 (두산에너빌리티 034020)
payload = {
    "symbol": "034020",
    "name": "두산에너빌리티",
    "price": 98100
}

try:
    res = requests.post("http://localhost:8000/api/order/buy", json=payload)
    print(f"Status Code: {res.status_code}")
    print("Response JSON:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
