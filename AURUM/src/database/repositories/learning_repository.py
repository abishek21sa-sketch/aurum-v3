from datetime import datetime, timezone

from src.database.postgres_manager import PostgresManager


def utc_now():
    return datetime.now(timezone.utc)


class LearningRepository:
    def __init__(self, db: PostgresManager | None = None):
        self.db = db or PostgresManager()

    def insert_event(
        self,
        event_type: str,
        lesson: str,
        outcome: str,
        timestamp=None,
        payload: dict | None = None,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO learning_events
            (timestamp, event_type, lesson, outcome, payload)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                timestamp or utc_now(),
                event_type,
                lesson,
                outcome,
                self.db.json(payload or {}),
            ),
        )