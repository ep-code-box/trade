import requests
import json

try:
    res = requests.get("http://localhost:8000/api/basket")
    print(f"Status: {res.status_code}")
    print("Content:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=True))
except Exception as e:
    print(f"Error: {e}")
