from datetime import datetime, timezone

from src.database.postgres_manager import PostgresManager


def utc_now():
    return datetime.now(timezone.utc)


class CommitteeRepository:
    def __init__(self, db: PostgresManager | None = None):
        self.db = db or PostgresManager()

    def insert_decision(
        self,
        investment_view: str,
        approval_status: str,
        confidence: float,
        minutes: str,
        timestamp=None,
        payload: dict | None = None,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO committee_decisions
            (timestamp, investment_view, approval_status, confidence, minutes, payload)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                timestamp or utc_now(),
                investment_view,
                approval_status,
                confidence,
                minutes,
                self.db.json(payload or {}),
            ),
        )