# Project Context: TrendHunter

## Project Overview
TrendHunter is a Python-based quantitative trading system optimized for the **Korea Investment & Securities (KIS)** API. It implements a strict rule-based investment strategy inherited from market legends like Jesse Livermore, William O'Neil, and Mark Minervini.

## Core Architecture (Refactored)
The project follows a modular structure for maintainability and scalability:
- `run.py`: Central CLI entry point for all operations.
- `src/`: Core application logic.
    - `auth.py`: KIS token management & production/sandbox URL handling.
    - `kis_api.py`: Standardized API wrapper with rate limiting and error handling.
    - `db/manager.py`: SQLite schema management (`stock_info.db`, `user_info.db`).
    - `jobs/`: Data collection (Master parsing, Daily OHLCV, Dividend mining).
    - `analysis/`: Quantitative logic (RS Score, VCP, Screening).
- `TrendHunter/db/`: Persistent storage for market and user data.

## Investment Strategy: The 3-Track System

### 1. TRACK 1: Trend Following (Aggressive)
*   **Target:** Market leaders within strong sectors (e.g., Robots, Semi-conductors).
*   **Rules:** Mark Minervini's Trend Template (Stage 2 uptrend), VCP (Volatility Contraction Pattern), and Volume Dry-up.
*   **Indicators:** RS Score (Flexible percentile rank), SMA(50/150/200), VCP Ratio (< 0.5).

### 2. TRACK EX: Independent Momentum (Extra)
*   **Target:** High-momentum stocks not belonging to any major theme.
*   **Purpose:** Captures individual growth stories based purely on price/volume strength.

### 3. TRACK 2: Toobuk Investment (Passive/Stability)
*   **Target:** High-dividend blue-chip stocks.
*   **Yield Goal:** Annualized yield > 5%.
*   **Mining Logic:** 100% KIS-based mining of DPS, Dividend Cycles (Monthly/Quarterly/Annual), and Payout ratios.

## Technical Implementation Details
- **Master Data:** Parsed from KIS `.mst` files (77 fields) for deep fundamental context.
- **Flexible RS:** Weighted calculation (recent 3 months weighted 40%) with percentile ranking across 3,800+ stocks.
- **Smart Update:** Incremental daily OHLCV fetching with indicator recalculation using past 200 days of buffer data.
- **Production API:** All critical data (Dividends, Fundamentals) is fetched via the Production Domain to ensure accuracy.

## Operational Workflow
1. `python3 run.py daily`: Sync latest market prices.
2. `python3 run.py rs`: Recalculate relative strength rankings.
3. `python3 run.py screen`: Generate the integrated investment report.

## Future Roadmap
- **GCP Deployment:** Migration to GCP e2-micro (Free Tier) for 24/7 operation.
- **Telegram Integration:** Automated report delivery and remote account control.
- **Automated Execution:** Rule-based buy/sell execution with server-side stop-losses.

---
**AI Mentor's Directive:** "Trust the data, enforce the rules, and ignore the noise. The system is the master."