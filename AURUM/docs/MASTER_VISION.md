# AURUM Master Vision

AURUM is an institutional-style quantitative research and portfolio intelligence platform.

The system combines market data ingestion, feature engineering, regime detection, signal generation, portfolio optimization, risk analytics, backtesting, reporting, and AI-assisted interpretation into one coherent research pipeline.

## Core Objective

Build a reproducible quant platform that can:

1. ingest multi-asset market data
2. detect market regimes
3. generate allocation signals
4. optimize portfolio weights
5. evaluate portfolio risk
6. run backtests
7. generate executive reports
8. support AI-based portfolio explanation and research assistance

## Asset Universe

Initial universe:

- SPY
- QQQ
- DIA
- TLT
- GLD
- VIX
- BTC-USD
- ETH-USD

## Phase 1 Goal

Phase 1 proves that the system can run as an integrated research engine.

Target command:

python -m src.pipelines.run_phase1_market_pulse

If this command runs cleanly and produces market data, regimes, signals, optimization outputs, risk outputs, reports, and AI summaries, then Phase 1 is complete.

## Long-Term Vision

AURUM should evolve into a full-stack quantitative intelligence platform with:

- live data ingestion
- database-backed storage
- robust alpha research
- regime-aware optimization
- institutional risk monitoring
- paper trading
- AI research copilots
- dashboards
- experiment tracking
- reproducible deployment

## Architecture Principle

Official codebase:

src/

Legacy prototype codebase:

app/

All future development should happen inside src/.

## Infrastructure Rule

All regime-related outputs must use:

data/regimes/

Do not use data/regime/.
