"""한국투자증권 REST API 공통 래퍼: 초고속 비동기 엔진 (Custom Executor)."""
import time
import requests
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, REAL_BASE_URL

# 전역 세션 및 커넥션 풀 확장
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200)
session.mount('https://', adapter)

# [핵심] 200개의 스레드를 확보하여 I/O 병목 제거
EXECUTOR = ThreadPoolExecutor(max_workers=200)

class AsyncRateLimiter:
    def __init__(self, max_per_second=30.0):
        self.max_per_second = max_per_second
        self.calls = deque()
        self._lock = None

    async def wait(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        while True:
            async with self._lock:
                now = time.time()
                while self.calls and now - self.calls[0] > 1:
                    self.calls.popleft()
                if len(self.calls) < self.max_per_second:
                    self.calls.append(now)
                    return
                sleep_time = 1.001 - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

ASYNC_LIMITER = AsyncRateLimiter(max_per_second=30.0)

def get_headers(tr_id: str, custtype: str = "P"):
    token = get_access_token()
    if not token: return None
    return {
        "content-type": "application/json; charset=utf-8", "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET, "tr_id": tr_id, "custtype": custtype,
    }

def kis_get_raw(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False, delay: float = 0):
    """원시 응답을 반환하는 동기 호출 (레거시 지원)"""
    if delay > 0: time.sleep(delay) # 레거시 대기 지원
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype)
    try:
        res = session.get(url, headers=headers, params=params or {}, timeout=15)
        return res.json()
    except Exception: return None

async def kis_get_async(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False):
    """비동기 호출 (requests + to_thread)"""
    await ASYNC_LIMITER.wait()
    
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype)
    
    def _fetch():
        try:
            res = session.get(url, headers=headers, params=params or {}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data.get("rt_cd") == "0" else None
            return None
        except: return None

    return await asyncio.to_thread(_fetch)

async def kis_get_raw_async(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False):
    """원시 응답을 그대로 반환하는 비동기 호출"""
    await ASYNC_LIMITER.wait()
    
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype)
    
    def _fetch():
        try:
            res = session.get(url, headers=headers, params=params or {}, timeout=10)
            return res.json()
        except: return None

    return await asyncio.to_thread(_fetch)