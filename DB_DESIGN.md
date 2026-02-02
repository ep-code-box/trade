# Database Design & Technical Specification (Final)

## 1. Core Databases

### A. `stock_info.db` (Market Intelligence & Execution)
The primary data store for technical analysis, fundamental data, and trade management across 3,800+ stocks.

#### 1. `master_info` (Extended Stock Master)
*   **Purpose:** Comprehensive metadata for every stock, parsed from KIS `.mst` files.
*   **Key Columns (Total 77):**
    *   `code` (PK), `name`, `market_type`: Core identifiers.
    *   `bstp_larg_div_code`: Industry classification for sector analysis.
    *   `per_stock_dvdn_amt`: Annualized Dividend Per Share (Reverse-engineered from yield/close).
    *   `dividend_cycle`: Identified as 'Quarterly/Monthly', 'Semi-annual', or 'Annual'.
    *   `dividend_count`: Number of dividend events in the past year.
    *   `per`, `pbr`, `roe`, `bsop_prfi`, `thtr_ntin`: Core fundamental metrics.
    *   `updated_at`: Timestamp of the last metadata sync.

#### 2. `daily_analysis` (Rich Time-Series Data)
*   **Purpose:** Stores daily OHLCV, calculated quantitative indicators, and investor supply data.
*   **Columns:**
    *   `date`, `code` (Composite PK).
    *   `open`, `high`, `low`, `close`, `volume`, `amount`: Raw market data.
    *   `frgn_net_buy`, `orgn_net_buy`, `pension_net_buy`: Investor supply breakdown (Added in v2.5).
    *   `sma_20`, `sma_50`, `sma_150`, `sma_200`: Moving averages for Trend Template.
    *   `volume_sma_50`: Volume moving average for Dry-up detection.
    *   `rs_score`: Relative Strength percentile rank (1-99).
    *   `vol_std_10d`, `vol_std_50d`: Volatility metrics for VCP detection (`vcp_ratio`).
    *   `high_52w`, `low_52w`: Used for breakout signals.
    *   `dividend_yield`: Dynamic yield based on daily closing price.

#### 3. `sectors_themes` (Relationship Mapping)
*   **Purpose:** Maps stocks to WICS sectors and dynamic themes.
*   **Source:** KIS `idxcode.mst` and `theme_code.mst`.

#### 4. `trade_plan` (Strategy Execution)
*   **Purpose:** Manages the pipeline of potential trades selected by the screener.
*   **Columns:**
    *   `date`, `code`: Identification.
    *   `entry_price`, `stop_price`: Calculated risk parameters (e.g., Pivot Point, Box Bottom).
    *   `weight`: Portfolio allocation strategy (e.g., "15%").
    *   `status`: State machine (`READY` -> `SUBMITTED` -> `FILLED` / `CANCELLED`).

#### 5. `trade_execution` (Audit Trail)
*   **Purpose:** Immutable record of all executed trades via the API.
*   **Columns:** `timestamp`, `code`, `side` (BUY/SELL), `qty`, `price`, `result_msg`.

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
*   Yield Goal: Annualized yield > 7% (Revised for high-rate environment).

---

## 3. Data Integrity Principles
*   **Load then Filter:** All indicators are calculated and stored for all stocks. Filtering is done at the query level (Views/Direct SQL) to allow flexible strategy adjustments.
*   **Full History Recalculation:** The `recalc` job ensures that moving averages and slopes are consistent across the entire 2-year history, eliminating "cold start" issues for slope analysis.
*   **Single Source of Truth:** `stock_info.db` acts as the unified repository for both market data and user trading records (Merged from `user_info.db`).
