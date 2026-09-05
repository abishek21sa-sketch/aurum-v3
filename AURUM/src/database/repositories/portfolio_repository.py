from datetime import datetime, timezone
from uuid import uuid4

from src.database.postgres_manager import PostgresManager


def utc_now():
    return datetime.now(timezone.utc)


class PortfolioRepository:
    def __init__(self, db: PostgresManager | None = None):
        self.db = db or PostgresManager()

    def insert_state(
        self,
        portfolio_value: float,
        cash: float,
        risk_budget: float,
        regime: str,
        health: str,
        timestamp=None,
        payload: dict | None = None,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO portfolio_state
            (timestamp, portfolio_value, cash, risk_budget, regime, health, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                timestamp or utc_now(),
                portfolio_value,
                cash,
                risk_budget,
                regime,
                health,
                self.db.json(payload or {}),
            ),
        )

    def insert_decision(
        self,
        action: str,
        confidence: float,
        rationale: str,
        execution_permission: str,
        timestamp=None,
        payload: dict | None = None,
        decision_id: str | None = None,
    ) -> str:
        did = decision_id or f"decision_{uuid4().hex[:12]}"

        self.db.execute(
            """
            INSERT INTO portfolio_decisions
            (decision_id, timestamp, action, confidence, rationale, execution_permission, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (decision_id) DO UPDATE
            SET timestamp = EXCLUDED.timestamp,
                action = EXCLUDED.action,
                confidence = EXCLUDED.confidence,
                rationale = EXCLUDED.rationale,
                execution_permission = EXCLUDED.execution_permission,
                payload = EXCLUDED.payload;
            """,
            (
                did,
                timestamp or utc_now(),
                action,
                confidence,
                rationale,
                execution_permission,
                self.db.json(payload or {}),
            ),
        )

        return did