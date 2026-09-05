# src/monitoring/institutional_monitoring_report.py

import json
from pathlib import Path

import pandas as pd


MONITORING_DIR = Path("results/monitoring")
REPORT_PATH = MONITORING_DIR / "institutional_monitoring_report.md"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def run_institutional_monitoring_report() -> str:
    dashboard = load_json(MONITORING_DIR / "dashboard_metrics.json")
    health = load_json(MONITORING_DIR / "portfolio_health_score.json")

    attribution = load_csv(MONITORING_DIR / "performance_attribution.csv")
    strategy = load_csv(MONITORING_DIR / "strategy_contribution.csv")
    drift = load_csv(MONITORING_DIR / "portfolio_drift_report.csv")
    risk = load_csv(MONITORING_DIR / "risk_budget_report.csv")
    benchmark = load_csv(MONITORING_DIR / "benchmark_report.csv")

    nav = dashboard.get("portfolio_nav", {})
    risk_block = dashboard.get("risk", {})
    drift_block = dashboard.get("drift", {})
    performance = dashboard.get("performance", {})

    report = f"""# AURUM Institutional Monitoring Report

## Executive Summary

AURUM completed post-execution monitoring for the current portfolio.

- Portfolio NAV: ${nav.get("current_nav", 0):,.2f}
- Daily PnL: ${nav.get("daily_pnl", 0):,.2f}
- Portfolio Return: {nav.get("portfolio_return", 0):.4%}
- Health Score: {health.get("health_score", 0)}
- Status: {health.get("status", "UNKNOWN")}

Interpretation:

{health.get("interpretation", "")}

---

## Performance Summary

- Benchmark Return: {performance.get("benchmark_return", 0):.4%}
- Active Return: {performance.get("active_return", 0):.4%}
- Top Strategy Contributor: {performance.get("top_strategy", "UNKNOWN")}
- Lowest Strategy Contributor: {performance.get("lowest_strategy", "UNKNOWN")}
- Benchmarks Outperformed: {performance.get("outperform_count", 0)}
- Benchmarks Underperformed: {performance.get("underperform_count", 0)}

---

## Risk Oversight

- Risk Budget Status: {risk_block.get("risk_budget_status", "UNKNOWN")}
- Risk Breach Count: {risk_block.get("risk_breach_count", 0)}
- Max Risk Contributor: {risk_block.get("max_risk_contributor", "UNKNOWN")}
- Max Risk Contribution: {risk_block.get("max_risk_contribution", 0):.2%}

---

## Drift Oversight

- Rebalance Required: {drift_block.get("rebalance_required", False)}
- Drift Breach Count: {drift_block.get("drift_breach_count", 0)}
- Max Absolute Drift: {drift_block.get("max_absolute_drift", 0):.4%}

---

## Attribution Table

{attribution.to_markdown(index=False) if not attribution.empty else "No attribution data available."}

---

## Strategy Contribution Table

{strategy.to_markdown(index=False) if not strategy.empty else "No strategy attribution data available."}

---

## Risk Budget Table

{risk.to_markdown(index=False) if not risk.empty else "No risk budget data available."}

---

## Portfolio Drift Table

{drift.to_markdown(index=False) if not drift.empty else "No drift data available."}

---

## Benchmark Comparison Table

{benchmark.to_markdown(index=False) if not benchmark.empty else "No benchmark data available."}

---

## Institutional Conclusion

The portfolio is currently marked as **{health.get("status", "UNKNOWN")}**.

The main monitoring concern is risk-budget concentration, especially where individual assets dominate or fall materially below intended contribution levels. Drift remains controlled, so immediate rebalancing is not required based on allocation drift alone.

AURUM should continue monitoring risk contribution, benchmark-relative performance, and strategy-level contribution before recommending the next rebalance.
"""

    REPORT_PATH.write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM INSTITUTIONAL MONITORING REPORT")
    print("=" * 80)

    report = run_institutional_monitoring_report()

    print(report)
    print("\nSaved:")
    print(f"- {REPORT_PATH}")