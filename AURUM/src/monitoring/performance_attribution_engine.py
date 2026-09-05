# src/monitoring/performance_attribution_engine.py

import json
from pathlib import Path

import pandas as pd


EXECUTION_DIR = Path("results/execution")
MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)


CURRENT_PORTFOLIO_PATH = EXECUTION_DIR / "current_portfolio_state.json"
TARGET_PORTFOLIO_PATH = EXECUTION_DIR / "target_portfolio.json"

OUTPUT_PATH = MONITORING_DIR / "performance_attribution.csv"
SUMMARY_PATH = MONITORING_DIR / "performance_attribution_summary.json"


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
    possible_keys = [
        "weights",
        "target_weights",
        "portfolio",
        "current_weights",
        "current_portfolio",
        "holdings",
        "positions",
    ]

    for key in possible_keys:
        if key in payload and isinstance(payload[key], dict):
            nested = payload[key]

            if all(isinstance(v, (int, float)) for v in nested.values()):
                return nested

            if all(isinstance(v, dict) for v in nested.values()):
                extracted = {}
                for asset, values in nested.items():
                    if "weight" in values:
                        extracted[asset] = values["weight"]
                    elif "target_weight" in values:
                        extracted[asset] = values["target_weight"]
                    elif "current_weight" in values:
                        extracted[asset] = values["current_weight"]
                if extracted:
                    return extracted

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

    raise KeyError(
        f"Could not find weights in portfolio JSON. Available top-level keys: {list(payload.keys())}"
    )


def build_mock_returns(assets: list[str]) -> dict:
    """
    Temporary deterministic return proxy for monitoring layer validation.

    Later this can be replaced with realized returns from live market data.
    """
    returns = {}

    for i, asset in enumerate(sorted(assets)):
        base = 0.001
        adjustment = (i + 1) * 0.00025
        returns[asset] = base + adjustment

    return returns


def calculate_attribution(
    current_weights: dict,
    target_weights: dict,
    asset_returns: dict,
) -> pd.DataFrame:
    rows = []

    all_assets = sorted(set(current_weights) | set(target_weights) | set(asset_returns))

    benchmark_return = sum(
        target_weights.get(asset, 0.0) * asset_returns.get(asset, 0.0)
        for asset in all_assets
    )

    portfolio_return = sum(
        current_weights.get(asset, 0.0) * asset_returns.get(asset, 0.0)
        for asset in all_assets
    )

    for asset in all_assets:
        target_w = target_weights.get(asset, 0.0)
        current_w = current_weights.get(asset, 0.0)
        asset_ret = asset_returns.get(asset, 0.0)

        allocation_effect = (current_w - target_w) * benchmark_return
        selection_effect = target_w * (asset_ret - benchmark_return)
        interaction_effect = (current_w - target_w) * (asset_ret - benchmark_return)

        total_effect = allocation_effect + selection_effect + interaction_effect

        rows.append(
            {
                "asset": asset,
                "target_weight": target_w,
                "current_weight": current_w,
                "asset_return": asset_ret,
                "benchmark_return": benchmark_return,
                "portfolio_return": portfolio_return,
                "allocation_effect": allocation_effect,
                "selection_effect": selection_effect,
                "interaction_effect": interaction_effect,
                "total_effect": total_effect,
            }
        )

    return pd.DataFrame(rows)


def run_performance_attribution() -> pd.DataFrame:
    current_payload = load_json(CURRENT_PORTFOLIO_PATH)
    target_payload = load_json(TARGET_PORTFOLIO_PATH)

    current_weights = normalize_weights(extract_weights(current_payload))
    target_weights = normalize_weights(extract_weights(target_payload))

    assets = sorted(set(current_weights) | set(target_weights))
    asset_returns = build_mock_returns(assets)

    attribution = calculate_attribution(
        current_weights=current_weights,
        target_weights=target_weights,
        asset_returns=asset_returns,
    )

    attribution.to_csv(OUTPUT_PATH, index=False)

    summary = {
        "portfolio_return": float(attribution["portfolio_return"].iloc[0]),
        "benchmark_return": float(attribution["benchmark_return"].iloc[0]),
        "active_return": float(
            attribution["portfolio_return"].iloc[0]
            - attribution["benchmark_return"].iloc[0]
        ),
        "total_allocation_effect": float(attribution["allocation_effect"].sum()),
        "total_selection_effect": float(attribution["selection_effect"].sum()),
        "total_interaction_effect": float(attribution["interaction_effect"].sum()),
        "total_effect": float(attribution["total_effect"].sum()),
        "asset_count": int(len(attribution)),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return attribution


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM PERFORMANCE ATTRIBUTION ENGINE")
    print("=" * 80)

    result = run_performance_attribution()

    print(result.to_string(index=False))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")
    print(f"- {SUMMARY_PATH}")