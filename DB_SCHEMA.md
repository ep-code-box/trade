# TrendHunter Database Schema

## Overview
- **Database File:** `TrendHunter/db/stock_info.db`
- **Engine:** SQLite3
- **Purpose:** Stores market data, fundamental info, and analysis metrics for KIS-based quantitative trading.

---

## Tables

### 1. `master_info`
*   **Description:** Static stock information and fundamental financial ratios.
*   **Source:** KIS API Master Data (`mst` files).
*   **Update Frequency:** Monthly or On-Demand.

| Column | Type | Description |
| :--- | :--- | :--- |
| `code` | TEXT | Stock Symbol (PK) |
| `name` | TEXT | Stock Name |
| `market_type` | TEXT | KOSPI / KOSDAQ |
| `thtr_ntin` | INTEGER | Net Income (당기순이익) |
| `roe` | REAL | Return on Equity |
| `per_stock_dvdn_amt` | INTEGER | Dividend Per Share (DPS) |
| `dividend_cycle` | TEXT | Dividend Frequency (e.g., 분기배당) |
| *(...and other KIS standard fields)* | | |

### 2. `daily_analysis`
*   **Description:** Daily price history, technical indicators, and supply/demand data.
*   **Source:** KIS API Daily Charts (`FHKST03010100`, `FHKST01010900`).
*   **Update Frequency:** Daily (After Market Close).

| Column | Type | Description |
| :--- | :--- | :--- |
| `date` | TEXT | Trading Date (YYYYMMDD) (PK) |
| `code` | TEXT | Stock Symbol (PK) |
| `open` | INTEGER | Open Price |
| `high` | INTEGER | High Price |
| `low` | INTEGER | Low Price |
| `close` | INTEGER | Close Price |
| `volume` | INTEGER | Trading Volume |
| `amount` | INTEGER | Trading Value (Won) |
| `sma_20` | REAL | 20-Day Simple Moving Average |
| `sma_50` | REAL | 50-Day SMA |
| `sma_150` | REAL | 150-Day SMA |
| `sma_200` | REAL | 200-Day SMA |
| `volume_sma_50` | REAL | 50-Day Volume SMA |
| `high_52w` | INTEGER | 52-Week High (Intraday) |
| `low_52w` | INTEGER | 52-Week Low (Intraday) |
| `rs_score` | REAL | Relative Strength Score (0-99) |
| `vol_std_10d` | REAL | 10-Day Volatility (Std Dev) |
| `vol_std_50d` | REAL | 50-Day Volatility (Std Dev) |
| `dividend_yield` | REAL | Dividend Yield (%) |
| `frgn_net_buy` | INTEGER | Foreigner Net Buy (Volume) |
| `orgn_net_buy` | INTEGER | Institution Net Buy (Volume) |
| `prsn_net_buy` | INTEGER | Personal Net Buy (Volume) |
| `fin_net_buy` | INTEGER | Financial Inv. Net Buy |
| `inv_net_buy` | INTEGER | Investment Trust Net Buy |
| `pension_net_buy` | INTEGER | Pension Fund Net Buy |
| `etc_net_buy` | INTEGER | Other Corp. Net Buy |

### 3. `sectors_themes`
*   **Description:** Mapping between stocks and their sectors/themes.
*   **Source:** KIS API Theme Master.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Auto Increment ID (PK) |
| `code` | TEXT | Stock Symbol (FK) |
| `category_type` | TEXT | 'SECTOR' or 'THEME' |
| `category_name` | TEXT | Name (e.g., 'Semiconductor') |

---

## Views (For Convenience)

### `view_trend_candidates`
*   Joins `daily_analysis` and `master_info` to provide a consolidated view for trend following strategy scanning.

### `view_dividend_candidates`
*   Filters high-yield stocks (>5%) for dividend strategy scanning.
