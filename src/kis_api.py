"""한국투자증권 REST API 공통 래퍼: v11.7 스나이퍼 엔진 (스탑 지정가 정밀 교정)."""
import time
import requests
import asyncio
import os
import json
from datetime import datetime
from collections import deque
from src.auth import get_access_token, APP_KEY, APP_SECRET, BASE_URL, REAL_BASE_URL

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200)
session.mount('https://', adapter)

class AsyncRateLimiter:
    def __init__(self, max_per_second=30.0):
        self.max_per_second = max_per_second
        self.calls = deque()
        self._lock = None
    async def wait(self):
        if self._lock is None: self._lock = asyncio.Lock()
        while True:
            async with self._lock:
                now = time.time()
                while self.calls and now - self.calls[0] > 1: self.calls.popleft()
                if len(self.calls) < self.max_per_second:
                    self.calls.append(now)
                    return
                sleep_time = 1.001 - (now - self.calls[0])
            if sleep_time > 0: await asyncio.sleep(sleep_time)

ASYNC_LIMITER = AsyncRateLimiter(max_per_second=30.0)

def get_headers(tr_id: str, custtype: str = "P"):
    token = get_access_token()
    if not token: return None
    return {
        "content-type": "application/json; charset=utf-8", 
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET, 
        "tr_id": tr_id, "custtype": custtype,
    }

async def kis_post_async(path: str, body: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False, skip_hash: bool = False):
    """비동기 POST 호출 (Hashkey 정밀 제어)"""
    await ASYNC_LIMITER.wait()
    from src.auth import issue_hashkey
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id, custtype=custtype)
    
    def _post():
        if body and not skip_hash:
            try:
                hash_val = issue_hashkey(body)
                if hash_val: headers["hashkey"] = hash_val
            except: pass
        try:
            res = session.post(url, headers=headers, json=body or {}, timeout=10)
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kis_api_debug.log")
            
            try: data = res.json()
            except: data = {"error": "Invalid JSON", "raw": res.text[:200]}
                
            log_msg = f"[{datetime.now()}] {tr_id} STATUS: {res.status_code} RES: {json.dumps(data, ensure_ascii=False)}\n"
            with open(log_path, "a") as f:
                f.write(log_msg)
                f.write(f"[{datetime.now()}] {tr_id} BODY: {json.dumps(body)} STATUS: {res.status_code} RAW: {res.text[:200]}\n")
            return data
        except Exception as e:
            return {"error": str(e)}
    return await asyncio.to_thread(_post)

async def register_auto_order(symbol: str, side: str, price: int, qty: int = 1, cano: str = None, cano_pwd: str = None):
    # 장중 스탑 주문(22)으로 통합 관리
    return await place_stop_order(symbol, qty, price, side, cano)

async def register_reserved_order(symbol: str, side: str, price: int, qty: int = 1, cano: str = None):
    from src.auth import MODE, load_config_from_db
    config = load_config_from_db()
    raw_cano = cano or config.get("KIS_CANO", "")
    if MODE != "real": return {"rt_cd": "1", "msg1": "예약주문은 실전 전용입니다."}
    clean_cano = raw_cano.replace("-", "")
    cano_8, prdt_cd = clean_cano[:8], clean_cano[8:10] if len(clean_cano) >= 10 else "01"
    body = {
        "CANO": cano_8, "ACNT_PRDT_CD": prdt_cd, "PDNO": symbol,
        "ORD_QTY": str(int(qty)), "ORD_UNPR": str(int(price)) if price > 0 else "0",
        "SLL_BUY_DVSN_CD": "02" if side == "BUY" else "01",
        "ORD_DVSN_CD": "00" if price > 0 else "01",
        "ORD_OBJT_CBLC_DVSN_CD": "10"
    }
    return await kis_post_async("/uapi/domestic-stock/v1/trading/order-resv", body=body, tr_id="CTSC0008U", use_real=True)

async def kis_get_async(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False):
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    headers = get_headers(tr_id or "FHKST03010100", custtype=custtype)
    def _fetch():
        try:
            res = session.get(url, headers=headers, params=params or {}, timeout=10)
            return res.json() if res.status_code == 200 else None
        except: return None
    return await asyncio.to_thread(_fetch)

async def kis_get_raw_async(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False):
    return await kis_get_async(path, params, tr_id, custtype, use_real)

def kis_get_raw(path: str, params: dict = None, tr_id: str = "", custtype: str = "P", use_real: bool = False):
    """동기 GET 호출 (봇 리스너 호환용)"""
    from src.auth import REAL_BASE_URL, BASE_URL, get_access_token, APP_KEY, APP_SECRET
    base = REAL_BASE_URL if use_real else BASE_URL
    url = f"{base}{path}"
    token = get_access_token()
    headers = {
        "content-type": "application/json; charset=utf-8", 
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET, 
        "tr_id": tr_id or "FHKST03010100", "custtype": custtype
    }
    try:
        res = session.get(url, headers=headers, params=params or {}, timeout=10)
        return res.json() if res.status_code == 200 else None
    except: return None

async def place_order_cash(symbol: str, qty: int, price: int = 0, side: str = "BUY", cano: str = None):
    from src.auth import MODE, load_config_from_db
    config = load_config_from_db()
    raw_cano = cano or config.get("KIS_CANO", "")
    clean_cano = raw_cano.replace("-", "")
    cano_8, prdt_cd = clean_cano[:8], clean_cano[8:10] if len(clean_cano) >= 10 else "01"
    tr_id = ("TTTC0012U" if side == "BUY" else "TTTC0011U") if MODE == "real" else ("VTTC0012U" if side == "BUY" else "VTTC0011U")
    body = {
        "CANO": cano_8, "ACNT_PRDT_CD": prdt_cd, "PDNO": symbol,
        "ORD_DVSN": "01", "ORD_QTY": str(qty), "ORD_UNPR": str(price) if price > 0 else "0"
    }
    return await kis_post_async("/uapi/domestic-stock/v1/trading/order-cash", body=body, tr_id=tr_id, use_real=(MODE == "real"))

async def place_stop_order(symbol: str, qty: int, stop_price: int, side: str = "BUY", cano: str = None):
    """
    [v11.7] 국내주식 스탑지정가(Breakout) 주문 등록
    - 스탑지정가(22)를 사용하여 '가격 도달 시' 주문 실행
    """
    from src.auth import MODE, load_config_from_db
    config = load_config_from_db()
    raw_cano = cano or config.get("KIS_CANO", "")
    clean_cano = raw_cano.replace("-", "")
    cano_8, prdt_cd = clean_cano[:8], clean_cano[8:10] if len(clean_cano) >= 10 else "01"
    
    tr_id = "TTTC0012U" if side == "BUY" else "TTTC0011U"
    if MODE != "real": tr_id = "V" + tr_id[1:]

    body = {
        "CANO": cano_8,
        "ACNT_PRDT_CD": prdt_cd,
        "PDNO": symbol,
        "ORD_DVSN": "22",           # 22: 스탑지정가
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": str(int(stop_price)), # 조건 달성 시 이 가격으로 지정가 주문
        "CNDT_PRIC": str(int(stop_price)), # 감시 가격 (스탑가)
        "PRC_COND_DV": "1" if side == "BUY" else "2" # 1:이상(돌파), 2:이하(손절)
    }
    return await kis_post_async("/uapi/domestic-stock/v1/trading/order-cash", body=body, tr_id=tr_id, use_real=(MODE == "real"))

async def cancel_auto_order(symbol: str, order_num: str):
    from src.auth import MODE, load_config_from_db
    config = load_config_from_db()
    raw_cano = config.get("KIS_CANO", "")
    clean_cano = raw_cano.replace("-", "")
    cano_8, prdt_cd = clean_cano[:8], clean_cano[8:10] if len(clean_cano) >= 10 else "01"
    return await kis_post_async("/uapi/domestic-stock/v1/trading/order-rvsecncl", 
                                body={ "CANO": cano_8, "ACNT_PRDT_CD": prdt_cd, "ORGN_ODNO": order_num, "RVSE_CNCL_DVSN_CD": "02", "ORD_QTY": "0", "ORD_UNPR": "0", "QTY_ALL_ORD_YN": "Y" }, 
                                tr_id="TTTC0803U", use_real=(MODE == "real"))