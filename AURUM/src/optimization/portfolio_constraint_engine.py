# src/optimization/portfolio_constraint_engine.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


RESULTS_DIR = Path("results/optimization")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


ASSET_CLASS_MAP = {
    "SPY": "equity",
    "QQQ": "equity",
    "DIA": "equity",
    "TLT": "bond",
    "GLD": "commodity",
    "VIX": "volatility",
    "BTC-USD": "crypto",
    "ETH-USD": "crypto",
    "CASH": "cash",
}


DEFAULT_CONSTRAINTS = {
    "max_position_weight": 0.30,
    "min_cash_weight": 0.05,
    "max_equity_weight": 0.65,
    "max_bond_weight": 0.35,
    "max_crypto_weight": 0.10,
    "max_commodity_weight": 0.20,
    "max_volatility_weight": 0.10,
}


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in weights.values())

    if total <= 0:
        return {"CASH": 1.0}

    return {k: max(v, 0.0) / total for k, v in weights.items()}


def calculate_group_exposures(weights: Dict[str, float]) -> Dict[str, float]:
    exposures = {}

    for asset, weight in weights.items():
        group = ASSET_CLASS_MAP.get(asset, "unknown")
        exposures[group] = exposures.get(group, 0.0) + weight

    return exposures


def cap_single_positions(
    weights: Dict[str, float],
    max_position_weight: float,
) -> Tuple[Dict[str, float], list]:
    adjusted = weights.copy()
    breaches = []

    excess_cash = 0.0

    for asset, weight in list(adjusted.items()):
        if asset == "CASH":
            continue

        if weight > max_position_weight:
            breach = {
                "constraint": "max_position_weight",
                "asset": asset,
                "original_weight": weight,
                "limit": max_position_weight,
                "excess": weight - max_position_weight,
            }
            breaches.append(breach)

            excess_cash += weight - max_position_weight
            adjusted[asset] = max_position_weight

    adjusted["CASH"] = adjusted.get("CASH", 0.0) + excess_cash

    return adjusted, breaches


def enforce_min_cash(
    weights: Dict[str, float],
    min_cash_weight: float,
) -> Tuple[Dict[str, float], list]:
    adjusted = weights.copy()
    breaches = []

    current_cash = adjusted.get("CASH", 0.0)

    if current_cash >= min_cash_weight:
        return adjusted, breaches

    cash_needed = min_cash_weight - current_cash

    non_cash_assets = {
        asset: weight
        for asset, weight in adjusted.items()
        if asset != "CASH" and weight > 0
    }

    non_cash_total = sum(non_cash_assets.values())

    if non_cash_total <= 0:
        adjusted["CASH"] = 1.0
        return adjusted, breaches

    for asset, weight in non_cash_assets.items():
        reduction = cash_needed * weight / non_cash_total
        adjusted[asset] = max(0.0, weight - reduction)

    adjusted["CASH"] = min_cash_weight

    breaches.append(
        {
            "constraint": "min_cash_weight",
            "original_cash": current_cash,
            "limit": min_cash_weight,
            "cash_added": cash_needed,
        }
    )

    return adjusted, breaches


def cap_group_exposure(
    weights: Dict[str, float],
    group_name: str,
    max_group_weight: float,
) -> Tuple[Dict[str, float], list]:
    adjusted = weights.copy()
    breaches = []

    group_assets = [
        asset
        for asset in adjusted
        if ASSET_CLASS_MAP.get(asset, "unknown") == group_name
    ]

    group_weight = sum(adjusted.get(asset, 0.0) for asset in group_assets)

    if group_weight <= max_group_weight:
        return adjusted, breaches

    excess = group_weight - max_group_weight
    scale = max_group_weight / group_weight if group_weight > 0 else 0

    for asset in group_assets:
        adjusted[asset] *= scale

    adjusted["CASH"] = adjusted.get("CASH", 0.0) + excess

    breaches.append(
        {
            "constraint": f"max_{group_name}_weight",
            "group": group_name,
            "original_weight": group_weight,
            "limit": max_group_weight,
            "excess_moved_to_cash": excess,
        }
    )

    return adjusted, breaches


def apply_portfolio_constraints(
    raw_weights: Dict[str, float],
    constraints: Dict[str, float] | None = None,
) -> Dict:
    constraints = constraints or DEFAULT_CONSTRAINTS

    weights = normalize_weights(raw_weights)
    all_breaches = []

    weights, breaches = cap_single_positions(
        weights,
        constraints["max_position_weight"],
    )
    all_breaches.extend(breaches)

    group_limits = {
        "equity": constraints["max_equity_weight"],
        "bond": constraints["max_bond_weight"],
        "crypto": constraints["max_crypto_weight"],
        "commodity": constraints["max_commodity_weight"],
        "volatility": constraints["max_volatility_weight"],
    }

    for group, limit in group_limits.items():
        weights, breaches = cap_group_exposure(weights, group, limit)
        all_breaches.extend(breaches)

    weights, breaches = enforce_min_cash(
        weights,
        constraints["min_cash_weight"],
    )
    all_breaches.extend(breaches)

    weights = normalize_weights(weights)

    exposures = calculate_group_exposures(weights)

    report = {
        "raw_weights": raw_weights,
        "constrained_weights": weights,
        "group_exposures": exposures,
        "constraints": constraints,
        "breaches": all_breaches,
        "breach_count": len(all_breaches),
        "institutional_verdict": "PASS" if len(all_breaches) == 0 else "ADJUSTED",
    }

    return report


def save_constraint_outputs(report: Dict) -> None:
    json_path = RESULTS_DIR / "portfolio_constraints.json"
    csv_path = RESULTS_DIR / "constrained_allocation.csv"

    json_path.write_text(json.dumps(report, indent=4), encoding="utf-8")

    rows = [
        {
            "asset": asset,
            "weight": weight,
            "asset_class": ASSET_CLASS_MAP.get(asset, "unknown"),
        }
        for asset, weight in report["constrained_weights"].items()
    ]

    pd.DataFrame(rows).sort_values("weight", ascending=False).to_csv(
        csv_path,
        index=False,
    )

    print(f"Saved constraint report: {json_path}")
    print(f"Saved constrained allocation: {csv_path}")


def run_demo() -> Dict:
    raw_weights = {
        "SPY": 0.42,
        "QQQ": 0.31,
        "TLT": 0.08,
        "GLD": 0.05,
        "BTC-USD": 0.09,
        "ETH-USD": 0.07,
        "CASH": -0.02,
    }

    report = apply_portfolio_constraints(raw_weights)
    save_constraint_outputs(report)

    print("\nPORTFOLIO CONSTRAINT ENGINE")
    print("=" * 70)
    print(f"Institutional Verdict: {report['institutional_verdict']}")
    print(f"Breach Count: {report['breach_count']}")

    print("\nCONSTRAINED WEIGHTS")
    print("-" * 70)
    for asset, weight in sorted(
        report["constrained_weights"].items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        print(f"{asset:<10} {weight:>8.2%}")

    print("\nGROUP EXPOSURES")
    print("-" * 70)
    for group, exposure in report["group_exposures"].items():
        print(f"{group:<12} {exposure:>8.2%}")

    return report


if __name__ == "__main__":
    run_demo()