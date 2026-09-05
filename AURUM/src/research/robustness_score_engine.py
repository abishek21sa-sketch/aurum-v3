from __future__ import annotations

from pathlib import Path

import pandas as pd


RESULTS_DIR = Path("results/research")
STRESS_PATH = RESULTS_DIR / "strategy_stress_results.csv"


def min_max_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    min_value = series.min()
    max_value = series.max()

    if max_value == min_value:
        return pd.Series([1.0] * len(series), index=series.index)

    score = (series - min_value) / (max_value - min_value)

    if not higher_is_better:
        score = 1.0 - score

    return score


def calculate_robustness_scores() -> Path:
    if not STRESS_PATH.exists():
        from src.research.strategy_stress_tester import stress_test_strategies

        stress_test_strategies()

    df = pd.read_csv(STRESS_PATH)

    grouped = (
        df.groupby(["strategy_id", "strategy_name", "category"])
        .agg(
            avg_stressed_return=("stressed_return", "mean"),
            worst_stressed_return=("stressed_return", "min"),
            avg_stressed_volatility=("stressed_volatility", "mean"),
            worst_drawdown=("stressed_max_drawdown", "min"),
            avg_stressed_sharpe=("stressed_sharpe", "mean"),
            avg_liquidity_cost=("liquidity_cost", "mean"),
            avg_stress_loss=("stress_loss", "mean"),
            base_turnover=("base_turnover", "mean"),
        )
        .reset_index()
    )

    grouped["return_score"] = min_max_score(grouped["avg_stressed_return"], True)
    grouped["worst_return_score"] = min_max_score(grouped["worst_stressed_return"], True)
    grouped["volatility_score"] = min_max_score(grouped["avg_stressed_volatility"], False)
    grouped["drawdown_score"] = min_max_score(grouped["worst_drawdown"].abs(), False)
    grouped["sharpe_score"] = min_max_score(grouped["avg_stressed_sharpe"], True)
    grouped["liquidity_score"] = min_max_score(grouped["avg_liquidity_cost"], False)
    grouped["turnover_score"] = min_max_score(grouped["base_turnover"], False)

    grouped["robustness_score"] = (
        0.20 * grouped["return_score"]
        + 0.15 * grouped["worst_return_score"]
        + 0.15 * grouped["volatility_score"]
        + 0.20 * grouped["drawdown_score"]
        + 0.15 * grouped["sharpe_score"]
        + 0.10 * grouped["liquidity_score"]
        + 0.05 * grouped["turnover_score"]
    )

    grouped = grouped.sort_values("robustness_score", ascending=False)
    grouped["rank"] = range(1, len(grouped) + 1)

    output_path = RESULTS_DIR / "robustness_scores.csv"
    grouped.to_csv(output_path, index=False)

    return output_path


if __name__ == "__main__":
    path = calculate_robustness_scores()
    print("=" * 80)
    print("AURUM ROBUSTNESS SCORE ENGINE")
    print("=" * 80)
    print(f"Saved: {path}")