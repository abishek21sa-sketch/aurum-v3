from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


RESULTS_DIR = Path("results/research")
SCORES_PATH = RESULTS_DIR / "robustness_scores.csv"
STRESS_PATH = RESULTS_DIR / "strategy_stress_results.csv"


def generate_strategy_research_report() -> tuple[Path, Path]:
    if not SCORES_PATH.exists():
        from src.research.robustness_score_engine import calculate_robustness_scores

        calculate_robustness_scores()

    scores = pd.read_csv(SCORES_PATH)
    stress = pd.read_csv(STRESS_PATH)

    best = scores.iloc[0].to_dict()
    worst = scores.iloc[-1].to_dict()

    scenario_winners = {}

    for scenario_id, group in stress.groupby("scenario_id"):
        winner = group.sort_values("stressed_sharpe", ascending=False).iloc[0]
        scenario_winners[scenario_id] = {
            "best_strategy": winner["strategy_name"],
            "stressed_return": float(winner["stressed_return"]),
            "stressed_volatility": float(winner["stressed_volatility"]),
            "stressed_sharpe": float(winner["stressed_sharpe"]),
            "stressed_max_drawdown": float(winner["stressed_max_drawdown"]),
        }

    report = {
        "platform": "AURUM",
        "phase": "Phase 4E - Institutional Strategy Research Platform",
        "status": "complete",
        "summary": {
            "strategy_count": int(scores["strategy_id"].nunique()),
            "scenario_count": int(stress["scenario_id"].nunique()),
            "top_strategy": best["strategy_name"],
            "top_strategy_score": float(best["robustness_score"]),
            "lowest_ranked_strategy": worst["strategy_name"],
            "lowest_ranked_score": float(worst["robustness_score"]),
        },
        "scenario_winners": scenario_winners,
        "rankings": scores.to_dict(orient="records"),
    }

    json_path = RESULTS_DIR / "strategy_research_report.json"
    txt_path = RESULTS_DIR / "strategy_research_report.txt"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM STRATEGY RESEARCH REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Top Strategy: {best['strategy_name']}")
    lines.append(f"Robustness Score: {best['robustness_score']:.4f}")
    lines.append("")
    lines.append("STRATEGY RANKINGS")
    lines.append("-" * 80)

    for _, row in scores.iterrows():
        lines.append(
            f"{int(row['rank'])}. {row['strategy_name']} | "
            f"Score={row['robustness_score']:.4f} | "
            f"Avg Stress Sharpe={row['avg_stressed_sharpe']:.4f} | "
            f"Worst Drawdown={row['worst_drawdown']:.4f}"
        )

    lines.append("")
    lines.append("SCENARIO WINNERS")
    lines.append("-" * 80)

    for scenario, data in scenario_winners.items():
        lines.append(
            f"{scenario}: {data['best_strategy']} | "
            f"Sharpe={data['stressed_sharpe']:.4f}"
        )

    txt_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, txt_path


if __name__ == "__main__":
    json_path, txt_path = generate_strategy_research_report()
    print("=" * 80)
    print("AURUM STRATEGY RESEARCH REPORT")
    print("=" * 80)
    print(f"JSON: {json_path}")
    print(f"TXT:  {txt_path}")