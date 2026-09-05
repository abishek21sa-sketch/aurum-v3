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
    print("AURUM PHASE 6C.3 DAILY CIO BRIEF DASHBOARD VALIDATION")
    print("=" * 80)

    dashboard = Path("src/dashboard/institutional_command_center.py")
    check(dashboard.exists(), "official command center exists")

    text = dashboard.read_text(encoding="utf-8", errors="ignore")

    check('"Daily CIO Brief"' in text, "Daily CIO Brief sidebar item added")
    check('elif page == "Daily CIO Brief":' in text, "Daily CIO Brief page block added")
    check("Executive Thesis" in text, "executive thesis section added")
    check("Portfolio Guidance" in text, "portfolio guidance section added")
    check("Research Intelligence" in text, "research intelligence section added")
    check("cio_market_thesis.json" in text, "CIO market thesis wired")
    check("cio_portfolio_directive.json" in text, "CIO portfolio directive wired")
    check("research_firm_portfolio_os_bridge.json" in text, "Portfolio OS bridge wired")
    check("cio_brief.txt" in text, "CIO brief text wired")

    required_artifacts = [
        Path("results/cio/cio_market_thesis.json"),
        Path("results/cio/cio_portfolio_directive.json"),
        Path("results/cio/cio_brief.txt"),
        Path("results/portfolio_os/research_firm_portfolio_os_bridge.json"),
    ]

    for artifact in required_artifacts:
        check(artifact.exists(), f"{artifact} exists")

    print("=" * 80)
    print("[PASS] PHASE 6C.3 DAILY CIO BRIEF DASHBOARD COMPLETE")
    print("AURUM now exposes a clean executive CIO brief in the command center.")
    print("=" * 80)


if __name__ == "__main__":
    main()