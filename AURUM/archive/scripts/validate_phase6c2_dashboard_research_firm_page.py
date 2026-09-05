from pathlib import Path


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6C.2 DASHBOARD RESEARCH FIRM PAGE VALIDATION")
    print("=" * 80)

    dashboard = Path("src/dashboard/institutional_command_center.py")
    check(dashboard.exists(), "official command center exists")

    text = dashboard.read_text(encoding="utf-8", errors="ignore")

    check('"AI Research Firm"' in text, "AI Research Firm sidebar item added")
    check('elif page == "AI Research Firm":' in text, "AI Research Firm page block added")
    check("ai_research_firm_mode.json" in text, "research firm state wired")
    check("research_firm_portfolio_os_bridge.json" in text, "Portfolio OS bridge wired")
    check("cio_brief.txt" in text, "CIO brief wired")
    check("Research Firm Stage Trace" in text, "stage trace section added")
    check("Portfolio OS Bridge Message" in text, "bridge message section added")

    required_artifacts = [
        Path("results/research_firm/ai_research_firm_mode.json"),
        Path("results/portfolio_os/research_firm_portfolio_os_bridge.json"),
        Path("results/cio/cio_brief.txt"),
    ]

    for artifact in required_artifacts:
        check(artifact.exists(), f"{artifact} exists")

    print("=" * 80)
    print("[PASS] PHASE 6C.2 DASHBOARD RESEARCH FIRM PAGE COMPLETE")
    print("AURUM now exposes AI Research Firm Mode in the official command center.")
    print("=" * 80)


if __name__ == "__main__":
    main()