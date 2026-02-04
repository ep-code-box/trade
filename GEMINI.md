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

## 5. Design Constitution (Studio Minimalism)

### A. Visual Standardization
- **Consistent Typography**: All data labels MUST use `text-[11px]`, **Bold**, and **Uppercase**. Primary metrics are standardized to `text-xl` or `text-2xl`. All numerical values MUST use a **Monospace font** to ensure perfect character alignment across columns.
- **Restrained Color Palette**: Use `slate-950/900` for backgrounds and `slate-800` for borders. Color-code using `emerald` for Profit, `red` for Loss, and `orange` for Risk. Maintain ~80% saturation/opacity to prevent visual fatigue. Ban all excessive gradients, glows, or decorative animations.

### B. Information Hierarchy (Risk-First)
- **Primary Directives**: **Available Cash** and **Risk Limit (1% Rule)** must be the most prominent elements in any account-related view. The UI must answer "How much can I lose?" before "How much can I make?".
- **Dynamic Seed Definition**: The system operates on the principle: "The current balance IS the seed." Historical principal is irrelevant; the **Current Total Equity** is the absolute baseline for all real-time risk and position sizing calculations.

### C. Layout & Uniformity
- **Modular Grid**: All summary elements must have identical height, padding, and alignment. Use standardized components (e.g., `SummaryCard`) to enforce strict UI consistency.
- **Responsive Grouping**: Information must be grouped logically (e.g., Cash paired with Risk Guide) and must maintain this relationship across mobile (2-column grid) and desktop (horizontal flex) layouts.

---

## 6. Development Constitution (Efficiency & Cleanliness)

### A. Modular Architecture
- **Strict Line Limit**: No single source file shall exceed **200-300 lines**. If logic expands beyond this threshold, it MUST be refactored into smaller, specialized modules.
- **Single Responsibility**: Each file must serve one clear purpose, adhering to the "Atomic Logic" principle.

### B. Logical Isolation
- **Centralized Validation**: All diagnostic checks, integrity audits, and debugging scripts MUST be concentrated in a dedicated directory (e.g., `src/scripts/`).
- **Separation of Concerns**: Core engine logic and auxiliary check logic must never reside in the same file.

### C. Resource & State Management
- **Mandatory Cleanup**: All temporary artifacts, intermediate data files, or transient logs generated during execution MUST be deleted immediately upon process completion.
- **Stateless Operation**: The system should maintain a zero-footprint policy regarding temporary files.

---

## 7. Operational Protocol (Standard Methodology)

### A. Source of Truth Compliance
- **Reference First**: Every API implementation or troubleshooting session MUST begin with cross-referencing the **official KIS API documentation**, the **KIS GitHub repository**, and the **REST API portal**. No assumptions are allowed regarding header or body structures.

### B. Sample-First Validation (Incremental Execution)
- **Dry Run**: Before executing bulk data acquisition or batch updates, the agent MUST perform a test run with a small subset (1-5 samples).
- **Schema Audit**: Verify the raw API response against the expected schema during the sample phase to ensure compatibility before scale-up.

### C. Post-Integration Database Audit
- **Verification Loop**: Once full data processing is complete, the results MUST be verified by performing direct SQL queries against the local database (`stock_info.db`).
- **Integrity Check**: Confirm that fields are correctly populated, data types are preserved, and no corruption occurred during the batch process.

---
**최종 지침 (Final Directive)**: "This document is the Constitution of TrendHunter. Code is merely a tool to implement these principles. Any code that deviates from these rules shall be discarded immediately."