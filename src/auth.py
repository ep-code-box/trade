"""한국투자증권 API 인증: 토큰 발급·저장 (DB 기반)."""
import os
import json
import requests
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

from src.config import ROOT

load_dotenv(os.path.join(ROOT, ".env"))

DB_PATH = "TrendHunter/db/stock_info.db"
_cached_token = None

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def load_config_from_db():
    """DB에서 API 설정 로드."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM system_config WHERE key LIKE 'KIS_%'")
    rows = cur.fetchall()
    conn.close()
    
    config = {}
    for key, val in rows:
        config[key] = val
    return config

# 초기 설정 로드 (DB 우선, 없으면 env)
db_conf = {}
try:
    db_conf = load_config_from_db()
except:
    pass

APP_KEY = db_conf.get("KIS_APP_KEY") or os.getenv("APP_KEY")
APP_SECRET = db_conf.get("KIS_APP_SECRET") or os.getenv("APP_SECRET")
MODE = db_conf.get("KIS_MODE") or os.getenv("MODE", "vts")

REAL_BASE_URL = db_conf.get("KIS_REAL_BASE_URL") or "https://openapi.koreainvestment.com:9443"
VTS_BASE_URL = db_conf.get("KIS_VTS_BASE_URL") or "https://openapivts.koreainvestment.com:29443"

if MODE == "real":
    BASE_URL = REAL_BASE_URL
else:
    BASE_URL = VTS_BASE_URL

def get_access_token():
    """Access Token 발급 및 DB 저장/조회 (만료 자동 갱신)."""
    global _cached_token
    
    # 1. 메모리 캐시 확인 (간단한 체크)
    if _cached_token:
        return _cached_token

    # 2. DB에서 토큰 조회
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_config WHERE key = 'KIS_ACCESS_TOKEN'")
        row = cur.fetchone()
        
        if row:
            token_data = json.loads(row[0])
            expired_at_str = token_data.get("access_token_token_expired") # 형식: "2025-02-03 14:00:00"
            
            if expired_at_str:
                exp_dt = datetime.strptime(expired_at_str, "%Y-%m-%d %H:%M:%S")
                # 만료 1분 전까지 여유
                if exp_dt > datetime.now():
                    _cached_token = token_data.get("access_token")
                    return _cached_token
    except Exception as e:
        print(f"Token DB read error: {e}")
    finally:
        conn.close()

    # 3. 토큰 만료 또는 없음 -> 신규 발급
    print("🔑 KIS Access Token 신규 발급 요청...")
    url = f"{BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            # DB 저장
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES ('KIS_ACCESS_TOKEN', ?, datetime('now', 'localtime'))
            """, (json.dumps(token_data),))
            conn.commit()
            conn.close()
            
            _cached_token = access_token
            return access_token
        else:
            print(f"🚨 Token Issue Failed: {response.text}")
            return None
    except Exception as e:
        print(f"🚨 Token Request Error: {e}")
        return None

if __name__ == "__main__":
    token = get_access_token()
    if token:
        print(f"✅ Access Token 확보 완료 (Length: {len(token)})")