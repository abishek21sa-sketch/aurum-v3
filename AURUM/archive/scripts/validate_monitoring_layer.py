# scripts/validate_monitoring_layer.py

from pathlib import Path
import json

import pandas as pd


REQUIRED_FILES = {
    "performance attribution": Path("results/monitoring/performance_attribution.csv"),
    "performance attribution summary": Path("results/monitoring/performance_attribution_summary.json"),
    "strategy attribution": Path("results/monitoring/strategy_contribution.csv"),
    "strategy attribution summary": Path("results/monitoring/strategy_contribution_summary.json"),
    "portfolio drift monitor": Path("results/monitoring/portfolio_drift_report.csv"),
    "portfolio drift summary": Path("results/monitoring/portfolio_drift_summary.json"),
    "risk budget monitor": Path("results/monitoring/risk_budget_report.csv"),
    "risk budget summary": Path("results/monitoring/risk_budget_summary.json"),
    "benchmark comparison": Path("results/monitoring/benchmark_report.csv"),
    "benchmark summary": Path("results/monitoring/benchmark_summary.json"),
    "portfolio health engine": Path("results/monitoring/portfolio_health_score.json"),
    "dashboard metrics": Path("results/monitoring/dashboard_metrics.json"),
    "institutional monitoring report": Path("results/monitoring/institutional_monitoring_report.md"),
    "dashboard page": Path("dashboard/portfolio_monitoring_dashboard.py"),
}


def check_file_exists(name: str, path: Path) -> bool:
    if path.exists():
        print(f"[PASS] {name}")
        print(f"       path: {path}")
        return True

    print(f"[FAIL] {name}")
    print(f"       missing: {path}")
    return False


def check_csv_not_empty(name: str, path: Path) -> bool:
    try:
        df = pd.read_csv(path)
        if len(df) > 0:
            print(f"[PASS] {name} data validation")
            print(f"       rows: {len(df)}")
            return True

        print(f"[FAIL] {name} data validation")
        print("       CSV is empty")
        return False

    except Exception as exc:
        print(f"[FAIL] {name} data validation")
        print(f"       error: {exc}")
        return False


def check_json_valid(name: str, path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data:
            print(f"[PASS] {name} JSON validation")
            return True

        print(f"[FAIL] {name} JSON validation")
        print("       JSON is empty or invalid")
        return False

    except Exception as exc:
        print(f"[FAIL] {name} JSON validation")
        print(f"       error: {exc}")
        return False


def validate_monitoring_layer() -> bool:
    print("=" * 80)
    print("AURUM MONITORING LAYER VALIDATION")
    print("=" * 80)

    checks = []

    print("\nOUTPUT EXISTENCE CHECKS")
    print("-" * 80)

    for name, path in REQUIRED_FILES.items():
        checks.append(check_file_exists(name, path))

    print("\nDATA QUALITY CHECKS")
    print("-" * 80)

    csv_files = {
        "performance attribution": REQUIRED_FILES["performance attribution"],
        "strategy attribution": REQUIRED_FILES["strategy attribution"],
        "portfolio drift": REQUIRED_FILES["portfolio drift monitor"],
        "risk budget": REQUIRED_FILES["risk budget monitor"],
        "benchmark comparison": REQUIRED_FILES["benchmark comparison"],
    }

    for name, path in csv_files.items():
        if path.exists():
            checks.append(check_csv_not_empty(name, path))

    json_files = {
        "portfolio health": REQUIRED_FILES["portfolio health engine"],
        "dashboard metrics": REQUIRED_FILES["dashboard metrics"],
        "risk budget summary": REQUIRED_FILES["risk budget summary"],
        "drift summary": REQUIRED_FILES["portfolio drift summary"],
    }

    for name, path in json_files.items():
        if path.exists():
            checks.append(check_json_valid(name, path))

    print("\nFINAL RESULT")
    print("-" * 80)

    passed = all(checks)

    if passed:
        print("[PASS] MONITORING LAYER VALIDATION PASSED")
    else:
        print("[FAIL] MONITORING LAYER VALIDATION FAILED")

    return passed


if __name__ == "__main__":
    validate_monitoring_layer()