from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
import json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IntelligenceRepository:
    def __init__(self, db) -> None:
        self.db = db

    def initialize_tables(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS cio_directives (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                directive_id TEXT,
                risk_posture TEXT,
                recommended_action TEXT,
                execution_permission TEXT,
                confidence DOUBLE PRECISION,
                payload JSONB
            );

            CREATE TABLE IF NOT EXISTS research_firm_runs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                mode TEXT,
                status TEXT,
                stage_count INTEGER,
                firm_view TEXT,
                payload JSONB
            );

            CREATE TABLE IF NOT EXISTS alpha_rankings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                name TEXT,
                score DOUBLE PRECISION,
                basis TEXT,
                payload JSONB
            );

            CREATE TABLE IF NOT EXISTS portfolio_lab_scenarios (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                scenario_id TEXT,
                name TEXT,
                portfolio_impact DOUBLE PRECISION,
                severity TEXT,
                recommended_response TEXT,
                payload JSONB
            );
            """
        )

    def insert_cio_directive(self, directive: Dict[str, Any]) -> None:
        self.db.execute(
            """
            INSERT INTO cio_directives (
                timestamp,
                directive_id,
                risk_posture,
                recommended_action,
                execution_permission,
                confidence,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                directive.get("timestamp", utc_now()),
                directive.get("directive_id"),
                directive.get("risk_posture"),
                directive.get("recommended_action"),
                directive.get("execution_permission"),
                float(directive.get("confidence", 0.0)),
                json.dumps(directive),
            ),
        )

    def insert_research_firm_run(self, run: Dict[str, Any]) -> None:
        summary = run.get("executive_summary", {})

        self.db.execute(
            """
            INSERT INTO research_firm_runs (
                timestamp,
                mode,
                status,
                stage_count,
                firm_view,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                run.get("timestamp", utc_now()),
                run.get("mode"),
                run.get("status"),
                int(run.get("stage_count", 0)),
                summary.get("firm_view"),
                json.dumps(run),
            ),
        )

    def insert_alpha_rankings(self, rankings: Dict[str, Any]) -> int:
        rows = rankings.get("ranked_entities", [])
        inserted = 0

        for row in rows:
            self.db.execute(
                """
                INSERT INTO alpha_rankings (
                    timestamp,
                    entity_type,
                    entity_id,
                    name,
                    score,
                    basis,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    rankings.get("timestamp", utc_now()),
                    row.get("entity_type"),
                    row.get("entity_id"),
                    row.get("name"),
                    float(row.get("score", 0.0)),
                    row.get("basis"),
                    json.dumps(row),
                ),
            )
            inserted += 1

        return inserted

    def insert_portfolio_lab_scenarios(self, lab_results: Dict[str, Any]) -> int:
        rows = lab_results.get("scenario_results", [])
        inserted = 0

        for row in rows:
            self.db.execute(
                """
                INSERT INTO portfolio_lab_scenarios (
                    timestamp,
                    scenario_id,
                    name,
                    portfolio_impact,
                    severity,
                    recommended_response,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    lab_results.get("timestamp", utc_now()),
                    row.get("scenario_id"),
                    row.get("name"),
                    float(row.get("portfolio_impact", 0.0)),
                    row.get("severity"),
                    row.get("recommended_response"),
                    json.dumps(row),
                ),
            )
            inserted += 1

        return inserted

    def table_count(self, table: str) -> int:
        rows = self.db.fetch_all(f"SELECT COUNT(*) AS count FROM {table}")
        if not rows:
            return 0
        return int(rows[0]["count"])

    def latest_cio_directive(self) -> Dict[str, Any]:
        rows = self.db.fetch_all(
            """
            SELECT
                timestamp,
                directive_id,
                risk_posture,
                recommended_action,
                execution_permission,
                confidence
            FROM cio_directives
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        return rows[0] if rows else {}

    def latest_research_firm_run(self) -> Dict[str, Any]:
        rows = self.db.fetch_all(
            """
            SELECT
                timestamp,
                mode,
                status,
                stage_count,
                firm_view
            FROM research_firm_runs
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        return rows[0] if rows else {}