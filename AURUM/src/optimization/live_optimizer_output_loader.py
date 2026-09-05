# src/optimization/live_optimizer_output_loader.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd


RESULTS_DIR = Path("results/optimization")


OPTIMIZER_FILE_MAP = {
    "mean_variance": [
        "mean_variance_allocation.csv",
        "mean_variance_weights.csv",
    ],
    "minimum_variance": [
        "minimum_variance_allocation.csv",
        "minimum_variance_weights.csv",
        "min_variance_allocation.csv",
    ],
    "risk_parity": [
        "risk_parity_allocation.csv",
        "risk_parity_weights.csv",
    ],
    "cvar": [
        "cvar_allocation.csv",
        "cvar_weights.csv",
    ],
    "bayesian_robust": [
        "bayesian_robust_allocation.csv",
        "bayesian_robust_weights.csv",
    ],
    "black_litterman": [
        "black_litterman_allocation.csv",
        "black_litterman_weights.csv",
    ],
}


WEIGHT_COLUMN_CANDIDATES = [
    "weight",
    "weights",
    "allocation",
    "recommended_weight",
    "portfolio_weight",
]


ASSET_COLUMN_CANDIDATES = [
    "asset",
    "ticker",
    "symbol",
]


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {col.lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]

    return None


def load_weights_from_csv(path: Path) -> Dict[str, float]:
    df = pd.read_csv(path)

    asset_col = find_column(df, ASSET_COLUMN_CANDIDATES)
    weight_col = find_column(df, WEIGHT_COLUMN_CANDIDATES)

    if asset_col is None or weight_col is None:
        raise ValueError(
            f"Could not identify asset/weight columns in {path}. "
            f"Columns found: {list(df.columns)}"
        )

    weights = {}

    for _, row in df.iterrows():
        asset = str(row[asset_col]).strip()
        weight = float(row[weight_col])

        if asset:
            weights[asset] = weight

    return weights


def load_weights_from_json(path: Path) -> Dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))

    possible_keys = [
        "weights",
        "allocation",
        "recommended_weights",
        "final_weights",
        "optimizer_weights",
    ]

    for key in possible_keys:
        value = data.get(key)

        if isinstance(value, dict):
            return {
                str(asset): float(weight)
                for asset, weight in value.items()
            }

    if all(isinstance(v, (int, float)) for v in data.values()):
        return {
            str(asset): float(weight)
            for asset, weight in data.items()
        }

    raise ValueError(f"Could not identify weights in JSON file: {path}")


def find_optimizer_file(optimizer_name: str) -> Path | None:
    candidates = OPTIMIZER_FILE_MAP.get(optimizer_name, [])

    for filename in candidates:
        path = RESULTS_DIR / filename
        if path.exists():
            return path

    json_candidates = [
        RESULTS_DIR / f"{optimizer_name}_allocation.json",
        RESULTS_DIR / f"{optimizer_name}_weights.json",
        RESULTS_DIR / f"{optimizer_name}_report.json",
    ]

    for path in json_candidates:
        if path.exists():
            return path

    return None


def load_live_optimizer_outputs() -> Dict[str, Dict[str, float]]:
    outputs = {}

    for optimizer_name in OPTIMIZER_FILE_MAP:
        path = find_optimizer_file(optimizer_name)

        if path is None:
            continue

        try:
            if path.suffix.lower() == ".csv":
                outputs[optimizer_name] = load_weights_from_csv(path)
            elif path.suffix.lower() == ".json":
                outputs[optimizer_name] = load_weights_from_json(path)

            print(f"[LOADED] {optimizer_name:<18} from {path}")

        except Exception as exc:
            print(f"[SKIPPED] {optimizer_name:<18} {path} | {exc}")

    return outputs


def get_fallback_optimizer_outputs() -> Dict[str, Dict[str, float]]:
    return {
        "mean_variance": {
            "QQQ": 0.5953,
            "GLD": 0.2240,
            "VIX": 0.1186,
            "BTC-USD": 0.0621,
        },
        "minimum_variance": {
            "SPY": 0.3256,
            "TLT": 0.2938,
            "DIA": 0.2513,
            "GLD": 0.0612,
            "VIX": 0.0566,
            "BTC-USD": 0.0116,
        },
        "risk_parity": {
            "TLT": 0.2202,
            "DIA": 0.1993,
            "SPY": 0.1739,
            "QQQ": 0.1429,
            "GLD": 0.1088,
            "VIX": 0.0694,
            "BTC-USD": 0.0512,
            "ETH-USD": 0.0342,
        },
        "cvar": {
            "SPY": 0.5790,
            "TLT": 0.1552,
            "DIA": 0.0987,
            "GLD": 0.0744,
            "VIX": 0.0693,
            "BTC-USD": 0.0234,
        },
        "bayesian_robust": {
            "SPY": 0.3217,
            "QQQ": 0.2447,
            "DIA": 0.2445,
            "CASH": 0.1217,
            "GLD": 0.0316,
            "BTC-USD": 0.0187,
            "TLT": 0.0159,
            "ETH-USD": 0.0133,
        },
        "black_litterman": {
            "SPY": 0.1993,
            "QQQ": 0.1789,
            "CASH": 0.1525,
            "BTC-USD": 0.1471,
            "DIA": 0.1343,
            "ETH-USD": 0.1110,
            "VIX": 0.0319,
            "GLD": 0.0278,
            "TLT": 0.0176,
        },
    }


def get_optimizer_outputs() -> Dict[str, Dict[str, float]]:
    live_outputs = load_live_optimizer_outputs()
    fallback_outputs = get_fallback_optimizer_outputs()

    merged = fallback_outputs.copy()
    merged.update(live_outputs)

    return merged


def run_loader_demo() -> Dict[str, Dict[str, float]]:
    outputs = get_optimizer_outputs()

    print("\nLIVE OPTIMIZER OUTPUT LOADER")
    print("=" * 80)

    for optimizer, weights in outputs.items():
        source = "LIVE" if find_optimizer_file(optimizer) else "FALLBACK"
        total_weight = sum(weights.values())

        print(
            f"{optimizer:<20} source={source:<8} "
            f"assets={len(weights):<3} total_weight={total_weight:.4f}"
        )

    return outputs


if __name__ == "__main__":
    run_loader_demo()