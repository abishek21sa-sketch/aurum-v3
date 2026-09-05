# src/monitoring/portfolio_health_engine.py

import json
from pathlib import Path


MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

RISK_BUDGET_SUMMARY_PATH = MONITORING_DIR / "risk_budget_summary.json"
DRIFT_SUMMARY_PATH = MONITORING_DIR / "portfolio_drift_summary.json"
BENCHMARK_SUMMARY_PATH = MONITORING_DIR / "benchmark_summary.json"
STRATEGY_SUMMARY_PATH = MONITORING_DIR / "strategy_contribution_summary.json"

OUTPUT_PATH = MONITORING_DIR / "portfolio_health_score.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_risk(risk_summary: dict) -> float:
    breach_count = risk_summary.get("breach_count", 0)
    max_risk_contribution = risk_summary.get("max_risk_contribution", 0)

    score = 100
    score -= breach_count * 20
    score -= max(0, max_risk_contribution - 0.35) * 100

    return clamp(score)


def score_drift(drift_summary: dict) -> float:
    breach_count = drift_summary.get("breach_count", 0)
    max_drift = drift_summary.get("max_absolute_drift", 0)

    score = 100
    score -= breach_count * 25
    score -= max_drift * 500

    return clamp(score)


def score_performance(benchmark_summary: dict) -> float:
    outperform_count = benchmark_summary.get("outperform_count", 0)
    benchmark_count = benchmark_summary.get("benchmark_count", 1)

    outperform_ratio = outperform_count / benchmark_count

    return clamp(50 + outperform_ratio * 50)


def score_strategy(strategy_summary: dict) -> float:
    total_return = strategy_summary.get("total_strategy_return", 0)

    if total_return > 0.002:
        return 95
    if total_return > 0.001:
        return 85
    if total_return > 0:
        return 70

    return 40


def run_portfolio_health_engine() -> dict:
    risk_summary = load_json(RISK_BUDGET_SUMMARY_PATH)
    drift_summary = load_json(DRIFT_SUMMARY_PATH)
    benchmark_summary = load_json(BENCHMARK_SUMMARY_PATH)
    strategy_summary = load_json(STRATEGY_SUMMARY_PATH)

    component_scores = {
        "risk_score": score_risk(risk_summary),
        "drift_score": score_drift(drift_summary),
        "performance_score": score_performance(benchmark_summary),
        "strategy_score": score_strategy(strategy_summary),
        "execution_quality_score": 90,
        "regime_alignment_score": 85,
    }

    health_score = (
        component_scores["risk_score"] * 0.25
        + component_scores["performance_score"] * 0.25
        + component_scores["drift_score"] * 0.20
        + component_scores["execution_quality_score"] * 0.15
        + component_scores["regime_alignment_score"] * 0.15
    )

    if health_score >= 85:
        status = "HEALTHY"
    elif health_score >= 70:
        status = "WATCH"
    else:
        status = "INTERVENTION_REQUIRED"

    output = {
        "health_score": round(health_score, 2),
        "status": status,
        "component_scores": component_scores,
        "interpretation": (
            "Portfolio is operating within acceptable institutional monitoring bounds."
            if status == "HEALTHY"
            else "Portfolio requires closer oversight due to monitoring warnings."
        ),
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=4), encoding="utf-8")

    return output


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM PORTFOLIO HEALTH ENGINE")
    print("=" * 80)

    result = run_portfolio_health_engine()

    print(json.dumps(result, indent=4))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")