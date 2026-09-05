# src/monitoring/performance_dashboard_engine.py

import json
from pathlib import Path

import pandas as pd


MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = MONITORING_DIR / "dashboard_metrics.json"


FILES = {
    "attribution_summary": MONITORING_DIR / "performance_attribution_summary.json",
    "strategy_summary": MONITORING_DIR / "strategy_contribution_summary.json",
    "drift_summary": MONITORING_DIR / "portfolio_drift_summary.json",
    "risk_summary": MONITORING_DIR / "risk_budget_summary.json",
    "benchmark_summary": MONITORING_DIR / "benchmark_summary.json",
    "health_score": MONITORING_DIR / "portfolio_health_score.json",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_performance_dashboard_engine() -> dict:
    data = {name: load_json(path) for name, path in FILES.items()}

    attribution = data["attribution_summary"]
    strategy = data["strategy_summary"]
    drift = data["drift_summary"]
    risk = data["risk_summary"]
    benchmark = data["benchmark_summary"]
    health = data["health_score"]

    nav_start = 1_000_000
    portfolio_return = attribution.get("portfolio_return", 0.0)
    nav_current = nav_start * (1 + portfolio_return)

    dashboard_metrics = {
        "portfolio_nav": {
            "starting_nav": nav_start,
            "current_nav": round(nav_current, 2),
            "daily_pnl": round(nav_current - nav_start, 2),
            "portfolio_return": portfolio_return,
        },
        "performance": {
            "benchmark_return": attribution.get("benchmark_return", 0.0),
            "active_return": attribution.get("active_return", 0.0),
            "top_strategy": strategy.get("top_contributor"),
            "lowest_strategy": strategy.get("lowest_contributor"),
            "outperform_count": benchmark.get("outperform_count", 0),
            "underperform_count": benchmark.get("underperform_count", 0),
        },
        "risk": {
            "risk_budget_status": risk.get("risk_budget_status", "UNKNOWN"),
            "risk_breach_count": risk.get("breach_count", 0),
            "max_risk_contributor": risk.get("max_risk_contributor", "UNKNOWN"),
            "max_risk_contribution": risk.get("max_risk_contribution", 0.0),
        },
        "drift": {
            "rebalance_required": drift.get("rebalance_required", False),
            "drift_breach_count": drift.get("breach_count", 0),
            "max_absolute_drift": drift.get("max_absolute_drift", 0.0),
        },
        "health": {
            "health_score": health.get("health_score", 0),
            "status": health.get("status", "UNKNOWN"),
            "interpretation": health.get("interpretation", ""),
        },
    }

    OUTPUT_PATH.write_text(json.dumps(dashboard_metrics, indent=4), encoding="utf-8")

    return dashboard_metrics


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM PERFORMANCE DASHBOARD ENGINE")
    print("=" * 80)

    result = run_performance_dashboard_engine()

    print(json.dumps(result, indent=4))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")