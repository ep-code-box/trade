# 🧠 KIS API Intelligence (TrendHunter Knowledge Base)

이 문서는 한국투자증권(KIS) API를 운용하며 발견한 공식 문서 이상의 '실전 지식'과 '히든 트릭'을 기록합니다. "인내는 가장 비싼 수업료다." - 제시 리버모어

---

## 🚀 실전 요약 팁 (Quick Tips)
- **종목코드의 함정**: 이름이 같아도 코드가 다를 수 있음 (예: 액트로는 `290740`). 반드시 API 응답의 `pdno`를 우선 신뢰할 것.
- **감시가의 이원화**: 앱(서버) 설정은 API로 읽기 매우 까다로움. 시스템 DB(`trade_plan`)에 `stop_price`를 별도로 기록하여 **이중 백업(Shield)** 체계를 갖출 것.
- **실전 수익의 정의**: 현재가 수익은 '환상'이고, **감시가 수익(Shield Profit)**이 '확정된 내 돈'임. 계좌 리포트에서 이 둘을 분리해 보는 것이 심리 관리에 필수.
- **경로 삽질 금지**: API 호출 시 404가 나면 무조건 `v1` ↔ `v2` 경로를 바꿔볼 것.
- **데이터 무결성**: DB에 코드를 넣을 땐 반드시 문자열 처리(`TEXT`)를 하여 앞자리 `0`이 사라지는 것을 막을 것.

---

## 1. 🎯 자동주문 및 스탑로스 (Stop-Loss)

### 실시간 감시 주문 (서버 저장형)
한투 앱의 '국내 자동주문' 메뉴와 연동되는 API들입니다.

- **조회 TR ID**: `TTTC8902R` (실전) / `VTTC8902R` (모의)
- **조회 Path**: `/uapi/domestic-stock/v1/trading/inquire-auto-check-order`
- **핵심 필드**:
    - `pdno`: 종목코드 (주의: '액트로'는 `290740`임. `039290`은 다른 종목!)
    - `stpm_cndt_pric`: 스탑지정가 조건 가격 (감시가)
    - `stpm_occr_prc`: 실제 발생 가격

### 주문 실행 시 특이사항
일반 주문 API(`TTTC0011U`)에서도 스탑로스 성격의 주문이 가능합니다.
- **ORD_DVSN (주문구분)**: `22` (스탑지정가호가)
- **CNDT_PRIC (조건가격)**: `ORD_DVSN`이 `22`일 때 필수 입력. 이 가격에 도달하면 주문이 나감.

---

## 2. 🚦 API 경로 및 에러 대응 (Troubleshooting)

### 404 Not Found 피하기
- KIS API는 `v1`과 `v2`가 혼용됩니다. 특정 API가 404가 나면 경로의 버전을 의심해야 합니다.
- **계좌 잔고 조회**: `/uapi/domestic-stock/v1/trading/inquire-balance` (V1이 기본)

### 데이터 타입 주의사항 (Data Integrity)
- **종목코드**: 반드시 6자리 문자열로 취급해야 합니다. (`zfill(6)`)
- SQLite 저장 시 `TEXT` 타입이 아닐 경우 앞의 `0`이 잘릴 수 있으므로 주의 (`039290` -> `39290`).

---

## 3. 🌐 유용한 리소스 및 커뮤니티
- **공식 GitHub**: [koreainvestment/open-trading-api](https://github.com/koreainvestment/open-trading-api)
- **개발자 포털**: [KIS Developers](https://apiportal.koreainvestment.com/)
- **실시간 데이터**: WebSocket 사용 시 `FHKST01010100` (실시간 체결가)

---

## 5. 📺 YouTube & Expert Insights (실전 고수들의 팁)

### 추천 채널
1.  **주식코딩 (Stock Coding)**: 실전 자동매매의 '끝판왕'. V1/V2 혼용 문제와 트레일링 스탑의 로컬 구현 로직이 매우 정교함.
2.  **조코딩 (JoCoding)**: 20분 만에 자동매매 뼈대 잡기. 초보자가 깃허브 오픈소스를 활용해 빠르게 구축하는 법 추천.
3.  **퀀티랩 (QuantiLab)**: 퀀트 분석 전문. 재무 제표와 시세를 결합한 전략 및 `asyncio` 기반의 비동기 엔진 설계 팁 제공.

### 실전 꿀팁 정리
- **로컬 스탑로스 관리**: 앱의 '서버 자동주문'은 API 연동이 불안정하므로, 시스템 내부 DB(`trade_plan`)에서 감시가를 관리하고 시스템이 직접 주문을 던지는 것이 가장 확실함.
- **TPS(초당 호출 제한) 대응**: 한투는 초당 호출 제한이 엄격하므로, 반드시 `RateLimiter`나 비동기 큐를 사용하여 '429 Too Many Requests' 에러를 방지해야 함.
- **WebSocket의 힘**: 실시간 체결가(`FHKST01010100`)를 구독하면 REST API 폴링보다 약 0.5~1초 빠르게 대응 가능. 단타나 칼같은 손절 시 필수.
- **트레일링 스탑(Trailing Stop)**: 고점 대비 특정 % 하락 시 매도하는 로직은 API가 제공하는 기능을 쓰기보다, 로컬에서 고점을 갱신하며 감시하다가 시장가 주문(`ORD_DVSN: 01`)을 던지는 것이 유연함.
- **테스트는 모의투자 계좌로**: 실전 TR ID(`TTTC...`)와 모의 TR ID(`VTTC...`)를 명확히 분리하여 `MODE`에 따라 자동 전환되게 설계할 것.
