from pathlib import Path
import importlib
import json

from src.database.postgres_manager import PostgresManager
from src.database.repositories.intelligence_repository import IntelligenceRepository


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
    print("AURUM PHASE 6C.4 INTELLIGENCE PERSISTENCE VALIDATION")
    print("=" * 80)

    importlib.import_module("src.database.repositories.intelligence_repository")
    check(True, "intelligence repository imports")

    required_artifacts = [
        Path("results/cio/cio_portfolio_directive.json"),
        Path("results/research_firm/ai_research_firm_mode.json"),
        Path("results/alpha_ranking/institutional_research_rankings.json"),
        Path("results/portfolio_lab_2/portfolio_lab_results.json"),
    ]

    for artifact in required_artifacts:
        check(artifact.exists(), f"{artifact} exists")

    db = PostgresManager()
    repo = IntelligenceRepository(db)

    repo.initialize_tables()
    check(True, "intelligence persistence tables initialized")

    cio_directive = load_json("results/cio/cio_portfolio_directive.json")
    research_firm = load_json("results/research_firm/ai_research_firm_mode.json")
    alpha_rankings = load_json("results/alpha_ranking/institutional_research_rankings.json")
    portfolio_lab = load_json("results/portfolio_lab_2/portfolio_lab_results.json")

    repo.insert_cio_directive(cio_directive)
    check(True, "CIO directive inserted")

    repo.insert_research_firm_run(research_firm)
    check(True, "research firm run inserted")

    alpha_inserted = repo.insert_alpha_rankings(alpha_rankings)
    check(alpha_inserted >= 8, "alpha rankings inserted", str(alpha_inserted))

    scenarios_inserted = repo.insert_portfolio_lab_scenarios(portfolio_lab)
    check(scenarios_inserted >= 5, "portfolio lab scenarios inserted", str(scenarios_inserted))

    expected_tables = [
        "cio_directives",
        "research_firm_runs",
        "alpha_rankings",
        "portfolio_lab_scenarios",
    ]

    for table in expected_tables:
        count = repo.table_count(table)
        check(count > 0, f"{table} has rows", str(count))

    latest_cio = repo.latest_cio_directive()
    latest_run = repo.latest_research_firm_run()

    check(latest_cio.get("recommended_action") is not None, "latest CIO directive readable")
    check(latest_run.get("status") == "complete", "latest research firm run readable")

    print("=" * 80)
    print("[PASS] PHASE 6C.4 INTELLIGENCE PERSISTENCE COMPLETE")
    print("AURUM now persists 6B intelligence outputs into Postgres.")
    print("=" * 80)


if __name__ == "__main__":
    main()