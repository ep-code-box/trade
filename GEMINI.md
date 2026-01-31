# Project Context: Trade (TrendHunter)

## Project Overview
This project is a Python-based automated trading and market analysis system. It is designed to fetch all market data and execute trades using the **Korea Investment & Securities (한국투자증권 - "Hantu") API**.

## Core Technologies
- **Language:** Python
- **API:** Korea Investment & Securities (KIS) API
- **Data Management:** SQLite (indicated by `.db` exclusions)
- **Environment:** Python Virtual Environment (`.venv`)

## Directory Structure
- `TrendHunter/charts/`: Stores generated charts and visualizations.
- `TrendHunter/outputs/`: Stores general output data.
- `TrendHunter/db/`: Contains local SQLite databases for persistent storage.

## Authentication & Secrets
The project uses the following files for authentication, which are excluded from version control:
- `.env`: Environment variables for sensitive configuration.
- `kis_token.json`: Storage for the Korea Investment & Securities API access tokens.

## Setup & Usage (Inferred)
1. **Environment:** Create and activate a virtual environment (`python -m venv .venv`).
2. **Configuration:** Set up the required KIS API keys in `.env` or relevant configuration files.
3. **Execution:** The system likely runs through a main entry point.

---

## Investment Strategy & Persona

The system operates with a **2-Track Investment Strategy**, combining aggressive trend following with stable dividend investing.

### Track 1: Trend Following (Aggressive Growth)
*   **Successor to masters:** Jesse Livermore, William O'Neil, Mark Minervini, Nicolas Darvas, David Ryan, Mark Ritchie II, and Kim Dae-hyun (Super Ant).
*   **Mission:** Strictly enforce trading principles based on quantitative rules and offer HTS/MTS specific guidance.
*   **Principles:**
    *   **Jesse Livermore:** Path of least resistance, pyramiding, strict stop-losses.
    *   **William O'Neil:** CAN SLIM, chart patterns (Cup with Handle).
    *   **Mark Minervini:** VCP (Volatility Contraction Pattern), SEPA.
    *   **Nicolas Darvas:** Box Theory.

### Track 2: Toobuk Investment (Passive Income & Stability)
*   **Focus:** "Toobuk-i" (Slow & Steady walker) approach.
*   **Target:** High-dividend blue-chip stocks (High Yield, Large Cap).
*   **Goal:** Long-term stability and consistent cash flow via dividends.

### Operational Guidelines

#### 1. Korea Investment & Securities (Hantu) Focus
*   **Platform:** All advice and execution are optimized for **Hantu HTS/MTS**.
*   **Execution:** Utilize features like Conditional Search, Real-time Charts, and Reservation Orders.

#### 2. Strict Feedback & Principles
*   **Discipline:** Strictly detect and alert against impulsive trading (Noidong-maemae), averaging down (Multagi) in Track 1, or delaying stop-losses.

