"""Contract-level evaluation for the AURUM Intelligence layer."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from src.institutional.ai_intelligence import (
    answer_ai_question,
    build_ai_brief,
    build_ai_status,
)


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def build_ai_evaluation(root: Path, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    if decision is None:
        from scripts.product_adapter import compute

        decision = compute()
    status = build_ai_status(root)
    live_eval_requested = _truthy("AURUM_AI_RUN_LIVE_EVAL")
    brief = build_ai_brief(root, decision, allow_live=live_eval_requested)
    answer = answer_ai_question(root, decision, "What is the main risk in this decision?", allow_live=live_eval_requested)
    checks = [
        {"check_id": "ai.provider_mode_declared", "status": "PASS" if status.get("provider_mode") else "FAIL", "summary": "The active AI provider mode is explicit"},
        {"check_id": "ai.brief_grounded", "status": "PASS" if brief.get("decision_id") == decision.get("decision_id") and brief.get("grounding") else "FAIL", "summary": "The brief is tied to the current decision and grounding sources"},
        {"check_id": "ai.question_response_grounded", "status": "PASS" if answer.get("decision_id") == decision.get("decision_id") and answer.get("answer") else "FAIL", "summary": "Ask AURUM returns a bounded answer tied to the current decision"},
        {"check_id": "ai.execution_boundary", "status": "PASS" if status.get("execution_enabled") is False and brief.get("execution_enabled") is False and answer.get("execution_enabled") is False else "FAIL", "summary": "AI cannot enable execution"},
        {"check_id": "ai.promotion_boundary", "status": "PASS" if brief.get("research_promotion") == "RESEARCH_ONLY" else "FAIL", "summary": "AI cannot promote research"},
        {"check_id": "ai.external_transmission_explicit", "status": "PASS" if status.get("provider_mode") == "LOCAL_GROUNDED" or status.get("external_transmission") is True else "FAIL", "summary": "External transmission is either disabled or explicitly visible"},
    ]
    failures = [check for check in checks if check["status"] == "FAIL"]
    return {
        "schema_version": "1.0",
        "service": "AURUM Intelligence evaluation contract",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "PASS" if not failures else "FAIL",
        "provider_mode": status.get("provider_mode"),
        "live_provider_evaluation": "LIVE_EVALUATION_REQUESTED" if live_eval_requested and status.get("live_model_enabled") else "CONFIGURED_NOT_RUN" if status.get("live_model_enabled") else "SKIPPED_NO_EXPLICIT_LIVE_MODEL",
        "live_evaluation_requested": live_eval_requested,
        "checks": checks,
        "summary": {"total_checks": len(checks), "passed_checks": len(checks) - len(failures), "failed_checks": len(failures)},
        "decision_id": decision.get("decision_id"),
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
        "claim_boundary": "Contract checks validate grounding and safety boundaries; they do not prove model quality, factual accuracy, or investment performance.",
    }
