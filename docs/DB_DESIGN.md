# Database Design & Technical Specification (Final)

## 1. Core Databases

### A. `stock_info.db` (Market Intelligence & Execution)
The primary data store for technical analysis, fundamental data, and trade management across 3,800+ stocks.

#### 1. `master_info` (Extended Stock Master)
*   **Purpose:** Comprehensive metadata for every stock, parsed from KIS `.mst` files.
*   **Unit Rules:**
    *   `lstn_stcn`: **Thousands (천 주)** for both KOSPI and KOSDAQ. Always multiply by 1,000 for actual share count calculations.
    *   `thtr_ntin`: **100 Millions (억 원)**.
*   **Key Columns:**
    *   `stck_sdpr`: Base Price (Used for calculating dividend drop adjustment).
    *   `flng_cls_code`: Ex-date flag (01: Rights, 02: Dividend).

---

## 2. Quantitative Algorithms

### 3. Dividend Intelligent Back-Calculation (v6.0)
When direct API values are unreliable, the system reconstructs dividend data from static financial statements:
*   **Source**: Latest 'December' (기말 결산) record from Income Statements and Financial Ratios.
*   **Formula**: `EPS = (Net Income * 100M) / (Listed Shares * 1000)`
*   **DPS**: `EPS * (Payout Ratio / 100)`
*   **Safety Cap**: Calculated yields > 15% are discarded as scale errors.

---

## 3. Data Integrity Principles
*   **Load then Filter:** All indicators are calculated and stored for all stocks. Filtering is done at the query level (Views/Direct SQL) to allow flexible strategy adjustments.
*   **Full History Recalculation:** The `recalc` job ensures that moving averages and slopes are consistent across the entire 2-year history, eliminating "cold start" issues for slope analysis.
*   **Single Source of Truth:** `stock_info.db` acts as the unified repository for both market data and user trading records (Merged from `user_info.db`).
