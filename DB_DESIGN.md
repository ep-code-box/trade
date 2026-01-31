# Database Design & Critical Review

## 1. Proposed Schema Design

### A. `stock_info.db` (Market Data)
Designed to store market-wide data, enabling quantitative technical analysis, screening, and backtesting.

#### 1. `master_info` (Stock Master)
*   **Purpose:** The single source of truth for stock metadata.
*   **Columns:**
    *   `code` (TEXT, PK): Standard ticker code (e.g., '005930').
    *   `name` (TEXT): Stock name.
    *   `market_type` (TEXT): Market classification (KOSPI, KOSDAQ).
    *   `listing_date` (TEXT): IPO date (useful for "IPO base" patterns).
    *   `is_active` (INTEGER): 1 if active, 0 if delisted.
    *   `sector_code` (TEXT): Standard industry classification code (WICS).
    *   `updated_at` (TEXT): Last sync timestamp.

#### 2. `sectors_themes` (Sector & Theme Mapping)
*   **Purpose:** To group stocks for "Leading Sector" analysis based on quantitative strength.
*   **Columns:**
    *   `id` (INTEGER, PK, Auto-inc).
    *   `code` (TEXT, FK): Link to `master_info`.
    *   `category_type` (TEXT): 'SECTOR' (WICS) or 'THEME'.
    *   `category_name` (TEXT): Name of the sector/theme.
    *   `source` (TEXT): Origin of this classification.

#### 3. `daily_analysis` (Daily Technical & Fundamental Metrics)
*   **Purpose:** Time-series data for quantitative screening and trend analysis.
*   **Columns:**
    *   `date` (TEXT, PK).
    *   `code` (TEXT, PK).
    *   `close` (REAL): Adjusted closing price.
    *   `volume` (INTEGER).
    *   `sma_50` (REAL), `sma_150` (REAL), `sma_200` (REAL).
    *   `rs_score` (REAL): Relative Strength score (0-100) vs Market Index.
    *   `volatility_20d` (REAL): For VCP detection.
    *   `dividend_yield_daily` (REAL).

---

### B. `user_info.db` (User & Portfolio)
Designed to isolate sensitive user data and operational logs for principle auditing.

#### 1. `account_config`
*   **Purpose:** Manage 2-Track strategies separately.
*   **Columns:**
    *   `account_no` (TEXT, PK): KIS account number.
    *   `track_type` (TEXT): 'TREND' (Track 1) or 'DIVIDEND' (Track 2).
    *   `target_ratio` (REAL): Asset allocation target.

#### 2. `trade_history`
*   **Purpose:** Record of execution.
*   **Columns:**
    *   `id` (INTEGER, PK).
    *   `date` (TEXT).
    *   `account_no` (TEXT).
    *   `code` (TEXT).
    *   `side` (TEXT): 'BUY' or 'SELL'.
    *   `price` (REAL).
    *   `qty` (INTEGER).
    *   `strategy_tag` (TEXT): Logic triggered.

#### 3. `audit_log` (Rule Enforcement Log)
*   **Purpose:** To track adherence to quantitative rules.
*   **Columns:**
    *   `id` (INTEGER, PK).
    *   `date` (TEXT).
    *   `violation_type` (TEXT): 'STOP_LOSS_DELAY', 'IMPULSE_BUY'.
    *   `severity` (TEXT).
    *   `message` (TEXT): Detailed critique of the violation.

---

## 2. Critical Review

### Strengths
1.  **Rule-Based Objectivity:** By using quantitative metrics like RS Score and VCP Volatility, the system avoids subjective bias.
2.  **Auditability:** Every trade is tagged with a strategy, and violations are logged for review.

### Refined Action Plan
1.  **Direct API Integration:** Focus on KIS API for raw data.
2.  **Pure Quantitative Logic:** All screening logic will use mathematical definitions (e.g., Standard Deviation for VCP).