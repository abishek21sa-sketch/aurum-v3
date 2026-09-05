from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import RealDictCursor, Json

from src.database.database_config import get_database_url


class PostgresManager:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or get_database_url()

    @contextmanager
    def connection(self):
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)

    def fetch_one(self, sql: str, params: Iterable[Any] | None = None) -> dict | None:
        with self.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None

    def fetch_all(self, sql: str, params: Iterable[Any] | None = None) -> list[dict]:
        with self.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    @staticmethod
    def json(value: Any) -> Json:
        return Json(value)