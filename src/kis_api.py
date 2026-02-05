"""한국투자증권 REST API 공통 래퍼: 초고속 비동기 엔진 (Custom Executor)."""
import time
import requests
import asyncio
import os
import json
from datetime import datetime
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

async def kis_post_async(path: str, body: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False):
    """비동기 POST 호출 (주문/설정 변경용 - Hashkey 자동 발급)"""
    await ASYNC_LIMITER.wait()
    
    from src.auth import issue_hashkey
    
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id, custtype=custtype)
    
    def _post():
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kis_api_debug.log")
        
        # [정석] POST 요청 시 본문 해싱 후 헤더에 주입 (스레드 내부에서 실행)
        if body:
            try:
                hash_val = issue_hashkey(body)
                if hash_val:
                    headers["hashkey"] = hash_val
            except Exception as e:
                print(f"Hashkey Issue Error: {e}")

        try:
            res = session.post(url, headers=headers, json=body or {}, timeout=10)
            data = res.json()
            log_msg = f"[{datetime.now()}] {tr_id} RES: {json.dumps(data, ensure_ascii=False)}\n"
            print(log_msg) # 콘솔 출력
            with open(log_path, "a") as f:
                f.write(log_msg)
            return data
        except Exception as e:
            log_msg = f"[{datetime.now()}] {tr_id} ERROR: {str(e)}\n"
            print(log_msg) # 콘솔 출력
            with open(log_path, "a") as f:
                f.write(log_msg)
            return {"error": str(e)}

    return await asyncio.to_thread(_post)

# --- 서버 자동주문 (Stop-Order) 전용 함수 ---

async def register_auto_order(symbol: str, side: str, price: int, qty: int = 1, cano: str = None, cano_pwd: str = None):
    """
    서버 자동주문 신규 등록 (TR: CTRP6010R)
    """
    cond_dv = "1" if side == "BUY" else "2"
    
    body = {
        "CANO": cano or os.getenv("CANO"),
        "ACNT_PRDT_CD": "01",
        "CANO_PWD": cano_pwd or os.getenv("CANO_PWD", "0000"),
        "PDNO": symbol,
        "PRC_COND_DV": cond_dv,
        "PRC_COND_PRC": str(price),
        "ORD_DVSN": "01", 
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0",
        "RE_ORD_YN": "N"
    }
    
    # 실전/모의에 따른 tr_id 분기
    tr_id = "CTRP6010R" # 실전 기준 (모의투자 미지원 시 에러 발생 가능)
    return await kis_post_async("/uapi/domestic-stock/v1/trading/auto-order-register", body=body, tr_id=tr_id)

async def cancel_auto_order(symbol: str, order_num: str):
    """서버 자동주문 취소/삭제 (TR: CTRP6014R)"""
    body = {
        "CANO": os.getenv("CANO"),
        "ACNT_PRDT_CD": "01",
        "PDNO": symbol,
        "AUTO_ORD_SNO": order_num # 자동주문 일련번호
    }
    return await kis_post_async("/uapi/domestic-stock/v1/trading/auto-order-cancel", body=body, tr_id="CTRP6014R")

async def place_order_cash(symbol: str, qty: int, price: int = 0, side: str = "BUY", cano: str = None, acnt_prdt_cd: str = "01"):
    """
    [정석] 현금 매수/매도 주문 (시장가 기본)
    TR: TTTC0802U(매수), TTTC0801U(매도)
    """
    from src.auth import MODE
    
    # 1. TR ID 설정
    if side == "BUY":
        tr_id = "TTTC0802U" if MODE == "real" else "VTTC0802U"
    else:
        tr_id = "TTTC0801U" if MODE == "real" else "VTTC0801U"
        
    # 2. 주문 본문 (시장가 '01' 기준)
    body = {
        "CANO": cano or os.getenv("CANO"),
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "PDNO": symbol,
        "ORD_DVSN": "01", # 시장가
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price) if price > 0 else "0"
    }
    
    path = "/uapi/domestic-stock/v1/trading/order-cash"
    return await kis_post_async(path, body=body, tr_id=tr_id, use_real=(MODE == "real"))