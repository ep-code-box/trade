# Database Design & Technical Specification (Final)

## 1. Core Databases

### A. `stock_info.db` (Market Intelligence)
The primary data store for technical and fundamental analysis across 3,800+ stocks.

#### 1. `master_info` (Extended Stock Master)
*   **Purpose:** Comprehensive metadata for every stock, parsed from KIS `.mst` files.
*   **Key Columns (Total 77):**
    *   `code` (PK), `name`, `market_type`: Core identifiers.
    *   `bstp_larg_div_code`: Industry classification for sector analysis.
    *   `per_stock_dvdn_amt`: Annualized Dividend Per Share (Reverse-engineered from yield/close).
    *   `dividend_cycle`: Identified as 'Quarterly/Monthly', 'Semi-annual', or 'Annual'.
    *   `dividend_count`: Number of dividend events in the past year.
    *   `roe`, `sale_account`, `thtr_ntin`: Core fundamental metrics.
    *   `updated_at`: Timestamp of the last metadata sync.

#### 2. `daily_analysis` (Rich Time-Series Data)
*   **Purpose:** Stores daily OHLCV and calculated quantitative indicators.
*   **Columns:**
    *   `date`, `code` (Composite PK).
    *   `open`, `high`, `low`, `close`, `volume`, `amount`: Raw market data.
    *   `sma_20`, `sma_50`, `sma_150`, `sma_200`: Moving averages for Trend Template.
    *   `volume_sma_50`: Volume moving average for Dry-up detection.
    *   `rs_score`: Relative Strength percentile rank (1-99).
    *   `vol_std_10d`, `vol_std_50d`: Volatility metrics for VCP detection (`vcp_ratio`).
    *   `high_52w`, `low_52w`: Used for breakout signals.
    *   `dividend_yield`: Dynamic yield based on daily closing price.

#### 3. `sectors_themes` (Relationship Mapping)
*   **Purpose:** Maps stocks to WICS sectors and dynamic themes.
*   **Source:** KIS `idxcode.mst` and `theme_code.mst`.

---

### B. `user_info.db` (Portfolio & Audit)
Manages user-specific data and enforces trading discipline.

*   **`account_config`:** 2-Track account segregation.
*   **`trade_history`:** Execution records with strategy tags (e.g., 'VCP_BREAKOUT').
*   **`audit_log`:** Logs violations of the 1% risk rule or mentor critiques.

---

## 2. Quantitative Algorithms

### 1. Flexible RS Score
Calculated across all 3,800+ stocks using a weighted formula:
*   `Score = (3m_Return * 2) + 6m_Return + 9m_Return + 12m_Return`
*   Requires a minimum of 60 days of history to include new leaders.

### 2. VCP & Volume Dry-up
*   `vcp_ratio = vol_std_10d / vol_std_50d` (Values < 0.5 indicate contraction).
*   `dry_up = current_volume < (previous_volume * 0.6)`.

### 3. Dividend Annualization
*   DPS is aggregated from all dividend events within a 1-year window to handle quarterly/monthly payouts correctly.

---

## 3. Data Integrity Principles
*   **Load then Filter:** All indicators are calculated and stored for all stocks. Filtering is done at the query level (Views/Direct SQL) to allow flexible strategy adjustments.
*   **Full History Recalculation:** The `recalc` job ensures that moving averages and slopes are consistent across the entire 2-year history, eliminating "cold start" issues for slope analysis.
