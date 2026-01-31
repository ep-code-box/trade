"""한국투자증권 API 인증: 토큰 발급·저장, BASE_URL."""
import os
import json
import requests
from dotenv import load_dotenv

from src.config import ROOT

load_dotenv(os.path.join(ROOT, ".env"))

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
MODE = os.getenv("MODE", "vts")

if MODE == "real":
    BASE_URL = "https://openapi.koreainvestment.com:9443"
else:
    BASE_URL = "https://openapivts.koreainvestment.com:29443"

# 배당 등 일부 API는 실전 도메인에서만 지원
REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"

TOKEN_FILE = os.path.join(ROOT, "kis_token.json")


def get_access_token():
    """Access Token 발급 및 로컬 저장."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token_data = json.load(f)
            return token_data.get("access_token")

    url = f"{BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        token_data = response.json()
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(token_data, f)
        return token_data.get("access_token")
    print(f"Error issuing token: {response.text}")
    return None


if __name__ == "__main__":
    token = get_access_token()
    if token:
        print("Successfully obtained access token.")
