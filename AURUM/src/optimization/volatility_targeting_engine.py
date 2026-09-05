# src/optimization/volatility_targeting_engine.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd


RESULTS_DIR = Path("results/optimization")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in weights.values())

    if total <= 0:
        return {"CASH": 1.0}

    return {
        asset: max(weight, 0.0) / total
        for asset, weight in weights.items()
    }


def apply_volatility_target(
    weights: Dict[str, float],
    estimated_volatility: float,
    target_volatility: float = 0.10,
    min_cash_weight: float = 0.05,
    max_leverage: float = 1.0,
) -> Dict:
    weights = normalize_weights(weights)

    if estimated_volatility <= 0:
        raise ValueError("estimated_volatility must be positive.")

    risk_scale = target_volatility / estimated_volatility
    risk_scale = min(risk_scale, max_leverage)

    adjusted_weights = {}

    for asset, weight in weights.items():
        if asset == "CASH":
            continue

        adjusted_weights[asset] = weight * risk_scale

    risky_weight = sum(adjusted_weights.values())
    cash_weight = 1.0 - risky_weight

    if cash_weight < min_cash_weight:
        excess_risk_weight = min_cash_weight - cash_weight

        scale_down = (risky_weight - excess_risk_weight) / risky_weight

        for asset in adjusted_weights:
            adjusted_weights[asset] *= scale_down

        cash_weight = min_cash_weight

    adjusted_weights["CASH"] = cash_weight

    adjusted_weights = normalize_weights(adjusted_weights)

    report = {
        "target_volatility": target_volatility,
        "estimated_volatility": estimated_volatility,
        "risk_scale": round(risk_scale, 6),
        "raw_weights": weights,
        "volatility_targeted_weights": adjusted_weights,
        "cash_weight": adjusted_weights.get("CASH", 0.0),
        "risk_budget_used": round(
            min(estimated_volatility * risk_scale / target_volatility, 1.0),
            6,
        ),
        "institutional_verdict": (
            "DE_RISKED"
            if risk_scale < 1.0
            else "FULLY_INVESTED"
        ),
    }

    return report


def save_outputs(report: Dict) -> None:
    json_path = RESULTS_DIR / "volatility_target_report.json"
    csv_path = RESULTS_DIR / "volatility_targeted_allocation.csv"

    json_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    rows = [
        {
            "asset": asset,
            "weight": weight,
        }
        for asset, weight in report["volatility_targeted_weights"].items()
    ]

    pd.DataFrame(rows).sort_values(
        "weight",
        ascending=False,
    ).to_csv(csv_path, index=False)

    print(f"Saved: {json_path}")
    print(f"Saved: {csv_path}")


def run_demo() -> Dict:
    constrained_weights = {
        "SPY": 0.30,
        "QQQ": 0.30,
        "TLT": 0.0784,
        "GLD": 0.0490,
        "BTC-USD": 0.0562,
        "ETH-USD": 0.0438,
        "CASH": 0.1725,
    }

    estimated_volatility = 0.16
    target_volatility = 0.10

    report = apply_volatility_target(
        weights=constrained_weights,
        estimated_volatility=estimated_volatility,
        target_volatility=target_volatility,
        min_cash_weight=0.05,
        max_leverage=1.0,
    )

    save_outputs(report)

    print("\nVOLATILITY TARGETING ENGINE")
    print("=" * 70)
    print(f"Estimated Volatility: {report['estimated_volatility']:.2%}")
    print(f"Target Volatility:    {report['target_volatility']:.2%}")
    print(f"Risk Scale:           {report['risk_scale']:.4f}")
    print(f"Cash Weight:          {report['cash_weight']:.2%}")
    print(f"Verdict:              {report['institutional_verdict']}")

    print("\nVOLATILITY TARGETED WEIGHTS")
    print("-" * 70)

    for asset, weight in sorted(
        report["volatility_targeted_weights"].items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        print(f"{asset:<10} {weight:>8.2%}")

    return report


if __name__ == "__main__":
    run_demo()