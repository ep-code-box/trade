"""한국투자증권 REST API 공통 래퍼: 헤더, GET/POST, rate limit."""
import time
import requests

from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, REAL_BASE_URL

# 호출 간 기본 대기(초)
DEFAULT_DELAY = 0.05


def get_headers(tr_id: str, custtype: str = "P", use_real: bool = False):
    """KIS API 공통 헤더 생성. use_real=True면 배당 등 실전 전용 API용."""
    token = get_access_token()
    if not token:
        return None
    base = REAL_BASE_URL if use_real else BASE_URL
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": custtype,
    }


def kis_get(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False, delay: float = DEFAULT_DELAY):
    """
    KIS GET 요청. 성공 시 body 반환, 실패 시 None.
    배당/실전 전용 API는 use_real=True.
    """
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype, use_real=use_real)
    if not headers:
        return None
    if delay > 0:
        time.sleep(delay)
    try:
        res = requests.get(url, headers=headers, params=params or {}, timeout=30)
        if res.status_code != 200:
            return None
        data = res.json()
        if data.get("rt_cd") != "0":
            return None
        return data
    except Exception:
        return None


def kis_get_raw(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False, delay: float = DEFAULT_DELAY):
    """GET 후 파싱 없이 전체 응답 dict 반환 (output 등 직접 사용 시)."""
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype, use_real=use_real)
    if not headers:
        return None
    if delay > 0:
        time.sleep(delay)
    try:
        res = requests.get(url, headers=headers, params=params or {}, timeout=30)
        if res.status_code != 200:
            print(f"HTTP Error {res.status_code}: {res.text}")
            return None
        return res.json()
    except Exception as e:
        print(f"Exception: {e}")
        return None


def kis_post(path: str, body: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False, delay: float = DEFAULT_DELAY):
    """KIS POST 요청. 성공 시 body 반환, 실패 시 None."""
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype, use_real=use_real)
    if not headers:
        return None
    if delay > 0:
        time.sleep(delay)
    try:
        res = requests.post(url, headers=headers, json=body or {}, timeout=30)
        if res.status_code != 200:
            return None
        data = res.json()
        if data.get("rt_cd") != "0":
            return None
        return data
    except Exception:
        return None
