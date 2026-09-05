from pathlib import Path


REQUIRED_DOCS = {
    "MASTER_VISION.md": [
        "Institutional Market Operating System",
        "reliable",
        "auditable",
        "scalable",
        "deployable",
        "maintainable",
    ],
    "SYSTEM_ARCHITECTURE.md": [
        "AURUM System Architecture",
        "Portfolio Operating System",
        "dashboard/official_dashboard.py",
        "Redis",
        "TimescaleDB",
        "Docker Compose",
    ],
    "DATA_PIPELINE.md": [
        "AURUM Data Pipeline",
        "YFinanceProvider",
        "PolygonProvider",
        "AlpacaProvider",
        "market_ticks",
        "learning_events",
    ],
    "PORTFOLIO_OS.md": [
        "AURUM Portfolio Operating System",
        "Research",
        "Committee",
        "Memory",
        "Decision Intelligence",
        "Governance",
        "Portfolio Directive",
    ],
    "AI_COMMITTEE.md": [
        "AURUM AI Committee",
        "AI Committee",
        "investment_committee_minutes.json",
        "committee_decision.json",
        "Governance",
    ],
    "OPERATIONS_MANUAL.md": [
        "AURUM Operations Manual",
        "docker compose up",
        "localhost:8501",
        "validate_phase6a5_reliability_layer",
        "validate_phase6a6_deployment_layer",
        "validate_phase6a7_documentation_layer",
    ],
}


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
    print("AURUM PHASE 6A.7 DOCUMENTATION LAYER VALIDATION")
    print("=" * 80)

    for filename, required_terms in REQUIRED_DOCS.items():
        path = Path(filename)

        check(path.exists(), f"{filename} exists")

        text = path.read_text(encoding="utf-8", errors="ignore")

        check(
            len(text.strip()) > 100,
            f"{filename} has substantive content",
            f"{len(text.strip())} characters",
        )

        for term in required_terms:
            check(term in text, f"{filename} contains '{term}'")

    print("=" * 80)
    print("[PASS] PHASE 6A.7 DOCUMENTATION LAYER COMPLETE")
    print("AURUM now has institutional documentation coverage.")
    print("=" * 80)


if __name__ == "__main__":
    main()