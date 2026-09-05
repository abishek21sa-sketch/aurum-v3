from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


REPORT_PATH = Path("results/portfolio_lab/portfolio_lab_report.json")
COMPARISON_PATH = Path("results/portfolio_lab/portfolio_lab_comparison.csv")


def ensure_lab_outputs() -> None:
    if REPORT_PATH.exists() and COMPARISON_PATH.exists():
        return

    from src.lab.portfolio_lab_engine import run_portfolio_lab

    run_portfolio_lab()


@st.cache_data(ttl=30)
def load_data():
    ensure_lab_outputs()

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    comparison = pd.read_csv(COMPARISON_PATH)

    return report, comparison


def fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def main() -> None:
    st.set_page_config(
        page_title="AURUM Portfolio Laboratory",
        page_icon="🧪",
        layout="wide",
    )

    report, comparison = load_data()

    st.title("AURUM Portfolio Laboratory")
    st.caption("Phase 4I — Interactive Portfolio Scenario Comparison Lab")

    summary = report["summary"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Scenarios", report["scenario_count"])
    c2.metric("Best Sharpe", summary["best_sharpe_scenario"])
    c3.metric("Lowest Volatility", summary["lowest_volatility_scenario"])
    c4.metric("Lowest Drawdown", summary["lowest_drawdown_scenario"])

    st.divider()

    st.subheader("Scenario Comparison")

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Risk / Return View")

    chart_df = comparison.set_index("scenario")[
        [
            "expected_return",
            "volatility",
            "sharpe",
            "cvar_proxy",
            "max_drawdown_proxy",
            "cash_weight",
        ]
    ]

    st.bar_chart(chart_df[["expected_return", "volatility"]])
    st.bar_chart(chart_df[["sharpe"]])
    st.bar_chart(chart_df[["cvar_proxy", "max_drawdown_proxy"]])

    st.divider()

    st.subheader("Scenario Drilldown")

    selected = st.selectbox(
        "Select scenario",
        comparison["scenario"].tolist(),
    )

    selected_row = comparison[comparison["scenario"] == selected].iloc[0]
    scenario_payload = report["scenarios"][selected]

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Expected Return", fmt_pct(selected_row["expected_return"]))
    m2.metric("Volatility", fmt_pct(selected_row["volatility"]))
    m3.metric("Sharpe", f"{selected_row['sharpe']:.4f}")
    m4.metric("Cash Weight", fmt_pct(selected_row["cash_weight"]))

    m5, m6, m7 = st.columns(3)

    m5.metric("CVaR Proxy", fmt_pct(selected_row["cvar_proxy"]))
    m6.metric("Max Drawdown Proxy", fmt_pct(selected_row["max_drawdown_proxy"]))
    m7.metric("Concentration", f"{selected_row['concentration']:.4f}")

    st.markdown("### Delta vs Current")

    delta_cols = [
        "expected_return_change",
        "volatility_change",
        "sharpe_change",
        "cvar_proxy_change",
        "max_drawdown_proxy_change",
        "concentration_change",
        "cash_weight_change",
    ]

    delta_view = selected_row[delta_cols].to_frame(name="delta").reset_index()
    delta_view.columns = ["metric", "delta"]

    st.dataframe(delta_view, use_container_width=True, hide_index=True)

    st.markdown("### Scenario Weights")

    weights = pd.DataFrame(
        list(scenario_payload["weights"].items()),
        columns=["asset", "weight"],
    ).sort_values("weight", ascending=False)

    st.dataframe(weights, use_container_width=True, hide_index=True)
    st.bar_chart(weights.set_index("asset")["weight"])

    st.divider()

    st.subheader("Institutional Interpretation")

    if selected == summary["best_sharpe_scenario"]:
        st.success("This scenario has the strongest Sharpe ratio among tested alternatives.")

    if selected == summary["lowest_volatility_scenario"]:
        st.info("This scenario has the lowest volatility among tested alternatives.")

    if selected == summary["lowest_drawdown_scenario"]:
        st.info("This scenario has the lowest drawdown proxy among tested alternatives.")

    if selected_row["volatility_change"] > 0:
        st.warning("This scenario increases volatility versus the current portfolio.")

    if selected_row["cash_weight"] < 0.05:
        st.warning("This scenario has a low cash buffer.")


if __name__ == "__main__":
    main()