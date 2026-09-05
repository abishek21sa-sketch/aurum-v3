# src/monitoring/risk_budget_monitor.py

import json
from pathlib import Path

import pandas as pd


EXECUTION_DIR = Path("results/execution")
MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_PORTFOLIO_PATH = EXECUTION_DIR / "current_portfolio_state.json"

OUTPUT_PATH = MONITORING_DIR / "risk_budget_report.csv"
SUMMARY_PATH = MONITORING_DIR / "risk_budget_summary.json"

RISK_BUDGET_THRESHOLD = 0.10


ASSET_RISK_MULTIPLIER = {
    "CASH": 0.05,
    "TLT": 0.60,
    "GLD": 0.75,
    "SPY": 1.00,
    "DIA": 0.95,
    "QQQ": 1.20,
    "BTC-USD": 2.50,
    "ETH-USD": 3.00,
    "VIX": 2.00,
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_weights(weights: dict) -> dict:
    total = sum(float(v) for v in weights.values())
    if total == 0:
        return {k: 0.0 for k in weights}
    return {k: float(v) / total for k, v in weights.items()}


def extract_weights(payload: dict) -> dict:
    extracted = {}

    for key, value in payload.items():
        if isinstance(value, dict):
            asset = value.get("asset") or value.get("ticker") or key

            if "weight" in value:
                extracted[asset] = value["weight"]
            elif "target_weight" in value:
                extracted[asset] = value["target_weight"]
            elif "current_weight" in value:
                extracted[asset] = value["current_weight"]

    if extracted:
        return extracted

    for key in [
        "weights",
        "target_weights",
        "portfolio",
        "current_weights",
        "current_portfolio",
        "holdings",
        "positions",
    ]:
        if key in payload and isinstance(payload[key], dict):
            nested = payload[key]

            if all(isinstance(v, (int, float)) for v in nested.values()):
                return nested

    raise KeyError(
        f"Could not find weights. Available top-level keys: {list(payload.keys())}"
    )


def run_risk_budget_monitor() -> pd.DataFrame:
    payload = load_json(CURRENT_PORTFOLIO_PATH)
    weights = normalize_weights(extract_weights(payload))

    raw_risk = {}

    for asset, weight in weights.items():
        multiplier = ASSET_RISK_MULTIPLIER.get(asset, 1.0)
        raw_risk[asset] = abs(weight) * multiplier

    total_risk = sum(raw_risk.values())

    if total_risk == 0:
        risk_contrib = {asset: 0.0 for asset in raw_risk}
    else:
        risk_contrib = {
            asset: risk_value / total_risk
            for asset, risk_value in raw_risk.items()
        }

    equal_budget = 1 / len(risk_contrib) if risk_contrib else 0

    rows = []

    for asset, contribution in risk_contrib.items():
        excess_risk = contribution - equal_budget

        rows.append(
            {
                "asset": asset,
                "portfolio_weight": weights.get(asset, 0.0),
                "risk_multiplier": ASSET_RISK_MULTIPLIER.get(asset, 1.0),
                "target_risk_budget": equal_budget,
                "actual_risk_contribution": contribution,
                "excess_risk": excess_risk,
                "status": (
                    "BREACH"
                    if abs(excess_risk) > RISK_BUDGET_THRESHOLD
                    else "OK"
                ),
            }
        )

    df = pd.DataFrame(rows).sort_values(
        "actual_risk_contribution", ascending=False
    )

    df.to_csv(OUTPUT_PATH, index=False)

    breaches = df[df["status"] == "BREACH"]

    summary = {
        "asset_count": int(len(df)),
        "breach_count": int(len(breaches)),
        "max_risk_contributor": df.iloc[0]["asset"],
        "max_risk_contribution": float(df.iloc[0]["actual_risk_contribution"]),
        "risk_budget_status": "BREACH" if len(breaches) > 0 else "OK",
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return df


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM RISK BUDGET MONITOR")
    print("=" * 80)

    result = run_risk_budget_monitor()

    print(result.to_string(index=False))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")
    print(f"- {SUMMARY_PATH}")