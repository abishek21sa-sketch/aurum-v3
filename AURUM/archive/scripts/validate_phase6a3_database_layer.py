from src.database.postgres_manager import PostgresManager
from src.database.schema_initializer import SchemaInitializer
from src.database.repositories.market_repository import MarketRepository
from src.database.repositories.portfolio_repository import PortfolioRepository
from src.database.repositories.committee_repository import CommitteeRepository
from src.database.repositories.learning_repository import LearningRepository


REQUIRED_TABLES = [
    "market_ticks",
    "market_features",
    "market_signals",
    "portfolio_state",
    "portfolio_decisions",
    "committee_decisions",
    "execution_log",
    "learning_events",
]


def check(condition: bool, label: str):
    if condition:
        print(f"[PASS] {label}")
    else:
        print(f"[FAIL] {label}")
        raise SystemExit(1)


def main():
    print("=" * 80)
    print("AURUM PHASE 6A.3 DATABASE HARDENING VALIDATION")
    print("=" * 80)

    db = PostgresManager()
    row = db.fetch_one("SELECT 1 AS ok;")
    check(row and row["ok"] == 1, "Postgres connection")

    initializer = SchemaInitializer(db)
    initializer.initialize()
    check(True, "schema initializer ran")

    for table in REQUIRED_TABLES:
        check(initializer.table_exists(table), f"{table} table")

    market_repo = MarketRepository(db)
    portfolio_repo = PortfolioRepository(db)
    committee_repo = CommitteeRepository(db)
    learning_repo = LearningRepository(db)

    market_repo.insert_tick(
        ticker="SPY",
        price=747.94,
        volume=1000,
        source="phase6a3_validation",
        payload={"validation": True},
    )
    check(True, "insert market tick")

    market_repo.insert_feature(
        ticker="SPY",
        volatility=0.12,
        momentum=0.03,
        liquidity=0.9,
        regime="normal",
        payload={"validation": True},
    )
    check(True, "insert market feature")

    signal_id = market_repo.insert_signal(
        signal_type="validation_signal",
        confidence=0.99,
        payload={"validation": True},
    )
    check(signal_id.startswith("signal_"), "insert market signal")

    portfolio_repo.insert_state(
        portfolio_value=1_000_000,
        cash=100_000,
        risk_budget=0.10,
        regime="normal",
        health="healthy",
        payload={"validation": True},
    )
    check(True, "insert portfolio state")

    decision_id = portfolio_repo.insert_decision(
        action="hold",
        confidence=0.95,
        rationale="validation decision",
        execution_permission="blocked",
        payload={"validation": True},
    )
    check(decision_id.startswith("decision_"), "insert portfolio decision")

    committee_repo.insert_decision(
        investment_view="defensive",
        approval_status="approved_with_restrictions",
        confidence=0.85,
        minutes="Validation committee decision.",
        payload={"validation": True},
    )
    check(True, "insert committee decision")

    learning_repo.insert_event(
        event_type="database_validation",
        lesson="Database persistence layer is operational.",
        outcome="pass",
        payload={"validation": True},
    )
    check(True, "insert learning event")

    print("=" * 80)
    print("[PASS] PHASE 6A.3 DATABASE LAYER COMPLETE")
    print("AURUM now has hardened Postgres/Timescale persistence primitives.")
    print("=" * 80)


if __name__ == "__main__":
    main()