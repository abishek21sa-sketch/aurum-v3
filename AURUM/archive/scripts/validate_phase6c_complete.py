from pathlib import Path
import importlib
import os
import yaml


REQUIRED_MODULES = [
    "src.portfolio_os.research_firm_bridge",
    "src.institutional.daily_institutional_cycle",
    "src.institutional.daily_institutional_report_generator",
    "src.database.repositories.intelligence_repository",
    "src.research_firm.ai_research_firm_mode",
    "src.cio.chief_investment_officer_agent",
]

REQUIRED_ARTIFACTS = [
    "results/portfolio_os/research_firm_portfolio_os_bridge.json",
    "results/research_firm/ai_research_firm_mode.json",
    "results/research_firm/daily_research_firm_state.json",
    "results/cio/cio_market_thesis.json",
    "results/cio/cio_portfolio_directive.json",
    "results/cio/cio_brief.txt",
    "results/alpha_ranking/institutional_research_rankings.json",
    "results/institutional/daily_institutional_cycle.json",
    "results/institutional/daily_institutional_report.txt",
]

REQUIRED_DASHBOARD_TERMS = [
    '"AI Research Firm"',
    '"Daily CIO Brief"',
    "ai_research_firm_mode.json",
    "research_firm_portfolio_os_bridge.json",
    "cio_brief.txt",
    "cio_market_thesis.json",
    "cio_portfolio_directive.json",
]

REQUIRED_DB_TABLES = [
    "cio_directives",
    "research_firm_runs",
    "alpha_rankings",
    "portfolio_lab_scenarios",
]


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


def validate_dashboard_pages() -> None:
    dashboard = Path("src/dashboard/institutional_command_center.py")
    check(dashboard.exists(), "official command center exists")

    text = dashboard.read_text(encoding="utf-8", errors="ignore")

    for term in REQUIRED_DASHBOARD_TERMS:
        check(term in text, f"dashboard contains {term}")


def validate_compose_research_firm() -> None:
    compose_path = Path("docker-compose.yml")
    check(compose_path.exists(), "docker-compose.yml exists")

    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    services = compose.get("services", {})

    check("research_firm" in services, "research_firm service exists in docker-compose")

    service = services["research_firm"]
    command = service.get("command", [])
    command_text = " ".join(command) if isinstance(command, list) else str(command)

    check(
        "src.research_firm.ai_research_firm_mode" in command_text,
        "research_firm service runs AI Research Firm mode",
    )


def validate_database_tables() -> None:
    try:
        from src.database.postgres_manager import PostgresManager
        from src.database.repositories.intelligence_repository import IntelligenceRepository

        db = PostgresManager()
        repo = IntelligenceRepository(db)
        repo.initialize_tables()

        for table in REQUIRED_DB_TABLES:
            count = repo.table_count(table)
            check(count >= 0, f"{table} table readable", str(count))

    except Exception as exc:
        check(False, "database intelligence tables readable", str(exc))


def validate_daily_cycle_artifact() -> None:
    import json

    path = Path("results/institutional/daily_institutional_cycle.json")
    check(path.exists(), "daily institutional cycle artifact exists")

    payload = json.loads(path.read_text(encoding="utf-8"))

    check(payload.get("status") in {"complete", "degraded"}, "daily cycle status valid")
    check(payload.get("stage_count", 0) >= 6, "daily cycle has at least 6 stages")
    check(payload.get("executive_summary", {}).get("best_alpha") != "unknown", "daily cycle has best alpha")
    check(payload.get("executive_summary", {}).get("cio_action") != "unknown", "daily cycle has CIO action")


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6C COMPLETE VALIDATION")
    print("=" * 80)

    if not os.getenv("TIMESCALE_DATABASE_URL"):
        print("[WARN] TIMESCALE_DATABASE_URL is not set. Database checks may fail.")

    print("\nMODULE CHECKS")
    print("-" * 80)
    for module in REQUIRED_MODULES:
        importlib.import_module(module)
        check(True, f"import {module}")

    print("\nARTIFACT CHECKS")
    print("-" * 80)
    for artifact in REQUIRED_ARTIFACTS:
        check(Path(artifact).exists(), f"{artifact} exists")

    print("\nDASHBOARD CHECKS")
    print("-" * 80)
    validate_dashboard_pages()

    print("\nDEPLOYMENT CHECKS")
    print("-" * 80)
    validate_compose_research_firm()

    print("\nDATABASE CHECKS")
    print("-" * 80)
    validate_database_tables()

    print("\nDAILY CYCLE CHECKS")
    print("-" * 80)
    validate_daily_cycle_artifact()

    print("=" * 80)
    print("[PASS] PHASE 6C PRODUCTION INTELLIGENCE INTEGRATION COMPLETE")
    print("AURUM now integrates AI Research Firm intelligence into the daily institutional operating system.")
    print("=" * 80)


if __name__ == "__main__":
    main()