# src/dashboard/execution_dashboard.py

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import redis
import streamlit as st


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

PORTFOLIO_STATE_PATH = Path("results/portfolio/institutional_portfolio_state.json")

EXECUTION_ORDERS_PATH = Path("results/execution/execution_orders.json")
TRADE_TICKETS_PATH = Path("results/execution/trade_tickets.json")
EXECUTION_REPORTS_PATH = Path("results/execution/execution_reports.json")
GOVERNANCE_REPORT_PATH = Path("results/governance/execution_governance_report.json")
GOVERNANCE_ALERTS_PATH = Path("results/governance/governance_alerts.json")
AUDIT_LOG_PATH = Path("results/governance/execution_audit_log.jsonl")
INSTITUTIONAL_AUDIT_REPORT_PATH = Path("results/governance/institutional_audit_report.json")
CURRENT_CYCLE_AUDIT_LOG_PATH = Path("results/governance/current_cycle_audit_log.jsonl")


OPTIMIZATION_CANDIDATES = [
    Path("results/optimization/realtime_optimized_portfolio.json"),
    Path("results/optimization/regime_allocation_policy.json"),
    Path("results/optimization/final_optimizer_decision_report.json"),
    Path("results/optimization/optimizer_report.json"),
]

STREAMS = [
    "market_signals",
    "risk_events",
    "portfolio_decisions",
    "optimizer_events",
    "execution_orders",
    "trade_tickets",
    "execution_reports",
    "live_positions",
    "institutional_portfolio_state",
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows

def get_redis_client():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_stream_lengths() -> Dict[str, int]:
    lengths = {}
    try:
        r = get_redis_client()
        r.ping()
        for stream in STREAMS:
            lengths[stream] = r.xlen(stream)
    except Exception:
        for stream in STREAMS:
            lengths[stream] = 0
    return lengths


def as_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def fmt_pct(value: Any) -> str:
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "—"


def load_target_weights(state: Dict[str, Any]) -> Dict[str, float]:
    def clean_weights(raw: Any) -> Dict[str, float]:
        if not isinstance(raw, dict):
            return {}

        cleaned = {}
        for k, v in raw.items():
            if not isinstance(k, str):
                continue
            try:
                cleaned["CASH" if k.lower() == "cash" else k] = float(v)
            except Exception:
                continue
        return cleaned

    preferred_keys = [
        "recommended_weights",
        "target_weights",
        "final_recommended_weights",
        "constrained_weights",
        "volatility_targeted_weights",
        "weights",
    ]

    opt_state = state.get("optimization_state", {})
    for key in preferred_keys:
        cleaned = clean_weights(opt_state.get(key, {}))
        if cleaned:
            return cleaned

    for path in OPTIMIZATION_CANDIDATES:
        data = load_json(path, {})
        if not isinstance(data, dict):
            continue

        for key in preferred_keys:
            cleaned = clean_weights(data.get(key, {}))
            if cleaned:
                return cleaned

    return {}


def build_current_vs_target_df(
    current_positions: Dict[str, Any],
    target_weights: Dict[str, float],
) -> pd.DataFrame:
    normalized_current = {
        ("CASH" if k.lower() == "cash" else k): float(v)
        for k, v in current_positions.items()
    }

    normalized_target = {
        ("CASH" if k.lower() == "cash" else k): float(v)
        for k, v in target_weights.items()
    }

    tickers = sorted(set(normalized_current) | set(normalized_target))

    rows = []
    for ticker in tickers:
        current = float(normalized_current.get(ticker, 0.0))
        target = float(normalized_target.get(ticker, 0.0))
        drift = current - target

        rows.append(
            {
                "Ticker": ticker,
                "Current Weight": current,
                "Target Weight": target,
                "Drift": drift,
                "Current %": f"{current:.2%}",
                "Target %": f"{target:.2%}",
                "Drift %": f"{drift:+.2%}",
            }
        )

    return pd.DataFrame(rows)


def build_execution_quality(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not reports:
        return {
            "requested": 0.0,
            "executed": 0.0,
            "unfilled": 0.0,
            "fill_rate": 0.0,
            "avg_cost_bps": 0.0,
            "avg_delay_ms": 0.0,
            "partial_fills": 0,
            "rejections": 0,
        }

    requested = sum(float(r.get("requested_pct", 0.0)) for r in reports)
    executed = sum(float(r.get("executed_pct", 0.0)) for r in reports)
    unfilled = sum(float(r.get("unfilled_pct", 0.0)) for r in reports)

    fill_rate = executed / requested if requested > 0 else 0.0
    avg_cost_bps = sum(float(r.get("total_cost_bps", 0.0)) for r in reports) / len(reports)
    avg_delay_ms = sum(float(r.get("execution_delay_ms", 0.0)) for r in reports) / len(reports)

    partial_fills = sum(1 for r in reports if r.get("status") == "PARTIALLY_FILLED")
    rejections = sum(1 for r in reports if r.get("status") == "REJECTED")

    return {
        "requested": requested,
        "executed": executed,
        "unfilled": unfilled,
        "fill_rate": fill_rate,
        "avg_cost_bps": avg_cost_bps,
        "avg_delay_ms": avg_delay_ms,
        "partial_fills": partial_fills,
        "rejections": rejections,
    }


def build_governance_controls(
    state: Dict[str, Any],
    execution_quality: Dict[str, Any],
) -> pd.DataFrame:
    position_state = state.get("position_state", {})
    market_state = state.get("market_state", {})
    risk_state = state.get("risk_state", {})

    cash_weight = float(position_state.get("cash_weight", 0.0) or 0.0)
    gross_exposure = float(position_state.get("gross_exposure", 0.0) or 0.0)
    fill_rate = float(execution_quality.get("fill_rate", 0.0) or 0.0)
    stress_score = float(market_state.get("stress_score", 0.0) or 0.0)
    risk_level = str(risk_state.get("risk_level", "unknown")).lower()

    return pd.DataFrame(
        [
            {
                "Control": "Cash Limit",
                "Rule": "cash >= -2%",
                "Observed": f"{cash_weight:.2%}",
                "Status": "PASS" if cash_weight >= -0.02 else "FAIL",
            },
            {
                "Control": "Gross Exposure Limit",
                "Rule": "gross exposure <= 110%",
                "Observed": f"{gross_exposure:.2%}",
                "Status": "PASS" if gross_exposure <= 1.10 else "FAIL",
            },
            {
                "Control": "Execution Fill Rate",
                "Rule": "fill rate >= 90%",
                "Observed": f"{fill_rate:.2%}",
                "Status": "PASS" if fill_rate >= 0.90 else "FAIL",
            },
            {
                "Control": "Market Stress",
                "Rule": "stress score < 80%",
                "Observed": f"{stress_score:.2%}",
                "Status": "PASS" if stress_score < 0.80 else "REVIEW",
            },
            {
                "Control": "Risk State",
                "Rule": "not high/critical/breach",
                "Observed": risk_level,
                "Status": "PASS"
                if risk_level not in {"high", "critical", "breach"}
                else "REVIEW",
            },
        ]
    )


def get_latest_stream_time(stream_name: str) -> str:
    try:
        r = get_redis_client()
        entries = r.xrevrange(stream_name, count=1)
        if not entries:
            return "—"
        _, fields = entries[0]
        return fields.get("timestamp", "—")
    except Exception:
        return "—"


def build_lifecycle_timeline() -> pd.DataFrame:
    event_map = [
        ("Market Signal", "market_signals"),
        ("Risk Event", "risk_events"),
        ("Portfolio Decision", "portfolio_decisions"),
        ("Optimizer Event", "optimizer_events"),
        ("Execution Orders", "execution_orders"),
        ("Trade Tickets", "trade_tickets"),
        ("Execution Reports", "execution_reports"),
        ("Live Positions", "live_positions"),
        ("Institutional State", "institutional_portfolio_state"),
    ]

    return pd.DataFrame(
        [
            {
                "Lifecycle Event": event_name,
                "Stream": stream,
                "Latest Timestamp": get_latest_stream_time(stream),
            }
            for event_name, stream in event_map
        ]
    )


def build_status_distribution(reports: List[Dict[str, Any]]) -> pd.DataFrame:
    statuses = ["FILLED", "PARTIALLY_FILLED", "REJECTED", "PENDING"]

    counts = {status: 0 for status in statuses}
    for report in reports:
        status = str(report.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1

    return pd.DataFrame(
        [{"Status": status, "Count": count} for status, count in counts.items()]
    )

def build_audit_timeline(audit_records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not audit_records:
        return pd.DataFrame()

    rows = []

    for record in audit_records:
        source_stream = record.get("source_stream", "unknown")
        summary = record.get("summary", "")
        status = record.get("status", "UNKNOWN")
        governance_status = record.get("governance_status", "UNKNOWN")

        if source_stream == "execution_orders":
            lifecycle_stage = "01 Order Generated"
        elif source_stream == "trade_tickets":
            lifecycle_stage = "02 Ticket Created"
        elif source_stream == "execution_reports":
            lifecycle_stage = "03 Execution Reported"
        elif source_stream == "live_positions":
            lifecycle_stage = "04 Position Updated"
        elif source_stream == "institutional_portfolio_state":
            lifecycle_stage = "05 Lifecycle Updated"
        elif source_stream == "governance_events":
            lifecycle_stage = "06 Governance Checked"
        elif source_stream == "governance_alerts":
            lifecycle_stage = "07 Governance Alert"
        else:
            lifecycle_stage = "99 Other"

        rows.append(
            {
                "Timestamp": record.get("timestamp", "—"),
                "Stage": lifecycle_stage,
                "Source": source_stream,
                "Entity": record.get("entity_id", "—"),
                "Summary": summary,
                "Status": status,
                "Governance": governance_status,
            }
        )

    df = pd.DataFrame(rows)

    if "Timestamp" in df.columns:
        df = df.sort_values("Timestamp", ascending=False)

    return df

def build_governance_heatmap_df(governance_controls_df: pd.DataFrame) -> pd.DataFrame:
    if governance_controls_df.empty:
        return pd.DataFrame()

    severity_score = {
        "PASS": 1.0,
        "CLEAR": 1.0,
        "WARNING": 0.6,
        "REVIEW": 0.4,
        "FAIL": 0.0,
        "BREACH": 0.0,
    }

    rows = []

    for _, row in governance_controls_df.iterrows():
        status = str(row.get("Status", "UNKNOWN")).upper()
        rows.append(
            {
                "Control": row.get("Control", "Unknown"),
                "Status": status,
                "Health Score": severity_score.get(status, 0.5),
                "Observed": row.get("Observed", "—"),
                "Rule": row.get("Rule", "—"),
            }
        )

    return pd.DataFrame(rows)

def main() -> None:
    st.set_page_config(
        page_title="AURUM Execution Dashboard",
        page_icon="📈",
        layout="wide",
    )

    st.title("AURUM Real-Time Execution & Portfolio Lifecycle Dashboard")
    st.caption("Phase 4D.6 — Institutional Execution Cockpit | Port 8504")

    state = load_json(PORTFOLIO_STATE_PATH, {})
    orders = load_json(EXECUTION_ORDERS_PATH, [])
    tickets = load_json(TRADE_TICKETS_PATH, [])
    reports = load_json(EXECUTION_REPORTS_PATH, [])
    stream_lengths = get_stream_lengths()
    governance_report = load_json(GOVERNANCE_REPORT_PATH, {})
    governance_alerts = load_json(GOVERNANCE_ALERTS_PATH, [])
    audit_records = load_jsonl(AUDIT_LOG_PATH)
    institutional_audit_report = load_json(INSTITUTIONAL_AUDIT_REPORT_PATH, {})
    current_cycle_audit_records = load_jsonl(CURRENT_CYCLE_AUDIT_LOG_PATH)

    if not state:
        st.warning("No institutional portfolio state found. Run:")
        st.code("python -m src.portfolio.portfolio_lifecycle_manager")
        return

    execution_state = state.get("execution_state", {})
    position_state = state.get("position_state", {})
    performance_state = state.get("performance_state", {})
    market_state = state.get("market_state", {})
    risk_state = state.get("risk_state", {})
    decision_state = state.get("decision_state", {})
    governance_state = state.get("governance_state", {})

    lifecycle_status = state.get("lifecycle_status", "UNKNOWN")
    governance_status = governance_state.get("governance_status", "UNKNOWN")
    alerts = governance_state.get("alerts", [])

    current_positions = position_state.get("positions", {})
    target_weights = load_target_weights(state)
    current_vs_target_df = build_current_vs_target_df(current_positions, target_weights)

    execution_quality = build_execution_quality(reports)
    governance_controls_df = build_governance_controls(state, execution_quality)
    governance_heatmap_df = build_governance_heatmap_df(governance_controls_df)
    lifecycle_timeline_df = build_lifecycle_timeline()
    status_distribution_df = build_status_distribution(reports)
    audit_timeline_df = build_audit_timeline(audit_records)

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Lifecycle Status", lifecycle_status)
    top2.metric("Governance", governance_status)
    top3.metric("Fill Ratio", fmt_pct(execution_state.get("aggregate_fill_ratio", 0.0)))
    top4.metric("Execution Cost", f"{execution_state.get('total_execution_cost_bps', 0.0)} bps")

    top5, top6, top7, top8 = st.columns(4)
    top5.metric("Gross Exposure", fmt_pct(position_state.get("gross_exposure", 0.0)))
    top6.metric("Cash Weight", fmt_pct(position_state.get("cash_weight", 0.0)))
    top7.metric("Reports", execution_state.get("report_count", 0))
    top8.metric("PnL Proxy", fmt_pct(performance_state.get("daily_pnl_proxy", 0.0)))

    if alerts:
        st.error(f"Governance Alerts: {', '.join(alerts)}")
    else:
        st.success("Governance clear. No active execution or portfolio alerts.")

    st.divider()

    st.subheader("Portfolio Command Strip")
    command_cols = st.columns(6)

    command_cols[0].metric("Portfolio ID", state.get("portfolio_id", "UNKNOWN"))
    command_cols[1].metric("Regime", market_state.get("regime", "unknown"))
    command_cols[2].metric("Decision", decision_state.get("decision", "unknown"))
    command_cols[3].metric("Risk Level", risk_state.get("risk_level", "unknown"))
    command_cols[4].metric("Target Assets", len(target_weights))
    command_cols[5].metric("Execution Status", lifecycle_status)

    st.divider()

    st.subheader("Governance & Audit Certification Strip")

    gov_cols = st.columns(6)

    gov_cols[0].metric(
        "Governance Score",
        governance_report.get("governance_score", "—"),
    )

    gov_cols[1].metric(
        "Certification",
        institutional_audit_report.get("certification_status", "UNKNOWN"),
    )

    gov_cols[2].metric(
        "Current Cycle",
        institutional_audit_report.get("audit_records_current_cycle", len(current_cycle_audit_records)),
    )

    gov_cols[3].metric(
        "Stale Records",
        institutional_audit_report.get("stale_audit_records", 0),
    )

    gov_cols[4].metric(
        "Violations",
        len(governance_report.get("violations", [])),
    )

    gov_cols[5].metric(
        "Alerts",
        len(governance_alerts),
    )

    cycle_id = institutional_audit_report.get("cycle_id", "UNKNOWN")
    optimizer_source = institutional_audit_report.get("optimizer_source", "unknown")

    st.caption(f"Cycle ID: `{cycle_id}`")
    st.caption(f"Optimizer Source: `{optimizer_source}`")

    st.divider()
    st.subheader("Portfolio Drift: Current vs Target")

    if current_vs_target_df.empty:
        st.info("No current or target portfolio weights available.")
    else:
        drift_display = current_vs_target_df[
            ["Ticker", "Current %", "Target %", "Drift %"]
        ]
        st.dataframe(drift_display, use_container_width=True, hide_index=True)

        plot_df = current_vs_target_df.melt(
            id_vars=["Ticker"],
            value_vars=["Current Weight", "Target Weight"],
            var_name="Type",
            value_name="Weight",
        )

        fig = px.bar(
            plot_df,
            x="Ticker",
            y="Weight",
            color="Type",
            barmode="group",
            title="Current vs Target Allocation",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()


    st.subheader("Execution Quality")

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Requested Volume", fmt_pct(execution_quality["requested"]))
    q2.metric("Executed Volume", fmt_pct(execution_quality["executed"]))
    q3.metric("Unfilled Volume", fmt_pct(execution_quality["unfilled"]))
    q4.metric("Avg Cost", f"{execution_quality['avg_cost_bps']:.2f} bps")

    q5, q6, q7, q8 = st.columns(4)
    q5.metric("Avg Delay", f"{execution_quality['avg_delay_ms']:.0f} ms")
    q6.metric("Partial Fills", execution_quality["partial_fills"])
    q7.metric("Rejections", execution_quality["rejections"])
    q8.metric("Quality Fill Rate", fmt_pct(execution_quality["fill_rate"]))

    st.subheader("Execution Status Distribution")
    fig_status = px.bar(
        status_distribution_df,
        x="Status",
        y="Count",
        title="Execution Status Breakdown",
    )
    st.plotly_chart(fig_status, use_container_width=True)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Market / Risk / Decision State")
        state_table = pd.DataFrame(
            [
                {"Layer": "Market Regime", "Value": market_state.get("regime", "unknown")},
                {"Layer": "Market Stress", "Value": market_state.get("stress_score", 0.0)},
                {"Layer": "Risk Level", "Value": risk_state.get("risk_level", "unknown")},
                {"Layer": "VaR 95", "Value": risk_state.get("var_95", "—")},
                {"Layer": "CVaR 95", "Value": risk_state.get("cvar_95", "—")},
                {"Layer": "Decision", "Value": decision_state.get("decision", "unknown")},
                {"Layer": "Confidence", "Value": decision_state.get("confidence", 0.0)},
            ]
        )
        st.dataframe(state_table, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Redis Stream Health")
        stream_df = pd.DataFrame(
            [
                {
                    "Stream": stream,
                    "Length": length,
                    "Status": "ACTIVE" if length > 0 else "EMPTY",
                }
                for stream, length in stream_lengths.items()
            ]
        )
        st.dataframe(stream_df, use_container_width=True, hide_index=True)

    st.divider()

    left2, right2 = st.columns(2)

    with left2:
        st.subheader("Portfolio Governance Monitor")

        if not governance_heatmap_df.empty:
            pass_count = int((governance_heatmap_df["Status"] == "PASS").sum())
            total_controls = len(governance_heatmap_df)
            health_score = governance_heatmap_df["Health Score"].mean()

            h1, h2, h3 = st.columns(3)
            h1.metric("Controls Passing", f"{pass_count}/{total_controls}")
            h2.metric("Control Health", f"{health_score:.0%}")
            h3.metric(
                "Governance Mode",
                "CLEAR" if health_score >= 0.95 else "REVIEW",
            )

            st.dataframe(
                governance_heatmap_df[
                    ["Control", "Rule", "Observed", "Status", "Health Score"]
                ],
                use_container_width=True,
                hide_index=True,
            )

            fig_gov = px.imshow(
                governance_heatmap_df[["Health Score"]].T,
                x=governance_heatmap_df["Control"],
                y=["Governance Health"],
                zmin=0,
                zmax=1,
                text_auto=True,
                title="Governance Control Heat Map",
            )

            st.plotly_chart(fig_gov, use_container_width=True)

        else:
            st.info("No governance controls available.")

    with right2:
        st.subheader("Lifecycle Timeline")
        st.dataframe(lifecycle_timeline_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Live Portfolio Positions")

    if current_positions:
        pos_df = pd.DataFrame(
            [
                {
                    "Ticker": "CASH" if ticker.lower() == "cash" else ticker,
                    "Weight": float(weight),
                    "Weight %": f"{float(weight):.2%}",
                }
                for ticker, weight in current_positions.items()
            ]
        )

        st.dataframe(pos_df[["Ticker", "Weight %"]], use_container_width=True, hide_index=True)

        fig_alloc = px.pie(
            pos_df[pos_df["Weight"] > 0],
            values="Weight",
            names="Ticker",
            hole=0.55,
            title="Current Portfolio Allocation",
        )
        fig_alloc.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_alloc, use_container_width=True)

        fig_bar = px.bar(
            pos_df,
            x="Ticker",
            y="Weight",
            title="Live Position Weights",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("No live positions available.")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Execution Orders",
            "Trade Tickets",
            "Execution Reports",
            "Audit & Governance",
            "Lifecycle State JSON",
        ]
    )
    
    with tab1:
        st.subheader("Execution Orders")
        orders_df = as_df(orders)

        if orders_df.empty:
            st.info("No execution orders found.")
        else:
            if "quantity_pct" in orders_df.columns:
                orders_df["quantity_pct_display"] = orders_df["quantity_pct"].map(
                    lambda x: f"{float(x):.2%}"
                )

            display_cols = [
                "order_id",
                "ticker",
                "action",
                "quantity_pct_display",
                "current_weight",
                "target_weight",
                "priority",
                "status",
                "reason",
            ]
            display_cols = [c for c in display_cols if c in orders_df.columns]
            st.dataframe(orders_df[display_cols], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Trade Tickets")
        tickets_df = as_df(tickets)

        if tickets_df.empty:
            st.info("No trade tickets found.")
        else:
            if "quantity_pct" in tickets_df.columns:
                tickets_df["quantity_pct_display"] = tickets_df["quantity_pct"].map(
                    lambda x: f"{float(x):.2%}"
                )

            display_cols = [
                "ticket_id",
                "order_id",
                "strategy",
                "ticker",
                "action",
                "quantity_pct_display",
                "trade_size",
                "priority",
                "status",
                "reason",
            ]
            display_cols = [c for c in display_cols if c in tickets_df.columns]
            st.dataframe(tickets_df[display_cols], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Execution Reports")
        reports_df = as_df(reports)

        if reports_df.empty:
            st.info("No execution reports found.")
        else:
            for col in ["requested_pct", "executed_pct", "unfilled_pct", "fill_ratio"]:
                if col in reports_df.columns:
                    reports_df[f"{col}_display"] = reports_df[col].map(
                        lambda x: f"{float(x):.2%}"
                    )

            display_cols = [
                "execution_id",
                "ticket_id",
                "ticker",
                "action",
                "requested_pct_display",
                "executed_pct_display",
                "unfilled_pct_display",
                "fill_ratio_display",
                "total_cost_bps",
                "execution_delay_ms",
                "status",
            ]
            display_cols = [c for c in display_cols if c in reports_df.columns]
            st.dataframe(reports_df[display_cols], use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Audit & Governance")

        g1, g2, g3, g4, g5 = st.columns(5)

        g1.metric(
            "Governance Status",
            governance_report.get("governance_status", "UNKNOWN"),
        )
        g2.metric(
            "Governance Score",
            governance_report.get("governance_score", "—"),
        )
        g3.metric(
            "Certification",
            institutional_audit_report.get("certification_status", "UNKNOWN"),
        )
        g4.metric(
            "Current Cycle Records",
            institutional_audit_report.get("audit_records_current_cycle", len(current_cycle_audit_records)),
        )
        g5.metric(
            "Stale Records",
            institutional_audit_report.get("stale_audit_records", 0),
        )   

        st.caption(
            f"Cycle ID: `{institutional_audit_report.get('cycle_id', 'UNKNOWN')}`"
        )
        st.caption(
            f"Optimizer Source: `{institutional_audit_report.get('optimizer_source', 'unknown')}`"
        )
        st.divider()

        left_gov, right_gov = st.columns(2)

        with left_gov:
            st.subheader("Governance Violations")

            violations = governance_report.get("violations", [])
            if violations:
                violations_df = pd.DataFrame(violations)
                st.dataframe(violations_df, use_container_width=True, hide_index=True)
            else:
                st.success("No governance violations.")

        with right_gov:
            st.subheader("Governance Alerts")

            if governance_alerts:
                alerts_df = pd.DataFrame(governance_alerts)
                st.dataframe(alerts_df, use_container_width=True, hide_index=True)
            else:
                st.success("No open governance alerts.")

        st.divider()
        st.divider()

        st.subheader("Current-Cycle Certified Audit Records")

        if current_cycle_audit_records:
            current_cycle_df = pd.DataFrame(current_cycle_audit_records[-30:])

            display_cols = [
                "audit_id",
                "cycle_id",
                "timestamp",
                "source_stream",
                "entity_id",
                "summary",
                "status",
                "governance_status",
                "is_current_cycle",
            ]
            display_cols = [c for c in display_cols if c in current_cycle_df.columns]

            st.dataframe(
                current_cycle_df[display_cols].sort_values("timestamp", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No current-cycle certified audit records found.")

        st.subheader("Latest Audit Records")

        if audit_records:
            audit_df = pd.DataFrame(audit_records[-20:])

            display_cols = [
                "audit_id",
                "timestamp",
                "source_stream",
                "entity_id",
                "summary",
                "status",
                "governance_status",
            ]
            display_cols = [c for c in display_cols if c in audit_df.columns]

            st.dataframe(
                audit_df[display_cols].sort_values("timestamp", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No audit records found.")

        st.divider()
    
    st.divider()

    st.subheader("Audit Timeline")

    if not audit_timeline_df.empty:
        timeline_display = audit_timeline_df[
            [
                "Timestamp",
                "Stage",
                "Source",
                "Entity",
                "Summary",
                "Status",
                "Governance",
            ]
        ].head(30)

        st.dataframe(
            timeline_display,
            use_container_width=True,
            hide_index=True,
        )

        timeline_counts = (
            audit_timeline_df.groupby("Stage")
            .size()
            .reset_index(name="Event Count")
            .sort_values("Stage")
        )

        fig_timeline = px.bar(
            timeline_counts,
            x="Stage",
            y="Event Count",
            title="Audit Events by Lifecycle Stage",
        )

        st.plotly_chart(fig_timeline, use_container_width=True)

    else:
        st.info("No audit timeline available.")

    st.subheader("Institutional Audit Report")

    if institutional_audit_report:
        report_cols = st.columns(5)

        report_cols[0].metric(
            "Orders",
            institutional_audit_report.get("orders_generated", 0),
        )
        report_cols[1].metric(
            "Tickets",
            institutional_audit_report.get("tickets_generated", 0),
        )
        report_cols[2].metric(
            "Executions",
            institutional_audit_report.get("execution_reports", 0),
        )
        report_cols[3].metric(
            "Current Cycle",
            institutional_audit_report.get("audit_records_current_cycle", 0),
        )
        report_cols[4].metric(
            "Certified",
            institutional_audit_report.get("certification_status", "UNKNOWN"),
        )

        st.json(institutional_audit_report)
    else:
        st.info("No institutional audit report found.")

    with tab5:
        st.subheader("Institutional Portfolio State")
        st.json(state)

    st.divider()

    st.caption(
        "Refresh pipeline: "
        "`python -m src.execution.execution_order_generator; "
        "python -m src.execution.trade_ticket_engine; "
        "python -m src.execution.portfolio_execution_simulator; "
        "python -m src.portfolio.position_management_engine; "
        "python -m src.portfolio.portfolio_lifecycle_manager`"
    )


if __name__ == "__main__":
    main()