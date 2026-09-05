# src/monitoring/portfolio_drift_monitor.py

import json
from pathlib import Path

import pandas as pd


EXECUTION_DIR = Path("results/execution")
MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_PORTFOLIO_PATH = EXECUTION_DIR / "current_portfolio_state.json"
TARGET_PORTFOLIO_PATH = EXECUTION_DIR / "target_portfolio.json"

OUTPUT_PATH = MONITORING_DIR / "portfolio_drift_report.csv"
SUMMARY_PATH = MONITORING_DIR / "portfolio_drift_summary.json"

DRIFT_THRESHOLD = 0.02


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


def run_portfolio_drift_monitor() -> pd.DataFrame:
    current_payload = load_json(CURRENT_PORTFOLIO_PATH)
    target_payload = load_json(TARGET_PORTFOLIO_PATH)

    current_weights = normalize_weights(extract_weights(current_payload))
    target_weights = normalize_weights(extract_weights(target_payload))

    assets = sorted(set(current_weights) | set(target_weights))

    rows = []

    for asset in assets:
        target_w = target_weights.get(asset, 0.0)
        current_w = current_weights.get(asset, 0.0)
        drift = current_w - target_w
        abs_drift = abs(drift)

        rows.append(
            {
                "asset": asset,
                "target_weight": target_w,
                "current_weight": current_w,
                "drift": drift,
                "absolute_drift": abs_drift,
                "threshold": DRIFT_THRESHOLD,
                "status": "BREACH" if abs_drift > DRIFT_THRESHOLD else "OK",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)

    breaches = df[df["status"] == "BREACH"]

    summary = {
        "asset_count": int(len(df)),
        "breach_count": int(len(breaches)),
        "max_absolute_drift": float(df["absolute_drift"].max()),
        "rebalance_required": bool(len(breaches) > 0),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return df


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM PORTFOLIO DRIFT MONITOR")
    print("=" * 80)

    result = run_portfolio_drift_monitor()

    print(result.to_string(index=False))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")
    print(f"- {SUMMARY_PATH}")