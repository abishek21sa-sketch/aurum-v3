from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


RESULTS_DIR = Path("results/research")

REGISTRY_PATH = RESULTS_DIR / "strategy_registry.json"
STRESS_PATH = RESULTS_DIR / "strategy_stress_results.csv"
SCORES_PATH = RESULTS_DIR / "robustness_scores.csv"
REPORT_PATH = RESULTS_DIR / "strategy_research_report.json"


def ensure_research_outputs() -> None:
    missing = [
        path
        for path in [REGISTRY_PATH, STRESS_PATH, SCORES_PATH, REPORT_PATH]
        if not path.exists()
    ]

    if missing:
        from src.research.strategy_registry import build_strategy_registry
        from src.research.strategy_stress_tester import stress_test_strategies
        from src.research.robustness_score_engine import calculate_robustness_scores
        from src.research.strategy_research_report import generate_strategy_research_report

        build_strategy_registry()
        stress_test_strategies()
        calculate_robustness_scores()
        generate_strategy_research_report()


@st.cache_data(ttl=30)
def load_data():
    ensure_research_outputs()

    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        registry = json.load(f)

    stress = pd.read_csv(STRESS_PATH)
    scores = pd.read_csv(SCORES_PATH)

    with REPORT_PATH.open("r", encoding="utf-8") as f:
        report = json.load(f)

    return registry, stress, scores, report


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_score(value: float) -> str:
    return f"{value:.4f}"


def main() -> None:
    st.set_page_config(
        page_title="AURUM Strategy Research Platform",
        page_icon="📊",
        layout="wide",
    )

    registry, stress, scores, report = load_data()

    st.title("AURUM Strategy Research Platform")
    st.caption("Phase 4E — Institutional Strategy Stress Testing & Robustness Lab")

    top = scores.sort_values("robustness_score", ascending=False).iloc[0]
    worst = scores.sort_values("robustness_score", ascending=True).iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Strategies", scores["strategy_id"].nunique())
    c2.metric("Stress Scenarios", stress["scenario_id"].nunique())
    c3.metric("Top Strategy", top["strategy_name"])
    c4.metric("Top Robustness Score", format_score(top["robustness_score"]))

    st.divider()

    st.subheader("Institutional Robustness Rankings")

    ranking_view = scores[
        [
            "rank",
            "strategy_name",
            "category",
            "robustness_score",
            "avg_stressed_return",
            "avg_stressed_volatility",
            "avg_stressed_sharpe",
            "worst_drawdown",
            "avg_liquidity_cost",
            "base_turnover",
        ]
    ].copy()

    st.dataframe(
        ranking_view,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        scores.set_index("strategy_name")["robustness_score"],
        use_container_width=True,
    )

    st.divider()

    st.subheader("Scenario Stress Results")

    scenario = st.selectbox(
        "Select scenario",
        sorted(stress["scenario_id"].unique()),
    )

    scenario_df = (
        stress[stress["scenario_id"] == scenario]
        .sort_values("stressed_sharpe", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        scenario_df[
            [
                "strategy_name",
                "category",
                "stressed_return",
                "stressed_volatility",
                "stressed_sharpe",
                "stressed_max_drawdown",
                "liquidity_cost",
                "stress_loss",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        scenario_df.set_index("strategy_name")["stressed_sharpe"],
        use_container_width=True,
    )

    st.divider()

    st.subheader("Strategy Profile")

    strategy_name = st.selectbox(
        "Select strategy",
        scores["strategy_name"].tolist(),
    )

    selected_row = scores[scores["strategy_name"] == strategy_name].iloc[0]
    selected_id = selected_row["strategy_id"]
    profile = registry[selected_id]

    st.markdown(f"### {profile['name']}")
    st.write(profile["description"])

    p1, p2, p3, p4 = st.columns(4)

    p1.metric("Category", profile["category"])
    p2.metric("Rank", int(selected_row["rank"]))
    p3.metric("Robustness Score", format_score(selected_row["robustness_score"]))
    p4.metric("Avg Stress Sharpe", format_score(selected_row["avg_stressed_sharpe"]))

    with st.expander("Detailed Strategy Notes", expanded=True):
        st.markdown("**Expected Behavior**")
        st.write(profile["expected_behavior"])

        st.markdown("**Risk Profile**")
        st.write(profile["risk_profile"])

        st.markdown("**Turnover Profile**")
        st.write(profile["turnover_profile"])

        st.markdown("**Regime Fit**")
        st.write(", ".join(profile["regime_fit"]))

    st.subheader("Scenario Winners")

    winners = report.get("scenario_winners", {})
    winner_rows = []

    for scenario_id, data in winners.items():
        winner_rows.append(
            {
                "scenario": scenario_id,
                "best_strategy": data["best_strategy"],
                "stressed_return": data["stressed_return"],
                "stressed_volatility": data["stressed_volatility"],
                "stressed_sharpe": data["stressed_sharpe"],
                "stressed_max_drawdown": data["stressed_max_drawdown"],
            }
        )

    winner_df = pd.DataFrame(winner_rows)
    st.dataframe(winner_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Phase 4E Research Summary")

    st.success(
        f"Top institutional strategy: {top['strategy_name']} "
        f"with robustness score {top['robustness_score']:.4f}."
    )

    st.warning(
        f"Lowest ranked strategy under stress: {worst['strategy_name']} "
        f"with robustness score {worst['robustness_score']:.4f}."
    )


if __name__ == "__main__":
    main()