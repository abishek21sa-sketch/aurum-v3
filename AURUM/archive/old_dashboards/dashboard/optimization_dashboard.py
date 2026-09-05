import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st


OPTIMIZED_PATH = Path("results/optimization/realtime_optimized_portfolio.json")
REBALANCE_PATH = Path("results/execution/rebalancing_recommendations.json")
SIMULATION_PATH = Path("results/simulation/portfolio_rebalance_simulation.json")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def weight_df(current: Dict[str, float], recommended: Dict[str, float]) -> pd.DataFrame:
    assets = sorted(set(current) | set(recommended))

    rows = []
    for asset in assets:
        c = float(current.get(asset, 0.0))
        r = float(recommended.get(asset, 0.0))
        rows.append(
            {
                "Asset": asset,
                "Current Weight": c,
                "Recommended Weight": r,
                "Change": r - c,
            }
        )

    return pd.DataFrame(rows)


def trade_df(recommendations: list[Dict[str, Any]]) -> pd.DataFrame:
    if not recommendations:
        return pd.DataFrame()

    return pd.DataFrame(recommendations)


def metrics_df(current: Dict[str, float], recommended: Dict[str, float]) -> pd.DataFrame:
    rows = []

    for metric in current.keys():
        c = float(current.get(metric, 0.0))
        r = float(recommended.get(metric, 0.0))
        rows.append(
            {
                "Metric": metric,
                "Current": c,
                "Recommended": r,
                "Change": r - c,
            }
        )

    return pd.DataFrame(rows)


def pct(value: float) -> str:
    return f"{value:.2%}"


def main() -> None:
    st.set_page_config(
        page_title="AURUM Optimization Dashboard",
        layout="wide",
    )

    st.title("AURUM Real-Time Optimization Dashboard")
    st.caption("Phase 4C — Real-Time Portfolio Operating System")

    optimized = load_json(OPTIMIZED_PATH)
    recommendation = load_json(REBALANCE_PATH)
    simulation = load_json(SIMULATION_PATH)

    if not optimized:
        st.error("Missing optimized portfolio. Run realtime_portfolio_reoptimizer first.")
        st.stop()

    if not recommendation:
        st.warning("Missing rebalancing recommendations.")

    if not simulation:
        st.warning("Missing portfolio simulation.")

    regime = optimized.get("regime", "unknown")
    portfolio_id = optimized.get("portfolio_id", "unknown")

    execution_summary = optimized.get("execution_summary", {})
    allocation_policy = optimized.get("allocation_policy", {})

    st.subheader("Live Portfolio Optimization State")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Portfolio", portfolio_id)
    col2.metric("Regime", regime.upper())
    col3.metric("Urgency", allocation_policy.get("rebalance_urgency", "unknown"))
    col4.metric("Turnover", pct(float(execution_summary.get("turnover", 0.0))))
    col5.metric(
        "Transaction Cost",
        f"{float(execution_summary.get('estimated_transaction_cost', 0.0)):.6f}",
    )

    st.divider()

    current_weights = optimized.get("current_weights", {})
    recommended_weights = optimized.get("recommended_weights", {})

    weights = weight_df(current_weights, recommended_weights)

    st.subheader("Current vs Recommended Portfolio")

    left, right = st.columns(2)

    with left:
        st.write("Current Portfolio")
        st.dataframe(
            weights[["Asset", "Current Weight"]],
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.write("Recommended Portfolio")
        st.dataframe(
            weights[["Asset", "Recommended Weight", "Change"]],
            use_container_width=True,
            hide_index=True,
        )

    st.bar_chart(
        weights.set_index("Asset")[["Current Weight", "Recommended Weight"]]
    )

    st.divider()

    st.subheader("Rebalancing Recommendations")

    trades = trade_df(recommendation.get("trade_recommendations", []))

    if not trades.empty:
        st.dataframe(trades, use_container_width=True, hide_index=True)
    else:
        st.info("No trade recommendations available.")

    st.divider()

    if simulation:
        st.subheader("Before vs After Portfolio Simulation")

        current_metrics = simulation.get("current_portfolio", {}).get("metrics", {})
        recommended_metrics = simulation.get("recommended_portfolio", {}).get("metrics", {})
        improvement = simulation.get("improvement", {})
        risk_reduction = improvement.get("risk_reduction", {})

        metrics = metrics_df(current_metrics, recommended_metrics)

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Volatility Reduction",
            pct(float(risk_reduction.get("volatility_reduction", 0.0))),
        )
        c2.metric(
            "CVaR Reduction",
            pct(float(risk_reduction.get("cvar_reduction", 0.0))),
        )
        c3.metric(
            "Drawdown Reduction",
            pct(float(risk_reduction.get("drawdown_reduction", 0.0))),
        )

        st.dataframe(metrics, use_container_width=True, hide_index=True)

        st.bar_chart(
            metrics.set_index("Metric")[["Current", "Recommended"]]
        )

    st.divider()

    st.subheader("Execution Summary")

    summary = {
        "execution_decision": recommendation.get("execution_decision"),
        "turnover": execution_summary.get("turnover"),
        "max_turnover": execution_summary.get("max_turnover"),
        "turnover_status": execution_summary.get("turnover_status"),
        "estimated_transaction_cost": execution_summary.get("estimated_transaction_cost"),
        "cost_bps": execution_summary.get("cost_bps"),
    }

    st.json(summary)


if __name__ == "__main__":
    main()