from pathlib import Path


DASHBOARD = Path("src/dashboard/institutional_command_center.py")


PAGE_BLOCK = '''
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

'''


def main() -> None:
    text = DASHBOARD.read_text(encoding="utf-8")

    if '"Daily CIO Brief"' not in text:
        text = text.replace(
            '        "AI Research Firm",\n',
            '        "AI Research Firm",\n        "Daily CIO Brief",\n',
        )

    if 'elif page == "Daily CIO Brief":' not in text:
        marker = 'elif page == "AI Research Firm":'
        if marker in text:
            text = text.replace(marker, PAGE_BLOCK + marker)
        else:
            text = text.rstrip() + "\n\n" + PAGE_BLOCK

    DASHBOARD.write_text(text, encoding="utf-8")

    print("[PASS] Dashboard patched with Daily CIO Brief page")


if __name__ == "__main__":
    main()