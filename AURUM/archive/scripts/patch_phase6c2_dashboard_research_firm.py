from pathlib import Path


DASHBOARD = Path("src/dashboard/institutional_command_center.py")


PAGE_BLOCK = '''
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

'''


def main() -> None:
    text = DASHBOARD.read_text(encoding="utf-8")

    if '"AI Research Firm"' not in text:
        text = text.replace(
            '        "System Health",\n',
            '        "System Health",\n        "AI Research Firm",\n',
        )

    if 'elif page == "AI Research Firm":' not in text:
        marker = 'elif page == "Phase 4 Closeout":'
        if marker in text:
            text = text.replace(marker, PAGE_BLOCK + marker)
        else:
            text = text.rstrip() + "\n\n" + PAGE_BLOCK

    DASHBOARD.write_text(text, encoding="utf-8")

    print("[PASS] Dashboard patched with AI Research Firm page")


if __name__ == "__main__":
    main()