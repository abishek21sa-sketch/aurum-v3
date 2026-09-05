from pathlib import Path

readme = """# AURUM — Institutional AI Portfolio Intelligence System

**Live system. Running daily. Paper trading active.**

AURUM is a real-time quantitative finance platform that ingests live market data, detects market regimes, optimizes portfolio allocation using CVaR minimization, stress-tests decisions through a digital twin simulation engine, and explains everything through an AI copilot.

Not a stock predictor. Not a toy dashboard. A running institutional-style decision engine.

---

## What It Does

Every cycle AURUM:
1. Pulls live prices (SPY, QQQ, TLT, GLD, BTC, ETH, VIX) via yfinance / Alpaca
2. Detects the current market regime (bull / bear / high-vol / defensive) using HMM
3. Runs CVaR portfolio optimization with regime-adjusted constraints
4. Checks governance gates — execution blocked until conditions are met
5. Updates a live Alpaca paper trading portfolio with real fills
6. Generates an AI morning briefing via GPT-4o-mini
7. Writes everything to the Mission Control dashboard

---

## Backtest Result

Walk-forward backtest, 2018-2025, no lookahead bias:

| Strategy        | Annual Return | Volatility | Sharpe | Max Drawdown | CVaR 95% |
|----------------|--------------|------------|--------|--------------|----------|
| SPY Buy & Hold | 13.74%       | 19.46%     | 0.71   | -33.72%      | -2.99%   |
| Equal Weight   | 10.95%       | 12.19%     | 0.90   | -25.15%      | -1.78%   |
| Regime CVaR    | 6.55%        | 12.11%     | 0.54   | -28.56%      | -1.78%   |

The regime-filtered CVaR strategy trades return for risk reduction — volatility cut by 38%, tail risk matches the best alternative. Designed to survive, not to chase.

---

## Architecture

    Live Market Data (yfinance / Alpaca / Polygon)
            |
    Feature Engine (returns, volatility, momentum, macro)
            |
    Regime Detection (HMM — filtered probabilities, no lookahead)
            |
    CVaR Optimizer (Rockafellar-Uryasev LP via cvxpy)
            |
    AI Research Committee (multi-agent via GPT-4o-mini)
            |
    Governance Gate (exposure limits, drawdown controls)
            |
    Portfolio Operating System (directive to execution)
            |
    Alpaca Paper Trading (real fills, real P&L)
            |
    Mission Control Dashboard (Streamlit, auto-refresh)

---

## Tech Stack

- Data: yfinance, Alpaca Markets API, Polygon, FRED
- Quant: numpy, pandas, scipy, cvxpy, hmmlearn, scikit-learn
- AI: OpenAI GPT-4o-mini, multi-agent committee architecture
- Backend: Python, FastAPI, Redis Streams
- Database: TimescaleDB, PostgreSQL, Parquet
- Dashboard: Streamlit
- Deployment: Docker, docker-compose

---

## Run Locally

    git clone https://github.com/YOUR_USERNAME/aurum.git
    cd aurum
    pip install -r requirements.txt

    # Add API keys to .env
    # OPENAI_API_KEY, ALPACA_API_KEY, ALPACA_SECRET_KEY

    # Run one cycle
    python -m src.mission_control.run_aurum_mission_control --once

    # Launch dashboard
    streamlit run dashboard/aurum_mission_control.py

    # Run continuously
    python -m src.mission_control.run_aurum_mission_control --loop --interval 300

---

## Run Backtest

    python -m src.backtest.regime_cvar_backtest

Outputs tearsheet to results/backtest/regime_cvar_backtest_tearsheet.txt

---

## Project Structure

    aurum/
    src/
        mission_control/     Live cycle orchestration
        regimes/             HMM regime detection
        optimization/        CVaR, mean-variance, risk parity
        research/            AI agents and investment committee
        risk/                Tail risk, CVaR, stress testing
        digital_twin/        Monte Carlo, historical replay
        execution/           Paper trading, order management
        backtest/            Walk-forward backtesting engine
    dashboard/
        aurum_mission_control.py   Main Streamlit dashboard
    results/                 Live outputs updated every cycle
    data/                    Historical price data
    config/                  Settings and AI config

---

## Current Status

- Live market data: yfinance (active), Alpaca (active)
- Paper portfolio: Running — $100,000 starting value
- Regime detection: DEFENSIVE (as of last cycle)
- Execution: Blocked by governance gate
- Auto-refresh: Every 5 minutes

---

Built by a Masters IE student exploring computational finance and operations research.
"""

Path("README.md").write_text(readme, encoding="utf-8")
print("README written.")
print("Lines:", readme.count("\\n"))
print("Has backtest:", "Regime CVaR" in readme)