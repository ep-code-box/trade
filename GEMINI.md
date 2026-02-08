# Project Context: TrendHunter

## 1. Project Overview
**TrendHunter** is a sophisticated quantitative trading system engineered for the **Korea Investment & Securities (KIS)** API. It automates the investment process by rigorously applying the strategies of market legends—**Jesse Livermore**, **William O'Neil**, and **Mark Minervini**.

The system consists of a robust **Python Backend Analysis Engine** and a modern **React-based Web Dashboard**.

## 2. Master's Absolute Rules

### A. Data Integrity & Efficiency
- **Adjusted Price Principle**: All chart analysis and indicator calculations MUST use **Adjusted Price (`adj_prc: 0`)**. "Do not be fooled by dividends and rights issues."
- **Direct API EPS**: Do not calculate EPS manually; use the precise **`eps`** field provided by the KIS API, as it accurately reflects treasury stock.
- **Financial Data Shelf-life (v14.2)**: Static financial data (EPS, ROE, DPS) undergoes an **Incremental Update every 7 days** to minimize unnecessary API calls.
- **Live Yield Audit**: While financial data is updated weekly, the **Dividend Yield is calculated in real-time by the screener based on today's closing price**.

### B. Quant Filters & Survival Rules
- **Survival Filter**: Any stock with a current price below the calculated **Stop-Loss (Shield)** is immediately removed from the report. "The dead tell no tales."
- **Relative Strength (RS) Priority**: All stocks passing the filters are sorted by **RS Score in descending order**, placing market leaders at the top. "Bet on the strongest first."
- **Mechanical Execution**: 
    - **Buy**: Enter immediately without emotion when the calculated Pivot price is breached.
    - **Preserve**: Once in profit, raise the Shield to the 5% Trailing Stop level from the peak to protect 'earned money'.

### C. AI Strategy & Local Resident Model (Mansour Engine)
- **Local-First Principle**: All AI analysis bypasses cloud APIs, utilizing the **local MLX model (Phi-3.5-mini)** optimized for Apple Silicon.
- **Resident Architecture**: The model resides in a dedicated process (`Port 11434`) separate from the backend server to eliminate loading delays.
- **Persona-Based Analysis**: Analysis MUST apply defined personas (Jesse Livermore, William O'Neil) to combine numerical logic with investment psychology.

---

## 3. Investment Strategy: The 3-Track System

### TRACK 1: Trend Following (Aggressive Growth) - [v5.5 Final]
1.  **Market Slope**: Index > SMA(200) AND SMA(200) Slope > 0 (Upward trend compared to 1 month ago).
2.  **Survival Filter**: Price >= Calculated Stop-Loss (Shield). Immediate drop if breached.
3.  **P-VCP (Price Tightness)**: 
    -   **Strict**: 5-day average price range <= 4%.
    -   **Relaxed**: 5-day average price range <= 6% (Top 3 RS only).
    -   **Trend**: Current volatility must be tighter than the previous 5 days.
4.  **VDU (Volume Dry-up)**: Current Volume < 50-day average Volume * 0.8.

### TRACK 2: Dividend Magic Formula (Value & Yield) - [v6.4 Final]
1.  **Live Yield Audit**: (Recorded DPS / Today's Price) * 100 within **3.0% ~ 12.0%**.
2.  **Payout Ratio (Health)**: (DPS / API EPS) * 100 within **10% ~ 100%**. Stocks exceeding 100% (Dividend Trap) are excluded.
3.  **Profitability**: ROE >= 8.0% or positive EPS (EPS > 0) is mandatory.
4.  **Magic Score**: Top **Top 5** based on `Live Yield * 0.7 + ROE * 0.3`.

---

## 4. Operational Workflow
1.  **Identity Sync**: Synchronize stock master data.
2.  **Context Mapping**: Analyze sectors and leading themes.
3.  **Daily Thermometer**: Collect indices and prices (Adjusted Price).
4.  **Financial Audit (7-Day Skip)**: Perform incremental collection based on `updated_at`. Secure EPS/ROE.
5.  **Supply Intel**: Audit institutional/foreign **Dual Buying (💎)**.
6.  **Screener Execution**: Generate reports based on real-time yield calculation and survival filtering.

---

## 5. Design Constitution (Premium Studio Minimalism)

### A. Visual Standardization & Accents
- **Uniform Typography**: Labels MUST use `text-[10px]`, **Black/Bold**, and **Uppercase** with tracking (`tracking-widest`). Primary values are standardized to `text-xl`. All numerical data MUST use a **Monospace font** (`font-mono`) for precision alignment.
- **Premium Material**: Use `bg-slate-900/40` with `backdrop-blur-md` for panels. Elements should be separated by thin `divide-x` or `gap-px` lines using `slate-800/50`.
- **Minimalist Indicators**: Instead of heavy icons, use **1px vertical accent bars** on the left of status cards to color-code metrics (Blue for Seed, Emerald for Profit, Orange for Risk).

### B. Survival-First Hierarchy (The Cockpit)
- **Essential Metrics**: The top dashboard MUST present the following five metrics in equal weight:
    1. **Current Seed**: Total equity (the absolute baseline).
    2. **Available**: Real-time buying power (Cash).
    3. **Round P/L**: Live performance from entry (Floating profit).
    4. **Shield P/L**: Guaranteed profit if stop-loss is triggered (Survival).
    5. **Round Risk**: Potential profit giveaway (Current Price - Shield).
- **Transparency**: Never hide the "ugly" numbers. If the round is in deficit, it must be displayed in `red` with a clear negative sign.

### C. Tables & Interaction
- **Information Density**: Tables MUST include `Shield (Stop-loss)`, `Round Loss`, and `Unrealized P/L` columns to mirror the CLI Survival Report.
- **Interactive Audit**: Selecting a position triggers a detailed **Audit Panel** that evaluates rule compliance (Break-even, Chandelier Exit, etc.) and provides clear execution buttons (Pyramiding, Trim, Exit).
- **Viewport Resilience [v9.5]**: Complex UI components (like charts) MUST adapt to the available viewport height. Use `max-height` with `calc()` and enable internal `overflow-y-auto` to prevent global layout breakage while ensuring all data remains accessible.

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

### D. Preservation & Atomic Changes
- **Strict Scope Control**: Do NOT delete or modify existing fields, logic, or UI elements unless specifically instructed to do so. 
- **Preservation Principle**: The agent must ensure that all previously implemented features and data columns are preserved when adding new functionality. 
- **Atomic Modification**: Changes should be focused only on the requested area, maintaining the integrity of the surrounding code.

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

### D. Tailscale & Local Serving (Operational)
- **Port Strategy**: **7777** port is used for unified UI and API serving.
- **External Access**: Accessible via Tailscale IP (`100.97.140.71:7777`).
- **Unified Restart**: Use the `./restart.sh` script in the parent directory for system control.
    - `./restart.sh trade`: Restart TrendHunter only.
    - `./restart.sh trade build`: Restart TrendHunter after building frontend.
    - `./restart.sh all`: Restart all services (including Mansoorrr).

---
**최종 지침 (Final Directive)**: "This document is the Constitution of TrendHunter. Code is merely a tool to implement these principles. Any code that deviates from these rules shall be discarded immediately."