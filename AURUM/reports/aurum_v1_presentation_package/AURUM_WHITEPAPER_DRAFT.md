# AURUM Whitepaper Draft

## 1. Executive Summary

AURUM is an institutional-style portfolio intelligence platform built to integrate quantitative finance, live market monitoring, risk management, AI research workflows, and portfolio governance.

## 2. Quantitative Core

AURUM includes a hardened CVaR optimization engine based on the Rockafellar-Uryasev linear programming formulation using cvxpy.

The regime engine uses Hidden Markov Models and clearly separates filtered probabilities from smoothed probabilities. Live decisions use filtered probabilities only.

Anomaly detection combines rolling z-scores with Isolation Forest.

## 3. Live Market Infrastructure

AURUM uses a provider abstraction layer:

- YFinanceProvider
- PolygonProvider
- AlpacaProvider

The live refresh pipeline runs:

```text
Market Data
↓
Features
↓
Regime
↓
Anomaly Detection
↓
Digital Twin Stress
↓
Portfolio OS Action
```

## 4. Dashboard

The official dashboard is:

```text
src/dashboard/institutional_command_center.py
```

## 5. Conclusion

AURUM v1.0 is a defensible institutional-style portfolio intelligence platform focused on quant credibility, live-market credibility, governance, and presentation readiness.
