from pathlib import Path
import json
import pandas as pd


GOVERNANCE_DIR = Path("results/governance")
EXECUTION_DIR = Path("results/execution")

PORTFOLIO_PATH = EXECUTION_DIR / "current_portfolio_state.json"
POLICY_PATH = GOVERNANCE_DIR / "policy_constraints.json"

OUTPUT_REPORT_PATH = GOVERNANCE_DIR / "liquidity_report.csv"
OUTPUT_SUMMARY_PATH = GOVERNANCE_DIR / "liquidity_summary.json"


LIQUIDITY_SCORE_MAP = {
    "CASH": 1.00,
    "SPY": 0.95,
    "QQQ": 0.95,
    "DIA": 0.90,
    "TLT": 0.90,
    "GLD": 0.85,
    "VIX": 0.70,
    "BTC-USD": 0.60,
    "ETH-USD": 0.55,
}


DAYS_TO_LIQUIDATE_MAP = {
    "CASH": 0,
    "SPY": 1,
    "QQQ": 1,
    "DIA": 1,
    "TLT": 1,
    "GLD": 2,
    "VIX": 3,
    "BTC-USD": 3,
    "ETH-USD": 3,
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_weights(portfolio: dict) -> dict:
    if "positions" in portfolio and isinstance(portfolio["positions"], dict):
        return {
            asset: float(weight)
            for asset, weight in portfolio["positions"].items()
            if isinstance(weight, (int, float))
        }

    for key in ["weights", "portfolio_weights", "target_weights", "current_weights"]:
        if key in portfolio and isinstance(portfolio[key], dict):
            return {
                asset: float(weight)
                for asset, weight in portfolio[key].items()
                if isinstance(weight, (int, float))
            }

    raise ValueError("Could not extract portfolio weights.")


def classify_liquidity_status(
    cash_weight: float,
    weighted_liquidity_score: float,
    weighted_days_to_liquidate: float,
    preferred_cash_buffer: float,
    stress_cash_buffer: float,
) -> str:
    if cash_weight < preferred_cash_buffer or weighted_liquidity_score < 0.75:
        return "STRESSED"

    if cash_weight < stress_cash_buffer or weighted_days_to_liquidate > 2.0:
        return "CAUTION"

    return "NORMAL"


def run_liquidity_governance_engine() -> tuple[pd.DataFrame, dict]:
    portfolio = load_json(PORTFOLIO_PATH)
    policy = load_json(POLICY_PATH)

    if not portfolio:
        raise FileNotFoundError("Missing current_portfolio_state.json.")

    if not policy:
        raise FileNotFoundError("Missing policy_constraints.json.")

    weights = extract_weights(portfolio)

    rows = []

    weighted_liquidity_score = 0.0
    weighted_days_to_liquidate = 0.0

    for asset, weight in weights.items():
        liquidity_score = LIQUIDITY_SCORE_MAP.get(asset, 0.50)
        days_to_liquidate = DAYS_TO_LIQUIDATE_MAP.get(asset, 5)

        weighted_liquidity_score += weight * liquidity_score
        weighted_days_to_liquidate += weight * days_to_liquidate

        rows.append(
            {
                "asset": asset,
                "weight": weight,
                "liquidity_score": liquidity_score,
                "days_to_liquidate": days_to_liquidate,
                "weighted_liquidity_score": weight * liquidity_score,
                "weighted_days_to_liquidate": weight * days_to_liquidate,
            }
        )

    report = pd.DataFrame(rows)

    cash_weight = weights.get("CASH", 0.0)

    preferred_cash_buffer = policy["liquidity_policy"]["preferred_cash_buffer"]
    stress_cash_buffer = policy["liquidity_policy"]["liquidity_stress_cash_buffer"]

    liquidity_status = classify_liquidity_status(
        cash_weight=cash_weight,
        weighted_liquidity_score=weighted_liquidity_score,
        weighted_days_to_liquidate=weighted_days_to_liquidate,
        preferred_cash_buffer=preferred_cash_buffer,
        stress_cash_buffer=stress_cash_buffer,
    )

    summary = {
        "cash_weight": cash_weight,
        "preferred_cash_buffer": preferred_cash_buffer,
        "liquidity_stress_cash_buffer": stress_cash_buffer,
        "weighted_liquidity_score": weighted_liquidity_score,
        "weighted_days_to_liquidate": weighted_days_to_liquidate,
        "liquidity_status": liquidity_status,
    }

    report.to_csv(OUTPUT_REPORT_PATH, index=False)
    OUTPUT_SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return report, summary


def main() -> None:
    print("=" * 80)
    print("AURUM LIQUIDITY GOVERNANCE ENGINE")
    print("=" * 80)

    report, summary = run_liquidity_governance_engine()

    print("\nLIQUIDITY SUMMARY")
    print("-" * 80)
    print(f"Cash weight: {summary['cash_weight']:.2%}")
    print(f"Preferred cash buffer: {summary['preferred_cash_buffer']:.2%}")
    print(f"Stress cash buffer: {summary['liquidity_stress_cash_buffer']:.2%}")
    print(f"Weighted liquidity score: {summary['weighted_liquidity_score']:.4f}")
    print(f"Weighted days to liquidate: {summary['weighted_days_to_liquidate']:.2f}")
    print(f"Liquidity status: {summary['liquidity_status']}")

    print("\nLIQUIDITY DETAIL")
    print("-" * 80)
    print(report.to_string(index=False))

    print(f"\nOutput report: {OUTPUT_REPORT_PATH}")
    print(f"Output summary: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()