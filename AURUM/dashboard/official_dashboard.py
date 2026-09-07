"""
AURUM V1 OFFICIAL DASHBOARD

Public dashboard entrypoint for AURUM v1.

Usage
-----
streamlit run dashboard/official_dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from src.institutional.mars_cvar_product import build_reference_product_evidence


st.set_page_config(
    page_title="AURUM v1",
    page_icon="🏛️",
    layout="wide",
)


DEMO_DIR = Path("reports/aurum_v1_demo")
PRESENTATION_DIR = Path("reports/aurum_v1_presentation_package")

DEMO_SUMMARY = DEMO_DIR / "demo_run_summary.json"
VALIDATION_REPORT = DEMO_DIR / "aurum_v1_validation_report.json"
CONSOLE_REPORT = DEMO_DIR / "demo_console_report.txt"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_text(path: Path) -> str:
    if not path.exists():
        return "File not found."
    return path.read_text(encoding="utf-8", errors="ignore")


def status_badge(status: str) -> str:
    if str(status).lower() in {"success", "pass", "aurum_v1_complete"}:
        return "✅"
    if str(status).lower() in {"failed", "fail", "aurum_v1_incomplete"}:
        return "❌"
    return "⚠️"


def main() -> None:
    st.title("AURUM v1 — Institutional Portfolio Intelligence Platform")
    st.caption("Official demo dashboard: quant core, live intelligence, portfolio OS, and AI research layer.")

    demo = load_json(DEMO_SUMMARY)
    validation = load_json(VALIDATION_REPORT)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    steps = demo.get("steps", [])
    passed_steps = sum(1 for s in steps if s.get("status") == "success")
    total_steps = len(steps)

    validation_status = validation.get("status", "UNKNOWN")
    checks_passed = validation.get("checks_passed", 0)
    checks_total = validation.get("checks_total", 0)

    with col1:
        st.metric("Demo Steps", f"{passed_steps}/{total_steps}")

    with col2:
        st.metric("Validation Checks", f"{checks_passed}/{checks_total}")

    with col3:
        st.metric("Platform Status", validation_status)

    with col4:
        st.metric("Last Demo Run", demo.get("timestamp", "N/A")[:19])

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Executive Summary",
            "Demo Pipeline",
            "Validation",
            "Artifacts",
            "Console Report",
            "MARS-CVaR",
        ]
    )

    with tab1:
        st.subheader("AURUM v1 Status")

        if validation_status == "AURUM_V1_COMPLETE":
            st.success("AURUM v1 is complete and demo-ready.")
        else:
            st.warning("AURUM v1 validation report is missing or incomplete.")

        st.markdown(
            """
            **AURUM v1** is a portfolio intelligence platform combining:

            - live market refresh
            - HMM-based regime intelligence
            - institutional anomaly detection
            - CVaR linear-programming optimization
            - portfolio operating system
            - AI research firm mode
            - presentation-ready reporting

            The purpose of this dashboard is not to show every internal module.
            It is the official public-facing control panel for the v1 demo.
            """
        )

    with tab2:
        st.subheader("Single-Command Demo Pipeline")

        if not steps:
            st.warning("No demo summary found. Run: `python -m scripts.run_aurum_v1_demo`")
        else:
            df = pd.DataFrame(
                [
                    {
                        "Step": s.get("step"),
                        "Status": f"{status_badge(s.get('status'))} {s.get('status')}",
                    }
                    for s in steps
                ]
            )

            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("Raw demo summary JSON"):
                st.json(demo)

    with tab3:
        st.subheader("AURUM v1 Validation")

        if not validation:
            st.warning("No validation report found. Run: `python -m scripts.validate_aurum_v1_complete`")
        else:
            if validation_status == "AURUM_V1_COMPLETE":
                st.success("Validation passed.")
            else:
                st.error("Validation incomplete.")

            st.json(validation)

    with tab4:
        st.subheader("Presentation Package")

        files = [
            "README_DRAFT.md",
            "ARCHITECTURE_DIAGRAM.md",
            "AURUM_WHITEPAPER_DRAFT.md",
            "RESUME_SUMMARY.md",
            "PACKAGE_INDEX.md",
        ]

        artifact_rows = []

        for file in files:
            path = PRESENTATION_DIR / file
            artifact_rows.append(
                {
                    "Artifact": file,
                    "Exists": "✅" if path.exists() else "❌",
                    "Path": str(path),
                }
            )

        st.dataframe(
            pd.DataFrame(artifact_rows),
            use_container_width=True,
            hide_index=True,
        )

        selected = st.selectbox("Preview artifact", files)
        selected_path = PRESENTATION_DIR / selected

        st.markdown("### Preview")
        st.code(load_text(selected_path)[:6000], language="markdown")

    with tab5:
        st.subheader("Demo Console Report")
        st.code(load_text(CONSOLE_REPORT), language="text")

    with tab6:
        st.subheader("MARS-CVaR Regime Allocation Council")
        st.caption("Institutional research workflow: regime evidence, portfolio construction, CVaR tail analysis, baselines, and human-gated promotion.")
        c1, c2, c3, c4 = st.columns(4)
        stress = c1.slider("Next-regime stress probability", 0.0, 1.0, 0.50, 0.05)
        turnover_penalty = c2.slider("Turnover penalty", 0.0, 0.20, 0.05, 0.01)
        risk_aversion = c3.slider("CVaR risk weight lambda", 0.0, 3.0, 0.35, 0.05)
        alpha = c4.slider("CVaR confidence alpha", 0.80, 0.99, 0.95, 0.01)
        evidence = build_reference_product_evidence(
            Path("."),
            stress_probability=float(stress),
            turnover_penalty=float(turnover_penalty),
            risk_aversion=float(risk_aversion),
            alpha=float(alpha),
        )
        d = evidence["decision"]
        g1, g2, g3 = st.columns([1, 1, 2])
        (g1.success if d["authorized"] else g1.error)(f'Optimization authorization: {d["risk_gate"]}')
        g2.warning(f'Research promotion: {evidence["governance"]["research_promotion"]}')
        g3.code(d["decision_id"])
        surface_tabs = st.tabs(["Overview", "Market / Regime", "Portfolio", "Risk Lab", "Research", "Stress / Frontier", "Evidence"])
        with surface_tabs[0]:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Expected return", f'{100 * d["expected_return"]:.3f}%')
            m2.metric("CVaR signed loss", f'{100 * d["cvar_loss"]:.3f}%')
            m3.metric("Downside magnitude", f'{100 * max(0, d["cvar_loss"]):.3f}%')
            m4.metric("L1 turnover", f'{100 * d["turnover"]:.2f}%')
            st.markdown("### Current versus target allocation")
            st.dataframe(pd.DataFrame(evidence["portfolio_workspace"]["asset_contributions"]), use_container_width=True, hide_index=True)
            st.caption(evidence["claim_boundary"])
        with surface_tabs[1]:
            regime = evidence["market_regime"]
            st.write({"current_regime": regime["current_regime"], "transition_matrix_valid": regime["transition_matrix_valid"], "probability_entropy": regime["probability_entropy_normalized"]})
            st.markdown("### Transition matrix")
            st.dataframe(pd.DataFrame(regime["transition_matrix"]).T, use_container_width=True)
            st.markdown("### Next-regime probability vector")
            st.dataframe(pd.DataFrame([regime["decision_input_next_regime_probabilities"]]), use_container_width=True, hide_index=True)
            st.caption(regime["probability_vector_source"])
        with surface_tabs[2]:
            st.markdown("### Portfolio allocation")
            st.dataframe(pd.DataFrame([{"asset": a, "current_weight": evidence["portfolio_workspace"]["current_weights"][a], "target_weight": d["target_weights"][a], "change": d["weight_changes"][a]} for a in d["assets"]]), use_container_width=True, hide_index=True)
            st.markdown("### Constraints / evidence gates")
            st.dataframe(pd.DataFrame(evidence["constraints"]), use_container_width=True, hide_index=True)
            st.markdown("### Transaction / turnover")
            st.dataframe(pd.DataFrame(evidence["transaction_analysis"]["trades"]), use_container_width=True, hide_index=True)
        with surface_tabs[3]:
            risk = evidence["risk_lab"]
            st.info(risk["cvar_convention"])
            st.metric("Dominant tail scenarios", ", ".join(risk["dominant_tail_scenarios"]))
            st.dataframe(pd.DataFrame(risk["scenarios"]), use_container_width=True, hide_index=True)
        with surface_tabs[4]:
            st.markdown("### Baseline lab")
            st.dataframe(pd.DataFrame(evidence["baselines"]), use_container_width=True, hide_index=True)
            st.markdown("### Walk-forward research validation")
            st.json(evidence["walk_forward_research"])
            st.warning(f'Research promotion: {evidence["governance"]["research_promotion"]}; this is not an application error.')
        with surface_tabs[5]:
            st.markdown("### Synthetic stress sensitivity")
            st.dataframe(pd.DataFrame(evidence["sensitivity"]["stress_probability"]), use_container_width=True, hide_index=True)
            st.markdown("### Risk-return / turnover frontier")
            st.dataframe(pd.DataFrame(evidence["frontier"]), use_container_width=True, hide_index=True)
            st.markdown("### Turnover penalty sensitivity")
            st.dataframe(pd.DataFrame(evidence["sensitivity"]["turnover_penalty"]), use_container_width=True, hide_index=True)
        with surface_tabs[6]:
            st.markdown("### Data provenance")
            st.dataframe(pd.DataFrame([{"field": k, "value": v} for k, v in evidence["data_provenance"].items()]), use_container_width=True, hide_index=True)
            st.markdown("### Auditable evidence payload")
            st.json(evidence)

    st.divider()

    st.caption(
        f"Generated dashboard view at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    main()
