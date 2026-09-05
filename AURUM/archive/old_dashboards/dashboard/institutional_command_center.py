# src/dashboard/institutional_command_center.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.postgres_manager import PostgresManager

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="aurum_refresh")
except Exception:
    pass

try:
    from src.dashboard.live_refresh_dashboard_adapter import LiveRefreshDashboardAdapter

    live_state = LiveRefreshDashboardAdapter().load_state()

    st.subheader("Live Market Refresh")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Provider", live_state.provider)
    col2.metric("Regime", live_state.regime)
    col3.metric("Anomaly", live_state.anomaly_severity)
    col4.metric("Portfolio Action", live_state.portfolio_action)

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Stress Score", f"{live_state.stress_score:.4f}")
    col6.metric("Digital Twin", live_state.digital_twin_state)
    col7.metric("Probability Type", live_state.probability_type)
    col8.metric("Refresh Cycles", live_state.cycles_completed)

    st.caption(f"Last refresh: {live_state.timestamp}")

except Exception as exc:
    st.warning(f"Live refresh dashboard state unavailable: {exc}")

st.set_page_config(
    page_title="AURUM Institutional Command Center",
    page_icon="📈",
    layout="wide",
)

ROOT = Path("results")


def load_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        path = Path(path)
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    try:
        path = Path(path)
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
    except Exception:
        return []


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def pct(value: Any) -> str:
    return f"{safe_float(value):.2%}"


def num(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def weights_to_df(weights: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for asset, weight in weights.items():
        try:
            rows.append({"Asset": asset, "Weight": float(weight)})
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Weight", ascending=False)


def trades_to_df(trades: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for asset, trade in trades.items():
        try:
            trade = float(trade)
            rows.append(
                {
                    "Asset": asset,
                    "Trade": trade,
                    "Action": "BUY" if trade > 0 else "SELL" if trade < 0 else "HOLD",
                    "Abs Trade": abs(trade),
                }
            )
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Abs Trade", ascending=False)


def classify_asset_group(asset: str) -> str:
    asset_u = asset.upper()
    if asset_u in {"SPY", "QQQ", "DIA"}:
        return "Equity"
    if asset_u in {"TLT", "IEF", "SHY"}:
        return "Fixed Income"
    if asset_u in {"GLD", "SLV", "DBC"}:
        return "Commodity"
    if "BTC" in asset_u or "ETH" in asset_u:
        return "Crypto"
    if asset_u in {"CASH", "USD"} or asset.lower() == "cash":
        return "Cash"
    return "Other"


def exposure_df_from_positions(positions: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for asset, weight in positions.items():
        rows.append(
            {
                "Group": classify_asset_group(asset),
                "Weight": safe_float(weight),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).groupby("Group", as_index=False)["Weight"].sum()


portfolio_state = load_json(ROOT / "portfolio" / "institutional_portfolio_state.json")
operating_cycle = load_json(ROOT / "orchestrator" / "operating_cycle.json")
approval = load_json(ROOT / "orchestrator" / "decision_approval.json")
memory_summary = load_json(ROOT / "memory" / "memory_summary.json")
memory_log = load_jsonl(ROOT / "memory" / "portfolio_memory.jsonl")
cio_brief = load_json(ROOT / "ai" / "cio_daily_brief.json")
optimized_portfolio = load_json(ROOT / "optimization" / "realtime_optimized_portfolio.json")
live_positions = load_json(ROOT / "portfolio" / "live_positions.json")
governance_report = load_json(ROOT / "governance" / "execution_governance_report.json")
audit_report = load_json(ROOT / "governance" / "institutional_audit_report.json")
event_triggers = load_json(ROOT / "orchestrator" / "event_triggers.json")
rebalance_schedule = load_json(ROOT / "orchestrator" / "rebalance_schedule.json")
audit_records = load_jsonl(ROOT / "governance" / "current_cycle_audit_log.jsonl")
performance_snapshot = load_json(ROOT / "monitoring" / "live_performance_snapshot.json")
performance_summary = load_json(ROOT / "monitoring" / "live_performance_summary.json")
performance_history = load_jsonl(ROOT / "monitoring" / "performance_history.jsonl")
risk_snapshot = load_json(ROOT / "monitoring" / "risk_snapshot.json")
risk_summary = load_json(ROOT / "monitoring" / "risk_history_summary.json")
risk_history = load_jsonl(ROOT / "monitoring" / "risk_history.jsonl")
event_stream_snapshot = load_json(ROOT / "monitoring" / "event_stream_snapshot.json")
event_stream_summary = load_json(ROOT / "monitoring" / "event_stream_summary.json")
event_stream_history = load_jsonl(ROOT / "monitoring" / "event_stream_history.jsonl")
institutional_readiness = load_json(ROOT / "institutional" / "institutional_readiness_report.json")
runtime_integrity = load_json(ROOT / "institutional" / "runtime_integrity_audit.json")
coherence_gate = load_json(ROOT / "institutional" / "runtime_coherence_gate.json")
latest_runtime_state = load_json(ROOT / "institutional" / "latest_institutional_runtime_state.json")
decision_cycle_report = load_json(ROOT / "institutional" / "institutional_decision_cycle_report.json")

portfolio_lab_report = load_json(ROOT / "portfolio_lab" / "portfolio_lab_report.json")
portfolio_lab_comparison_path = ROOT / "portfolio_lab" / "portfolio_lab_comparison.csv"

strategy_research_report = load_json(ROOT / "research" / "strategy_research_report.json")
robustness_scores_path = ROOT / "research" / "robustness_scores.csv"

phase4_final_report = load_json(ROOT / "phase4" / "phase4_final_completion_report.json")

market_state = portfolio_state.get("market_state", {})
risk_state = portfolio_state.get("risk_state", {})
governance_state = portfolio_state.get("governance_state", {})
execution_state = portfolio_state.get("execution_state", {})
position_state = portfolio_state.get("position_state", {})
performance_state = portfolio_state.get("performance_state", {})

market_regime = market_state.get("market_regime") or market_state.get("regime") or "unknown"
stress_score = market_state.get("market_stress") or market_state.get("stress_score") or 0.0
risk_level = risk_state.get("risk_level", "unknown")
approval_status = approval.get("status", "UNKNOWN")
governance_status = (
    governance_state.get("governance_status")
    or governance_state.get("status")
    or approval.get("governance_status")
    or "UNKNOWN"
)
portfolio_status = (
    portfolio_state.get("status")
    or portfolio_state.get("portfolio_status")
    or live_positions.get("status")
    or position_state.get("status")
    or "ACTIVE"
)

positions = live_positions.get("positions") or position_state.get("positions") or {}
target_weights = (
    optimized_portfolio.get("recommended_weights")
    or optimized_portfolio.get("target_weights")
    or portfolio_state.get("optimization_state", {}).get("target_weights")
    or {}
)
rebalance_trades = optimized_portfolio.get("rebalance_trades", {})

positions_df = weights_to_df(positions)
target_df = weights_to_df(target_weights)
trades_df = trades_to_df(rebalance_trades)
exposure_df = exposure_df_from_positions(positions)

def load_csv_safe(path: Path) -> pd.DataFrame:
    try:
        path = Path(path)
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def show_json_block(title: str, payload: Dict[str, Any]) -> None:
    with st.expander(title, expanded=False):
        if payload:
            st.json(payload)
        else:
            st.info("No data found.")

def find_json_artifacts(keywords: List[str]) -> List[Path]:
    files = []
    if not ROOT.exists():
        return files

    for path in ROOT.rglob("*.json"):
        name = str(path).lower()
        if any(keyword.lower() in name for keyword in keywords):
            files.append(path)

    return sorted(files)


def show_artifact_browser(title: str, keywords: List[str]) -> None:
    st.subheader(title)
    files = find_json_artifacts(keywords)

    if not files:
        st.info("No matching artifacts found.")
        return

    for file in files:
        with st.expander(str(file), expanded=False):
            st.json(load_json(file, default={}))


def database_table_count(table_name: str) -> int:
    try:
        from src.database.postgres_manager import PostgresManager

        db = PostgresManager()
        row = db.fetch_one(f"SELECT COUNT(*) AS n FROM {table_name};")
        return int(row["n"]) if row else 0
    except Exception:
        return 0


def show_database_counts() -> None:
    tables = [
        "market_ticks",
        "market_features",
        "market_signals",
        "portfolio_state",
        "portfolio_decisions",
        "committee_decisions",
        "execution_log",
        "learning_events",
    ]

    rows = []

    for table in tables:
        rows.append(
            {
                "table": table,
                "rows": database_table_count(table),
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.sidebar.title("AURUM")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Market",
        "Risk",
        "Optimization",
        "Portfolio Lab",
        "Strategy Research",
        "Execution",
        "Governance",
        "Institutional Readiness",
        "Runtime Integrity",
        "Memory",
        "AI CIO",
        "Control Tower",
        "System Health",
        "AI Research Firm",
        "Daily CIO Brief",
        "Portfolio OS",
        "Database",
        "Reliability",
        "Phase 4 Closeout",
    ]
)

st.sidebar.markdown("---")
st.sidebar.write("Phase 4G")
st.sidebar.write("Institutional Control Tower")


if page == "Overview":
    st.title("AURUM Institutional Command Center")

    c1, c2, c3 = st.columns(3)
    c1.metric("Market Regime", str(market_regime).upper())
    c2.metric("Stress Score", num(stress_score, 2))
    c3.metric("Risk Level", str(risk_level).upper())

    c4, c5, c6 = st.columns(3)
    c4.metric("Approval", approval_status)
    c5.metric("Governance", governance_status)
    c6.metric("Portfolio Status", portfolio_status)

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Autonomous Operating Cycle")
        oc1, oc2, oc3, oc4 = st.columns(4)
        oc1.metric("Status", operating_cycle.get("overall_status", "UNKNOWN"))
        oc2.metric("Triggers", operating_cycle.get("trigger_count", 0))
        oc3.metric("Schedule", operating_cycle.get("schedule_type", "UNKNOWN"))
        oc4.metric("Memory Cycles", operating_cycle.get("memory_cycles", 0))
        st.json(operating_cycle)

    with right:
        st.subheader("Portfolio Snapshot")
        if not positions_df.empty:
            st.bar_chart(positions_df.set_index("Asset")["Weight"])
            st.dataframe(positions_df, use_container_width=True, hide_index=True)
        else:
            st.info("No live position data found.")


elif page == "Market":
    st.title("Market")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Regime", str(market_regime).upper())
    c2.metric("Stress", num(stress_score, 2))
    c3.metric("State", str(market_state.get("state_label", "unknown")).upper())
    c4.metric("Ticker", market_state.get("raw", {}).get("latest_ticker", "—"))

    st.markdown("---")
    st.json(market_state)


elif page == "Risk":
    st.title("Risk")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Level", str(risk_level).upper())
    c2.metric("VaR 95", num(risk_state.get("var_95", 0), 4))
    c3.metric("CVaR 95", num(risk_state.get("cvar_95", 0), 4))
    c4.metric("Drawdown", num(risk_state.get("drawdown", 0), 4))

    st.markdown("---")

    stress_val = safe_float(stress_score)
    var_val = abs(safe_float(risk_state.get("var_95", 0)))
    cvar_val = abs(safe_float(risk_state.get("cvar_95", 0)))
    dd_val = abs(safe_float(risk_state.get("drawdown", 0)))

    st.subheader("Risk Trends")

    r1, r2, r3, r4 = st.columns(4)

    r1.metric(
        "Stress Score",
        num(risk_snapshot.get("stress_score", 0), 2),
    )

    r2.metric(
        "VaR 95",
        pct(risk_snapshot.get("var_95", 0)),
    )

    r3.metric(
        "CVaR 95",
        pct(risk_snapshot.get("cvar_95", 0)),
    )

    r4.metric(
        "Drawdown",
        pct(abs(risk_snapshot.get("drawdown", 0))),
    )

    with st.expander("Raw Risk JSON"):
        st.json(risk_state)

    if risk_history:
        risk_df = pd.DataFrame(risk_history)

        if "timestamp" in risk_df.columns:

            c1, c2 = st.columns(2)

            with c1:
                st.subheader("Stress History")

                stress_df = risk_df[["timestamp", "stress_score"]].copy()
                stress_df["stress_score"] = stress_df["stress_score"].astype(float)

                st.line_chart(
                    stress_df.set_index("timestamp")["stress_score"]
                )

            with c2:
                st.subheader("VaR History")

                var_df = risk_df[["timestamp", "var_95"]].copy()
                var_df["var_95"] = var_df["var_95"].astype(float)

                st.line_chart(
                    var_df.set_index("timestamp")["var_95"]
                )

            c3, c4 = st.columns(2)

            with c3:
                st.subheader("CVaR History")

                cvar_df = risk_df[["timestamp", "cvar_95"]].copy()
                cvar_df["cvar_95"] = cvar_df["cvar_95"].astype(float)

                st.line_chart(
                    cvar_df.set_index("timestamp")["cvar_95"]
                )

            with c4:
                st.subheader("Drawdown History")

                dd_df = risk_df[["timestamp", "drawdown"]].copy()
                dd_df["drawdown"] = (
                    dd_df["drawdown"]
                    .astype(float)
                    .abs()
                )

                st.line_chart(
                    dd_df.set_index("timestamp")["drawdown"]
                )

    st.subheader("Risk Summary")

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "History Points",
        risk_summary.get("history_points", 0),
    )

    s2.metric(
        "Critical Cycles",
        risk_summary.get("critical_cycles", 0),
    )

    s3.metric(
        "Review Cycles",
        risk_summary.get("review_required_cycles", 0),
    )

    s4.metric(
        "Max Stress",
        num(risk_summary.get("max_stress_score", 0), 2),
    )


elif page == "Optimization":
    st.title("Optimization")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Optimizer", optimized_portfolio.get("optimizer", {}).get("method", "unknown"))
    c2.metric("Regime", optimized_portfolio.get("regime", "unknown"))
    c3.metric("Turnover", pct(optimized_portfolio.get("execution_summary", {}).get("turnover", 0)))
    c4.metric("Max Turnover", pct(optimized_portfolio.get("execution_summary", {}).get("max_turnover", 0)))

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Target Allocation")
        if not target_df.empty:
            st.bar_chart(target_df.set_index("Asset")["Weight"])
            st.dataframe(target_df, use_container_width=True, hide_index=True)
        else:
            st.info("No target weights found.")

    with right:
        st.subheader("Rebalance Trades")
        if not trades_df.empty:
            st.bar_chart(trades_df.set_index("Asset")["Trade"])
            st.dataframe(trades_df, use_container_width=True, hide_index=True)
        else:
            st.info("No rebalance trades found.")

    with st.expander("Raw Optimizer JSON"):
        st.json(optimized_portfolio)

elif page == "Portfolio Lab":
    st.title("Portfolio Laboratory")

    comparison_df = load_csv_safe(portfolio_lab_comparison_path)
    summary = portfolio_lab_report.get("summary", {})

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Scenarios", portfolio_lab_report.get("scenario_count", 0))
    c2.metric("Best Sharpe", summary.get("best_sharpe_scenario", "UNKNOWN"))
    c3.metric("Lowest Volatility", summary.get("lowest_volatility_scenario", "UNKNOWN"))
    c4.metric("Lowest Drawdown", summary.get("lowest_drawdown_scenario", "UNKNOWN"))

    st.markdown("---")

    if not comparison_df.empty:
        st.subheader("Scenario Comparison")
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        metric_cols = [
            col for col in [
                "expected_return",
                "volatility",
                "sharpe",
                "cvar_proxy",
                "max_drawdown_proxy",
                "cash_weight",
            ]
            if col in comparison_df.columns
        ]

        if metric_cols and "scenario" in comparison_df.columns:
            st.subheader("Scenario Metrics")
            st.bar_chart(comparison_df.set_index("scenario")[metric_cols])

        selected = st.selectbox(
            "Scenario Drilldown",
            comparison_df["scenario"].tolist(),
        )

        selected_row = comparison_df[comparison_df["scenario"] == selected].iloc[0]

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Expected Return", pct(selected_row.get("expected_return", 0)))
        d2.metric("Volatility", pct(selected_row.get("volatility", 0)))
        d3.metric("Sharpe", num(selected_row.get("sharpe", 0), 4))
        d4.metric("Cash", pct(selected_row.get("cash_weight", 0)))

        scenarios = portfolio_lab_report.get("scenarios", {})
        selected_payload = scenarios.get(selected, {})
        weights = selected_payload.get("weights", {})

        weights_df = weights_to_df(weights)

        st.subheader("Scenario Weights")
        if not weights_df.empty:
            st.bar_chart(weights_df.set_index("Asset")["Weight"])
            st.dataframe(weights_df, use_container_width=True, hide_index=True)
        else:
            st.info("No scenario weights found.")

    else:
        st.warning("Portfolio Lab comparison data not found.")

    show_json_block("Raw Portfolio Lab Report", portfolio_lab_report)

elif page == "Strategy Research":
    st.title("Strategy Research Platform")

    scores_df = load_csv_safe(robustness_scores_path)
    summary = strategy_research_report.get("summary", {})

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Strategies", summary.get("strategy_count", 0))
    c2.metric("Scenarios", summary.get("scenario_count", 0))
    c3.metric("Top Strategy", summary.get("top_strategy", "UNKNOWN"))
    c4.metric("Top Score", num(summary.get("top_strategy_score", 0), 4))

    st.markdown("---")

    if not scores_df.empty:
        st.subheader("Robustness Rankings")
        st.dataframe(scores_df, use_container_width=True, hide_index=True)

        if "strategy_name" in scores_df.columns and "robustness_score" in scores_df.columns:
            st.bar_chart(scores_df.set_index("strategy_name")["robustness_score"])
    else:
        st.warning("Robustness scores not found.")

    scenario_winners = strategy_research_report.get("scenario_winners", {})

    if scenario_winners:
        st.subheader("Scenario Winners")
        winner_df = pd.DataFrame(
            [
                {"scenario": scenario, **payload}
                for scenario, payload in scenario_winners.items()
            ]
        )
        st.dataframe(winner_df, use_container_width=True, hide_index=True)

    show_json_block("Raw Strategy Research Report", strategy_research_report)

elif page == "Execution":
    st.title("Execution")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reports", execution_state.get("report_count", 0))
    c2.metric("Fill Ratio", pct(execution_state.get("aggregate_fill_ratio", 0)))
    c3.metric("Exec Cost", f"{num(execution_state.get('total_execution_cost_bps', 0), 2)} bps")
    c4.metric("Cash", pct(position_state.get("cash_weight", live_positions.get("cash_weight", 0))))

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Live Positions")
        if not positions_df.empty:
            st.bar_chart(positions_df.set_index("Asset")["Weight"])
            st.dataframe(positions_df, use_container_width=True, hide_index=True)
        else:
            st.info("No position data found.")

    with right:
        st.subheader("Execution Status")
        status_counts = execution_state.get("status_counts", {})
        if status_counts:
            status_df = pd.DataFrame([{"Status": k, "Count": v} for k, v in status_counts.items()])
            st.bar_chart(status_df.set_index("Status")["Count"])
            st.dataframe(status_df, use_container_width=True, hide_index=True)
        else:
            st.info("No execution status data found.")

    with st.expander("Raw Execution State"):
        st.json(execution_state)


elif page == "Governance":
    st.title("Governance")

    violations = governance_report.get("violations", [])
    alerts = governance_state.get("alerts", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Governance Status", governance_report.get("governance_status", governance_status))
    c2.metric("Score", governance_report.get("governance_score", "—"))
    c3.metric("Violations", len(violations))
    c4.metric("Certification", audit_report.get("certification_status", "UNKNOWN"))

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Governance Violations")
        if violations:
            st.dataframe(pd.DataFrame(violations), use_container_width=True, hide_index=True)
        else:
            st.success("No governance violations.")

    with right:
        st.subheader("Governance Alerts")
        if alerts:
            st.warning(", ".join(alerts))
        else:
            st.success("No active alerts.")

    with st.expander("Governance Report JSON"):
        st.json(governance_report)

    with st.expander("Institutional Audit JSON"):
        st.json(audit_report)

elif page == "Institutional Readiness":
    st.title("Institutional Readiness")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Overall Status", institutional_readiness.get("overall_status", "UNKNOWN"))
    c2.metric("Score", institutional_readiness.get("platform_score", "NA"))
    c3.metric("Research Ready", str(institutional_readiness.get("research_ready", "NA")))
    c4.metric("Production Ready", str(institutional_readiness.get("production_ready", "NA")))

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("Runtime", institutional_readiness.get("runtime_integrity_status", "UNKNOWN"))
    c6.metric("Gate", institutional_readiness.get("coherence_gate_status", "UNKNOWN"))
    c7.metric("Governance", institutional_readiness.get("governance_status", "UNKNOWN"))
    c8.metric("Execution Release", str(institutional_readiness.get("execution_release_allowed", "NA")))

    st.markdown("---")

    if institutional_readiness.get("research_ready") is True:
        st.success("AURUM is research-ready as an institutional real-time market laboratory.")

    if institutional_readiness.get("production_ready") is False:
        st.warning("AURUM is not production-released. Execution release remains blocked by controls.")

    st.subheader("Remaining Issues")
    st.json(institutional_readiness.get("remaining_issues", {}))

    st.subheader("Current Runtime State")
    st.json(institutional_readiness.get("current_runtime_summary", {}))

    show_json_block("Full Readiness Report", institutional_readiness)

elif page == "Runtime Integrity":
    st.title("Runtime Integrity and Coherence Gate")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Integrity Status", runtime_integrity.get("readiness_status", "UNKNOWN"))
    c2.metric("Critical Failures", runtime_integrity.get("critical_failures", "NA"))
    c3.metric("High Failures", runtime_integrity.get("high_failures", "NA"))
    c4.metric("Findings", runtime_integrity.get("finding_count", "NA"))

    g1, g2, g3, g4 = st.columns(4)

    g1.metric("Gate Status", coherence_gate.get("gate_status", "UNKNOWN"))
    g2.metric("Hard Blocks", coherence_gate.get("hard_block_count", "NA"))
    g3.metric("Soft Blocks", coherence_gate.get("soft_block_count", "NA"))
    g4.metric("Allow Execution", str(coherence_gate.get("allow_execution_release", "NA")))

    st.markdown("---")

    findings = runtime_integrity.get("findings", [])

    if findings:
        findings_df = pd.DataFrame(findings)
        st.subheader("Audit Findings")
        st.dataframe(findings_df, use_container_width=True, hide_index=True)
    else:
        st.info("No runtime integrity findings found.")

    st.subheader("Coherence Gate Blocks")

    hard_blocks = coherence_gate.get("hard_blocks", [])
    soft_blocks = coherence_gate.get("soft_blocks", [])

    if hard_blocks:
        st.error("Hard blocks are active.")
        st.dataframe(pd.DataFrame(hard_blocks), use_container_width=True, hide_index=True)
    else:
        st.success("No hard blocks.")

    if soft_blocks:
        st.warning("Soft blocks are active.")
        st.dataframe(pd.DataFrame(soft_blocks), use_container_width=True, hide_index=True)
    else:
        st.success("No soft blocks.")

    show_json_block("Latest Runtime State", latest_runtime_state)
    show_json_block("Decision Cycle Report", decision_cycle_report)

elif page == "Memory":
    st.title("Memory")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Cycles", memory_summary.get("total_cycles", 0))
    c2.metric("Approved", memory_summary.get("approved", 0))
    c3.metric("Escalated", memory_summary.get("escalated", 0))
    c4.metric("Rejected", memory_summary.get("rejected", 0))

    st.markdown("---")

    mem_df = pd.DataFrame(
        [
            {"Status": "Approved", "Count": memory_summary.get("approved", 0)},
            {"Status": "Escalated", "Count": memory_summary.get("escalated", 0)},
            {"Status": "Rejected", "Count": memory_summary.get("rejected", 0)},
        ]
    )
    st.bar_chart(mem_df.set_index("Status")["Count"])

    if memory_log:
        st.subheader("Latest Memory Records")
        st.dataframe(pd.DataFrame(memory_log[-20:]), use_container_width=True, hide_index=True)


elif page == "AI CIO":
    st.title("AI CIO")

    if cio_brief:
        st.info(cio_brief.get("market_view", ""))
        st.warning(cio_brief.get("risk_view", ""))
        st.success(cio_brief.get("recommended_action", ""))

        st.markdown("---")

        st.subheader("Market View")
        st.info(cio_brief.get("market_view", ""))

        st.subheader("Risk View")
        st.warning(cio_brief.get("risk_view", ""))

        st.subheader("Portfolio View")
        st.write(cio_brief.get("portfolio_view", ""))

        st.subheader("Governance View")
        st.write(cio_brief.get("governance_view", ""))

        st.subheader("Recommended Action")
        st.success(cio_brief.get("recommended_action", ""))
    else:
        st.warning("No CIO brief found.")


elif page == "Control Tower":
    st.title("AURUM Institutional Control Tower")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Operating Status", operating_cycle.get("overall_status", "UNKNOWN"))
    c2.metric("Schedule", rebalance_schedule.get("schedule_type", "UNKNOWN"))
    c3.metric("Approval", approval_status)
    c4.metric("Governance", governance_status)

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Exposure Dashboard")
        if not exposure_df.empty:
            st.bar_chart(exposure_df.set_index("Group")["Weight"])
            st.dataframe(exposure_df, use_container_width=True, hide_index=True)
        else:
            st.info("No exposure data found.")

        st.subheader("Live Performance")

        p1, p2, p3, p4 = st.columns(4)

        p1.metric(
            "NAV Proxy",
            num(performance_snapshot.get("nav_proxy", 1.0), 4),
        )

        p2.metric(
            "Daily PnL",
            pct(performance_snapshot.get("daily_pnl_proxy", 0)),
        )

        p3.metric(
            "MTD PnL",
            pct(performance_snapshot.get("mtd_pnl_proxy", 0)),
        )

        p4.metric(
            "YTD PnL",
            pct(performance_snapshot.get("ytd_pnl_proxy", 0)),
        )

        p5, p6, p7, p8 = st.columns(4)

        p5.metric(
            "Cash",
            pct(performance_snapshot.get("cash_weight", 0)),
        )

        p6.metric(
            "Gross Exposure",
            pct(performance_snapshot.get("gross_exposure", 0)),
        )

        p7.metric(
            "Peak NAV",
            num(performance_summary.get("peak_nav_proxy", 1.0), 4),
        )

        p8.metric(
            "Drawdown From Peak",
            pct(performance_summary.get("drawdown_from_peak", 0)),
        )

        if performance_history:
            hist_df = pd.DataFrame(performance_history)

        if "timestamp" in hist_df.columns and "nav_proxy" in hist_df.columns:
            st.subheader("NAV History")
            nav_df = hist_df[["timestamp", "nav_proxy"]].copy()
            nav_df["nav_proxy"] = nav_df["nav_proxy"].astype(float)
            st.line_chart(nav_df.set_index("timestamp")["nav_proxy"])
    
    with right:
        st.subheader("Trigger Timeline")
        triggers = event_triggers.get("triggers", [])
        if triggers:
            trig_df = pd.DataFrame(triggers)
            st.dataframe(
                trig_df[["timestamp", "trigger_type", "severity", "action", "reason"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No active triggers.")

        st.subheader("Autonomous Decision Log")
        decision_rows = [
            {
                "Stage": "Trigger",
                "Status": event_triggers.get("action_required", False),
                "Detail": f"{event_triggers.get('trigger_count', 0)} trigger(s)",
            },
            {
                "Stage": "Schedule",
                "Status": rebalance_schedule.get("schedule_type", "UNKNOWN"),
                "Detail": rebalance_schedule.get("reason", ""),
            },
            {
                "Stage": "Approval",
                "Status": approval.get("status", "UNKNOWN"),
                "Detail": approval.get("reason", ""),
            },
            {
                "Stage": "CIO",
                "Status": "GENERATED" if cio_brief else "MISSING",
                "Detail": cio_brief.get("recommended_action", ""),
            },
        ]
        st.dataframe(pd.DataFrame(decision_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Audit Timeline")
    if audit_records:
        audit_df = pd.DataFrame(audit_records[-30:])
        display_cols = [
            "timestamp",
            "cycle_id",
            "source_stream",
            "entity_id",
            "summary",
            "status",
            "governance_status",
        ]
        display_cols = [c for c in display_cols if c in audit_df.columns]
        st.dataframe(audit_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No current-cycle audit records found.")


elif page == "System Health":
    st.title("System Health")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Platform Status",
        event_stream_summary.get("health_status", "UNKNOWN"),
    )

    c2.metric(
        "Active Streams",
        event_stream_summary.get("active_streams", 0),
    )

    c3.metric(
        "Total Events",
        event_stream_summary.get("total_events", 0),
    )

    c4.metric(
        "Operating Cycle",
        operating_cycle.get("overall_status", "UNKNOWN"),
    )

    st.markdown("---")

    st.subheader("Stream Activity")

    streams = event_stream_snapshot.get("streams", [])

    if streams:
        stream_df = pd.DataFrame(streams)

        display_cols = [
            "stream",
            "status",
            "length",
            "latest_id",
            "latest_event_type",
        ]

        display_cols = [
            col for col in display_cols
            if col in stream_df.columns
        ]

        st.dataframe(
            stream_df[display_cols].sort_values(
                "length",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Stream Event Counts")

        count_df = stream_df[
            ["stream", "length"]
        ].copy()

        count_df["length"] = (
            count_df["length"]
            .astype(float)
        )

        st.bar_chart(
            count_df.set_index("stream")["length"]
        )

    else:
        st.warning("No stream monitoring data found.")

    st.markdown("---")

    st.subheader("Critical Stream Status")

    inactive_critical = event_stream_summary.get(
        "inactive_critical_streams",
        [],
    )

    if inactive_critical:
        st.error(
            "Inactive critical streams: "
            + ", ".join(inactive_critical)
        )
    else:
        st.success(
            "All critical streams are active."
        )

    st.markdown("---")

    st.subheader("Latest Event Feed")

    if streams:
        feed_rows = []

        for stream in streams:
            latest_event = stream.get(
                "latest_event",
                {},
            )

            feed_rows.append(
                {
                    "Stream": stream.get(
                        "stream",
                        "unknown",
                    ),
                    "Status": stream.get(
                        "status",
                        "UNKNOWN",
                    ),
                    "Event Type": stream.get(
                        "latest_event_type",
                        "unknown",
                    ),
                    "Latest ID": stream.get(
                        "latest_id",
                        "—",
                    ),
                    "Payload Preview": str(
                        latest_event
                    )[:250],
                }
            )

        feed_df = pd.DataFrame(feed_rows)

        st.dataframe(
            feed_df,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader("Autonomous Stack")

    health = {
        "orchestrator_status": operating_cycle.get(
            "orchestrator_status",
            "UNKNOWN",
        ),
        "orchestrator_success_rate": operating_cycle.get(
            "orchestrator_success_rate",
            0,
        ),
        "trigger_count": operating_cycle.get(
            "trigger_count",
            0,
        ),
        "schedule_type": operating_cycle.get(
            "schedule_type",
            "UNKNOWN",
        ),
        "approval_status": operating_cycle.get(
            "approval_status",
            "UNKNOWN",
        ),
        "cio_brief_generated": operating_cycle.get(
            "cio_brief_generated",
            False,
        ),
    }

    st.json(health)



elif page == "Daily CIO Brief":
    st.title("Daily CIO Brief")

    cio_thesis = load_json(
        ROOT / "cio" / "cio_market_thesis.json",
        default={},
    )

    cio_directive = load_json(
        ROOT / "cio" / "cio_portfolio_directive.json",
        default={},
    )

    bridge = load_json(
        ROOT / "portfolio_os" / "research_firm_portfolio_os_bridge.json",
        default={},
    )

    research_firm = load_json(
        ROOT / "research_firm" / "ai_research_firm_mode.json",
        default={},
    )

    summary = research_firm.get("executive_summary", {})

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Market View",
        cio_thesis.get("market_view", "UNKNOWN"),
    )

    c2.metric(
        "Primary Risk",
        cio_thesis.get("primary_risk", bridge.get("primary_risk", "UNKNOWN")),
    )

    c3.metric(
        "Risk Impact",
        pct(cio_thesis.get("primary_risk_impact", bridge.get("primary_risk_impact", 0))),
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "CIO Action",
        cio_directive.get("recommended_action", bridge.get("cio_recommended_action", "UNKNOWN")),
    )

    c5.metric(
        "Execution",
        cio_directive.get("execution_permission", bridge.get("cio_execution_permission", "UNKNOWN")),
    )

    c6.metric(
        "Confidence",
        num(cio_directive.get("confidence", bridge.get("cio_confidence", 0)), 2),
    )

    st.markdown("---")

    st.subheader("Executive Thesis")

    thesis_text = cio_thesis.get(
        "investment_thesis",
        "No CIO thesis found.",
    )

    st.info(thesis_text)

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Portfolio Guidance")
        st.write("Risk Posture")
        st.success(cio_directive.get("risk_posture", "UNKNOWN"))

        st.write("Portfolio OS Guidance")
        st.warning(
            bridge.get(
                "portfolio_os_execution_guidance",
                "No Portfolio OS execution guidance found.",
            )
        )

        st.write("Portfolio OS Message")
        st.info(
            bridge.get(
                "portfolio_os_message",
                "No Portfolio OS bridge message found.",
            )
        )

    with right:
        st.subheader("Research Intelligence")
        st.write("Top Alpha")
        st.success(bridge.get("top_alpha", summary.get("best_alpha", "UNKNOWN")))

        st.write("Top Research Entity")
        st.success(
            bridge.get(
                "top_research_entity",
                summary.get("top_ranked_research_entity", "UNKNOWN"),
            )
        )

        st.write("Worst Scenario")
        st.error(
            bridge.get(
                "primary_risk",
                summary.get("worst_portfolio_scenario", "UNKNOWN"),
            )
        )

    st.markdown("---")

    st.subheader("CIO Brief Text")

    brief_path = ROOT / "cio" / "cio_brief.txt"

    if brief_path.exists():
        st.text(brief_path.read_text(encoding="utf-8"))
    else:
        st.info("CIO brief not found.")

    show_json_block("CIO Market Thesis", cio_thesis)
    show_json_block("CIO Portfolio Directive", cio_directive)
    show_json_block("Research Firm Bridge", bridge)

elif page == "AI Research Firm":
    st.title("AI Research Firm Mode")

    research_firm = load_json(
        ROOT / "research_firm" / "ai_research_firm_mode.json",
        default={},
    )

    bridge = load_json(
        ROOT / "portfolio_os" / "research_firm_portfolio_os_bridge.json",
        default={},
    )

    cio_thesis = load_json(
        ROOT / "cio" / "cio_market_thesis.json",
        default={},
    )

    cio_directive = load_json(
        ROOT / "cio" / "cio_portfolio_directive.json",
        default={},
    )

    summary = research_firm.get("executive_summary", {})

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Research Firm Status",
        research_firm.get("status", "UNKNOWN"),
    )

    c2.metric(
        "CIO Risk Posture",
        bridge.get("cio_risk_posture", cio_directive.get("risk_posture", "UNKNOWN")),
    )

    c3.metric(
        "CIO Action",
        bridge.get("cio_recommended_action", cio_directive.get("recommended_action", "UNKNOWN")),
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Best Alpha",
        bridge.get("top_alpha", summary.get("best_alpha", "UNKNOWN")),
    )

    c5.metric(
        "Worst Scenario",
        bridge.get("primary_risk", summary.get("worst_portfolio_scenario", "UNKNOWN")),
    )

    c6.metric(
        "Top Research Entity",
        bridge.get("top_research_entity", summary.get("top_ranked_research_entity", "UNKNOWN")),
    )

    st.markdown("---")

    st.subheader("CIO Brief")

    brief_path = ROOT / "cio" / "cio_brief.txt"

    if brief_path.exists():
        st.text(brief_path.read_text(encoding="utf-8"))
    else:
        st.info("CIO brief not found.")

    st.markdown("---")

    st.subheader("Portfolio OS Bridge Message")

    st.info(
        bridge.get(
            "portfolio_os_message",
            "No Research Firm to Portfolio OS bridge message found.",
        )
    )

    st.markdown("---")

    st.subheader("Research Firm Stage Trace")

    stages = research_firm.get("stages", [])

    if stages:
        rows = []

        for stage in stages:
            rows.append(
                {
                    "stage": stage.get("stage"),
                    "status": stage.get("status"),
                    "timestamp": stage.get("timestamp"),
                    "output_summary": stage.get("output_summary"),
                }
            )

        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No Research Firm stage trace found.")

    show_json_block("AI Research Firm State", research_firm)
    show_json_block("Research Firm → Portfolio OS Bridge", bridge)
    show_json_block("CIO Market Thesis", cio_thesis)
    show_json_block("CIO Portfolio Directive", cio_directive)

elif page == "Phase 4 Closeout":
    st.title("Phase 4 Closeout")

    c1, c2, c3 = st.columns(3)

    c1.metric("Completion", phase4_final_report.get("completion_status", "UNKNOWN"))
    c2.metric("Production", phase4_final_report.get("production_status", "UNKNOWN"))
    c3.metric(
        "Readiness",
        phase4_final_report.get("readiness", {}).get("overall_status", "UNKNOWN"),
    )

    st.markdown("---")

    st.subheader("Completed Capabilities")
    completed = phase4_final_report.get("completed_capabilities", [])

    if completed:
        for item in completed:
            st.success(item)
    else:
        st.info("No completed capabilities listed.")

    st.subheader("Remaining Before Production")
    remaining = phase4_final_report.get("remaining_before_production", [])

    if remaining:
        for item in remaining:
            st.warning(item)
    else:
        st.success("No remaining production gaps listed.")

    st.subheader("Phase 5 Recommendation")
    st.info(phase4_final_report.get("phase5_recommendation", ""))

    show_json_block("Raw Final Phase 4 Report", phase4_final_report)

elif page == "Portfolio OS":
    st.title("Portfolio Operating System")

    portfolio_os = load_json(
        ROOT / "portfolio_os" / "portfolio_operating_system.json",
        default={},
    )

    directive = load_json(
        ROOT / "portfolio_os" / "portfolio_directive.json",
        default={},
    )

    daily_cycle = load_json(
        ROOT / "portfolio_os" / "daily_portfolio_cycle.json",
        default={},
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Status",
        portfolio_os.get("status", portfolio_os.get("cycle_status", "UNKNOWN")),
    )

    c2.metric(
        "Execution",
        directive.get("execution_permission", "UNKNOWN"),
    )

    c3.metric(
        "Confidence",
        num(directive.get("confidence", 0), 2),
    )

    show_json_block("Portfolio Operating System", portfolio_os)
    show_json_block("Portfolio Directive", directive)
    show_json_block("Daily Portfolio Cycle", daily_cycle)

    show_artifact_browser(
        "All Portfolio OS Artifacts",
        ["portfolio_os", "portfolio_operating_system", "portfolio_directive", "daily_portfolio"],
    )


elif page == "Database":
    st.title("Database Layer")

    st.subheader("Core Institutional Tables")
    show_database_counts()

    st.markdown("---")

    st.subheader("Latest Market Ticks")

    try:
        from src.database.postgres_manager import PostgresManager

        db = PostgresManager()
        rows = db.fetch_all(
            """
            SELECT COALESCE(timestamp, time) AS timestamp, ticker, price, volume, source
            FROM market_ticks
            ORDER BY COALESCE(timestamp, time) DESC
            LIMIT 50;
            """
        )
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    except Exception as exc:
        st.warning(f"Could not load market ticks: {exc}")


elif page == "Reliability":
    st.title("Reliability Layer")

    readiness = load_json(
        ROOT / "reliability" / "institutional_readiness_score.json",
        default={},
    )

    service = load_json(
        ROOT / "reliability" / "service_health_report.json",
        default={},
    )

    audit = load_json(
        ROOT / "reliability" / "runtime_audit_report.json",
        default={},
    )

    alerts = load_json(
        ROOT / "reliability" / "alerts_report.json",
        default={},
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Readiness Score",
        readiness.get("institutional_readiness_score", "N/A"),
    )

    c2.metric(
        "Reliability Status",
        readiness.get("status", "UNKNOWN"),
    )

    c3.metric(
        "Alerts",
        alerts.get("alert_count", 0),
    )

    show_json_block("Institutional Readiness Score", readiness)
    show_json_block("Service Health", service)
    show_json_block("Runtime Audit", audit)
    show_json_block("Alerts", alerts)

    show_artifact_browser(
        "All Reliability Artifacts",
        ["reliability", "health", "readiness", "audit", "alert"],
    )