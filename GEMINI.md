# Project Context: TrendHunter

## 1. Project Overview
**TrendHunter** is a sophisticated quantitative trading system engineered for the **Korea Investment & Securities (KIS)** API. It automates the investment process by rigorously applying the strategies of market legends—**Jesse Livermore** (Price Action), **William O'Neil** (CANSLIM), and **Mark Minervini** (Volatility Contraction Pattern).

The system consists of a robust **Python Backend Analysis Engine** and a modern **React-based Web Dashboard** for visualization.

## 2. Core Architecture
-   **`src/`**: Backend Analysis Engine (FastAPI & Quantitative Algorithms).
-   **`dashboard/`**: React-based UI for Screening results and VCP annotations.
-   **`TrendHunter/db/`**: SQLite-based persistence layer (Master Info, Daily Analysis, Trade Plan).

---

## 3. Investment Strategy: The 3-Track System

### TRACK 1: Trend Following (Aggressive Growth) - [v5.5 Survival Master Final]
*   **Philosophy**: "Buy high, sell higher." Focus on Market Leaders with Price Tightness.
*   **Selection Criteria (Strictly Applied)**:
    1.  **Market Slope**: Index must be above SMA(200) AND SMA(200) must be trending up (current > 1-month ago).
    2.  **Survival Filter**: Current Price **MUST** be greater than or equal to the Calculated Stop-Loss (Shield). Dead stocks (broken trends) are immediately dropped.
    3.  **Perfect Alignment**: Price > SMA(20) > SMA(50) > SMA(150) > SMA(200).
    4.  **P-VCP (Price Tightness)**: 
        -   **Strict**: 5-day Average Price Range ((High-Low)/Close) <= 4%.
        -   **Relaxed**: 5-day Average Price Range <= 6% (RS Top 3 only if no Strict candidates found).
        -   **Trend**: Tightness must be contracting (Recent Avg < Previous Avg * 1.1).
    5.  **RS Priority**: Candidates are sorted by **RS Score (Highest first)** to prioritize market dominance.
    6.  **Volume Dry-up (VDU)**: Current Volume < 50-day Volume SMA * 0.8.

### TRACK EX: Independent Momentum (Catalyst Driven)
*   **Criteria**: Meets Track 1 technical criteria but belongs to niche sectors.
*   **Priority**: Enhanced by **Double-Buy (💎 쌍끌이)** status (Foreign + Institutional).

### TRACK 2: Toobuk Investment (Dividend & Stability)
*   **Criteria**: Yield ≥ 7.0%, ROE ≥ 10.0%, Positive Net Income.

---

## 4. Operational Workflow (Daily Routine)
The system operates on a rigorous 8-step pipeline:
1.  **Identity Sync**: Sync stock masters from MST files.
2.  **Context Mapping**: Sector/Theme dominance analysis.
3.  **Market Thermometer**: Fetch Index & Stock trends using **Adjusted Price**.
4.  **Financial Audit**: Real-time ROE & Profit audit.
5.  **Dividend Mining**: v3.6 Real-time yield calculation.
6.  **Supply Intel**: Double-Buy (💎) and Accumulation evidence audit.
7.  **Momentum Ranking**: Multi-period weighted RS percentile ranking.
8.  **Screener Execution**: Survival-based filtering and RS-sorted reporting.

---

## 5. Technical Implementation Details
- **Adjusted Price**: "A chart without adjustment is a lie." All calculations use `adj_prc: 0`.
- **Accumulation Evidence**: `up_supply > down_supply * 1.5` identifies aggressive accumulation.
- **30 TPS Engine**: Maximizes throughput while respecting KIS API rate limits.

---

## 6. 개발 및 운영 절대 원칙 (The Master's Core)
- **Survival First**: "Losses are not to be cut; they are to be avoided entirely."
- **Price Tightness**: P-VCP (4%) is the soul of the entry point.
- **The Strongest First**: Always bet on the highest RS stock in the leading sector.

**최종 지침**: "시장의 맥락(Theme)을 읽고, 거장의 잣대(P-VCP)로 타격하며, 생존(Survival)으로 승리하라."
