from pathlib import Path
import json
import pandas as pd


RESULTS_DIR = Path("results/governance")
EXECUTION_DIR = Path("results/execution")

POLICY_PATH = RESULTS_DIR / "policy_constraints.json"
PORTFOLIO_PATH = EXECUTION_DIR / "current_portfolio_state.json"

OUTPUT_REPORT_PATH = RESULTS_DIR / "exposure_limit_report.csv"
OUTPUT_SUMMARY_PATH = RESULTS_DIR / "exposure_limit_summary.json"


ASSET_CLASS_MAP = {
    "SPY": "equity",
    "QQQ": "equity",
    "DIA": "equity",
    "TLT": "bond",
    "GLD": "commodity",
    "BTC-USD": "crypto",
    "ETH-USD": "crypto",
    "VIX": "hedge",
    "CASH": "cash",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_policy() -> dict:
    policy = load_json(POLICY_PATH)

    if not policy:
        raise FileNotFoundError(
            "Missing policy_constraints.json. Run portfolio_policy_engine first."
        )

    return policy


def load_current_portfolio() -> dict:
    portfolio = load_json(PORTFOLIO_PATH)

    if not portfolio:
        print("WARNING: current_portfolio_state.json not found. Using fallback portfolio.")
        return {
            "weights": {
                "SPY": 0.25,
                "QQQ": 0.20,
                "DIA": 0.10,
                "TLT": 0.15,
                "GLD": 0.08,
                "BTC-USD": 0.04,
                "ETH-USD": 0.03,
                "VIX": 0.05,
                "CASH": 0.10,
            }
        }

    return portfolio


def extract_weights(portfolio: dict) -> dict:
    possible_keys = [
        "weights",
        "portfolio_weights",
        "target_weights",
        "current_weights",
        "allocation",
        "holdings",
        "positions",
    ]

    for key in possible_keys:
        if key in portfolio and isinstance(portfolio[key], dict):
            extracted = {}

            for asset, value in portfolio[key].items():
                if isinstance(value, (int, float)):
                    extracted[asset] = float(value)

                elif isinstance(value, dict):
                    for weight_key in ["weight", "portfolio_weight", "current_weight"]:
                        if weight_key in value:
                            extracted[asset] = float(value[weight_key])
                            break

            if extracted:
                return extracted

    raise ValueError("Could not extract portfolio weights from current portfolio state.")

def check_single_asset_limits(weights: dict, policy: dict) -> list[dict]:
    rows = []

    max_single = policy["single_asset_limits"]["max_single_asset_weight"]
    max_crypto = policy["single_asset_limits"]["max_crypto_asset_weight"]
    max_cash = policy["single_asset_limits"]["max_cash_weight"]

    for asset, weight in weights.items():
        asset_class = ASSET_CLASS_MAP.get(asset, "unknown")

        limit = max_single
        rule = "max_single_asset_weight"

        if asset_class == "crypto":
            limit = max_crypto
            rule = "max_crypto_asset_weight"

        if asset_class == "cash":
            limit = max_cash
            rule = "max_cash_weight"

        status = "PASS" if weight <= limit else "FAIL"

        rows.append(
            {
                "check_type": "single_asset_limit",
                "asset": asset,
                "asset_class": asset_class,
                "rule": rule,
                "actual_weight": weight,
                "limit": limit,
                "status": status,
                "violation_amount": max(0.0, weight - limit),
            }
        )

    return rows


def check_asset_class_limits(weights: dict, policy: dict) -> list[dict]:
    rows = []

    class_exposures = {}

    for asset, weight in weights.items():
        asset_class = ASSET_CLASS_MAP.get(asset, "unknown")
        class_exposures[asset_class] = class_exposures.get(asset_class, 0.0) + weight

    for asset_class, exposure in class_exposures.items():
        if asset_class not in policy["asset_class_limits"]:
            continue

        min_limit = policy["asset_class_limits"][asset_class]["min"]
        max_limit = policy["asset_class_limits"][asset_class]["max"]

        if exposure < min_limit:
            status = "FAIL"
            violation_amount = min_limit - exposure
            rule = "minimum_asset_class_exposure"
        elif exposure > max_limit:
            status = "FAIL"
            violation_amount = exposure - max_limit
            rule = "maximum_asset_class_exposure"
        else:
            status = "PASS"
            violation_amount = 0.0
            rule = "asset_class_exposure_range"

        rows.append(
            {
                "check_type": "asset_class_limit",
                "asset": "PORTFOLIO",
                "asset_class": asset_class,
                "rule": rule,
                "actual_weight": exposure,
                "limit": f"{min_limit:.2f}-{max_limit:.2f}",
                "status": status,
                "violation_amount": violation_amount,
            }
        )

    return rows


def run_exposure_limit_monitor() -> tuple[pd.DataFrame, dict]:
    policy = load_policy()
    portfolio = load_current_portfolio()
    weights = extract_weights(portfolio)

    rows = []
    rows.extend(check_single_asset_limits(weights, policy))
    rows.extend(check_asset_class_limits(weights, policy))

    report = pd.DataFrame(rows)

    total_checks = len(report)
    failed_checks = int((report["status"] == "FAIL").sum())
    passed_checks = total_checks - failed_checks

    overall_status = "PASS" if failed_checks == 0 else "FAIL"

    summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "overall_status": overall_status,
        "output_report": str(OUTPUT_REPORT_PATH),
    }

    report.to_csv(OUTPUT_REPORT_PATH, index=False)
    OUTPUT_SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return report, summary


def main() -> None:
    print("=" * 80)
    print("AURUM EXPOSURE LIMIT MONITOR")
    print("=" * 80)

    report, summary = run_exposure_limit_monitor()

    print("\nEXPOSURE LIMIT SUMMARY")
    print("-" * 80)
    print(f"Total checks: {summary['total_checks']}")
    print(f"Passed checks: {summary['passed_checks']}")
    print(f"Failed checks: {summary['failed_checks']}")
    print(f"Overall status: {summary['overall_status']}")

    print("\nFAILED CHECKS")
    print("-" * 80)
    failed = report[report["status"] == "FAIL"]

    if failed.empty:
        print("No exposure limit violations.")
    else:
        print(failed.to_string(index=False))

    print(f"\nOutput report: {OUTPUT_REPORT_PATH}")
    print(f"Output summary: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()