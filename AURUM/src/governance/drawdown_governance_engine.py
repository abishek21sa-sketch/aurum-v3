from pathlib import Path
import json
import pandas as pd


GOVERNANCE_DIR = Path("results/governance")
MONITORING_DIR = Path("results/monitoring")
RISK_DIR = Path("results/risk")
EXECUTION_DIR = Path("results/execution")

POLICY_PATH = GOVERNANCE_DIR / "policy_constraints.json"

POSSIBLE_DRAWDOWN_SOURCES = [
    MONITORING_DIR / "benchmark_summary.json",
    MONITORING_DIR / "performance_attribution_summary.json",
    RISK_DIR / "portfolio_risk_summary.json",
    EXECUTION_DIR / "portfolio_state_summary.json",
]

OUTPUT_REPORT_PATH = GOVERNANCE_DIR / "drawdown_governance_report.csv"
OUTPUT_SUMMARY_PATH = GOVERNANCE_DIR / "drawdown_governance_summary.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_value_recursive(data, keywords: list[str]):
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()

            if any(keyword in key_lower for keyword in keywords):
                if isinstance(value, (int, float)):
                    return float(value)

            result = find_value_recursive(value, keywords)
            if result is not None:
                return result

    elif isinstance(data, list):
        for item in data:
            result = find_value_recursive(item, keywords)
            if result is not None:
                return result

    return None


def load_latest_drawdown() -> tuple[float, str]:
    for path in POSSIBLE_DRAWDOWN_SOURCES:
        data = load_json(path)

        if not data:
            continue

        drawdown = find_value_recursive(
            data,
            keywords=[
                "max_drawdown",
                "maximum_drawdown",
                "drawdown",
            ],
        )

        if drawdown is not None:
            return drawdown, str(path)

    print("WARNING: No drawdown source found. Using fallback drawdown = -0.125.")
    return -0.125, "fallback"


def classify_drawdown(drawdown: float, policy: dict) -> tuple[str, str]:
    limits = policy["portfolio_risk_limits"]

    warning = limits["max_drawdown_warning"]
    hedge = limits["max_drawdown_hedge"]
    derisk = limits["max_drawdown_derisk"]
    emergency = limits["max_drawdown_emergency"]

    if drawdown <= emergency:
        return "EMERGENCY_REVIEW", "Maximum drawdown exceeds emergency threshold."

    if drawdown <= derisk:
        return "DERISK_REQUIRED", "Maximum drawdown exceeds de-risk threshold."

    if drawdown <= hedge:
        return "HEDGE_REQUIRED", "Maximum drawdown exceeds hedge threshold."

    if drawdown <= warning:
        return "CAUTION", "Maximum drawdown exceeds warning threshold."

    return "NORMAL", "Drawdown is within normal governance limits."


def run_drawdown_governance_engine() -> tuple[pd.DataFrame, dict]:
    policy = load_json(POLICY_PATH)

    if not policy:
        raise FileNotFoundError("Missing policy_constraints.json.")

    latest_drawdown, source = load_latest_drawdown()
    status, action = classify_drawdown(latest_drawdown, policy)

    limits = policy["portfolio_risk_limits"]

    rows = [
        {
            "metric": "latest_max_drawdown",
            "value": latest_drawdown,
            "source": source,
            "warning_threshold": limits["max_drawdown_warning"],
            "hedge_threshold": limits["max_drawdown_hedge"],
            "derisk_threshold": limits["max_drawdown_derisk"],
            "emergency_threshold": limits["max_drawdown_emergency"],
            "governance_status": status,
            "recommended_action": action,
        }
    ]

    report = pd.DataFrame(rows)

    summary = {
        "latest_max_drawdown": latest_drawdown,
        "drawdown_source": source,
        "governance_status": status,
        "recommended_action": action,
        "requires_action": status != "NORMAL",
    }

    report.to_csv(OUTPUT_REPORT_PATH, index=False)
    OUTPUT_SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return report, summary


def main() -> None:
    print("=" * 80)
    print("AURUM DRAWDOWN GOVERNANCE ENGINE")
    print("=" * 80)

    report, summary = run_drawdown_governance_engine()

    print("\nDRAWDOWN GOVERNANCE SUMMARY")
    print("-" * 80)
    print(f"Latest max drawdown: {summary['latest_max_drawdown']:.2%}")
    print(f"Source: {summary['drawdown_source']}")
    print(f"Governance status: {summary['governance_status']}")
    print(f"Recommended action: {summary['recommended_action']}")
    print(f"Requires action: {summary['requires_action']}")

    print(f"\nOutput report: {OUTPUT_REPORT_PATH}")
    print(f"Output summary: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()