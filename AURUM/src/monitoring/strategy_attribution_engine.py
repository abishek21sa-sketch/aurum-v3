# src/monitoring/strategy_attribution_engine.py

import json
from pathlib import Path

import pandas as pd


MONITORING_DIR = Path("results/monitoring")
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = MONITORING_DIR / "strategy_contribution.csv"
SUMMARY_PATH = MONITORING_DIR / "strategy_contribution_summary.json"


STRATEGY_RETURNS = {
    "rolling_min_variance": 0.0024,
    "risk_parity": 0.0021,
    "mean_variance": 0.0028,
    "bayesian_robust": 0.0017,
    "black_litterman": 0.0031,
    "regime_aware": 0.0023,
}


STRATEGY_WEIGHTS = {
    "rolling_min_variance": 0.2629,
    "dynamic_allocation": 0.2519,
    "regime_aware": 0.2311,
    "black_litterman": 0.1488,
    "bayesian_robust": 0.1053,
}


def run_strategy_attribution() -> pd.DataFrame:
    rows = []

    for strategy, weight in STRATEGY_WEIGHTS.items():
        strategy_return = STRATEGY_RETURNS.get(strategy, 0.0020)
        contribution = weight * strategy_return

        rows.append(
            {
                "strategy": strategy,
                "strategy_weight": weight,
                "strategy_return": strategy_return,
                "return_contribution": contribution,
            }
        )

    df = pd.DataFrame(rows)

    total_return = float(df["return_contribution"].sum())

    df["contribution_pct"] = df["return_contribution"] / total_return

    df.to_csv(OUTPUT_PATH, index=False)

    summary = {
        "total_strategy_return": total_return,
        "top_contributor": df.sort_values(
            "return_contribution", ascending=False
        ).iloc[0]["strategy"],
        "lowest_contributor": df.sort_values(
            "return_contribution", ascending=True
        ).iloc[0]["strategy"],
        "strategy_count": int(len(df)),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    return df


if __name__ == "__main__":
    print("=" * 80)
    print("AURUM STRATEGY ATTRIBUTION ENGINE")
    print("=" * 80)

    result = run_strategy_attribution()

    print(result.to_string(index=False))
    print("\nSaved:")
    print(f"- {OUTPUT_PATH}")
    print(f"- {SUMMARY_PATH}")