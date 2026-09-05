# AURUM — Institutional Portfolio Intelligence Platform

AURUM is an institutional-style portfolio intelligence system combining quantitative optimization, regime detection, live market monitoring, AI research agents, governance controls, and portfolio operating workflows.

## Core Capabilities

- CVaR optimization using Rockafellar-Uryasev linear programming via cvxpy
- HMM regime detection using live-safe filtered probabilities
- Anomaly detection using rolling z-score and Isolation Forest
- Market provider abstraction for YFinance, Polygon, and Alpaca
- Scheduled live refresh pipeline from market data to portfolio action
- Digital twin stress scoring
- AI research firm, investment committee, and CIO briefing layers
- Portfolio Operating System
- Official dashboard: `src/dashboard/institutional_command_center.py`

## Validation

Run:

```bash
python -m scripts.validate_platform_complete
```
