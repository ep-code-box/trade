# Project Context: TrendHunter

## 1. Project Overview
**TrendHunter** is a sophisticated quantitative trading system engineered for the **Korea Investment & Securities (KIS)** API. It automates the investment process by rigorously applying the strategies of market legends—**Jesse Livermore**, **William O'Neil**, and **Mark Minervini**.

The system consists of a robust **Python Backend Analysis Engine** and a modern **React-based Web Dashboard**.

## 2. 핵심 운영 원칙 (The Master's Absolute Rules)

### A. 데이터 무결성 및 효율성 (Data Integrity & Efficiency)
- **수정주가 원칙**: 모든 차트 분석과 지표 계산은 **수정주가(`adj_prc: 0`)**를 사용한다. "배당락과 권리락에 속지 마라."
- **API EPS 우선**: EPS를 직접 계산하지 않고 KIS API가 제공하는 정밀 **`eps`** 필드를 직접 사용한다. 자사주가 반영된 가장 정확한 수치이기 때문이다.
- **재무 데이터의 유통기한 (v14.2)**: EPS, ROE, DPS 등 정적 재무 데이터는 **7일 주기 증분 업데이트(Incremental Update)**를 수행한다. 불필요한 API 호출을 줄이고 배치의 효율성을 극대화한다.
- **실시간 수익률 연산 (Live Yield)**: 재무 데이터는 일주일 단위로 갱신하지만, **배당수익률은 매일 변하는 오늘의 종가를 기준으로 스크리너가 실시간 계산**한다. 효율성과 정확성을 동시에 잡는 핵심 로직이다.

### B. 퀀트 필터 및 생존 원칙 (Quant & Survival)
- **생존자 필터 (Survival First)**: 현재가가 시스템이 계산한 **손절선(Shield) 아래에 있는 종목은 리포트에서 즉시 제명**한다. "죽은 자는 말이 없다."
- **강자 존중 (RS Sorting)**: 모든 필터를 통과한 종목은 **RS Score 내림차순**으로 정렬하여 시장 대장주를 최상단에 배치한다. "가장 강한 놈에게 먼저 베팅하라."

---

## 3. Investment Strategy: The 3-Track System

### TRACK 1: Trend Following (Aggressive Growth) - [v5.5 Final]
1.  **Market Slope**: Index > SMA(200) AND SMA(200) Slope > 0 (1개월 전 대비 상승).
2.  **Survival Filter**: Price >= Calculated Stop-Loss (Shield). 이탈 시 즉시 Drop.
3.  **P-VCP (Price Tightness)**: 
    -   **Strict**: 5일 평균 가격 등락폭 <= 4%.
    -   **Relaxed**: 5일 평균 가격 등락폭 <= 6% (RS 상위 3선 한정).
    -   **Trend**: 최근 변동성이 이전 5일보다 수축 상태여야 함 (Tightening).
4.  **VDU (Volume Dry-up)**: 현재 거래량 < 50일 평균 거래량 * 0.8.

### TRACK 2: Dividend Magic Formula (Value & Yield) - [v6.4 Final]
1.  **Live Yield Audit**: (기록된 DPS / 오늘의 종가) * 100 기준 **3.0% ~ 12.0%** 선별.
2.  **Payout Ratio (건전성)**: (DPS / API EPS) * 100 기준 **10% ~ 100%** 필수. 100% 초과 종목(배당 함정)은 원천 배제.
3.  **Profitability**: ROE >= 8.0% 또는 흑자(EPS > 0) 필수.
4.  **Magic Score**: `Live Yield * 0.7 + ROE * 0.3` 기준 상위 **Top 5**만 정예 출력.

---

## 4. 데이터 수집 파이프라인 (Operational Workflow)
1.  **Identity Sync**: 종목 마스터 동기화.
2.  **Context Mapping**: 섹터 및 주도 테마 분석.
3.  **Daily Thermometer**: 지수 및 시세 수집 (수정주가).
4.  **Financial Audit (7-Day Skip)**: `updated_at` 기준 증분 수집. EPS/ROE 확보.
5.  **Supply Intel**: 외인/기관 **쌍끌이 매집(💎)** 감사.
6.  **Screener Execution**: 실시간 수익률 연산 및 생존자 필터링 기반 리포트 생성.

---
**최종 지침**: "이 문서는 TrendHunter의 헌법이다. 코드는 이 원칙을 구현하는 도구일 뿐이며, 원칙을 벗어난 코드는 즉시 폐기한다."