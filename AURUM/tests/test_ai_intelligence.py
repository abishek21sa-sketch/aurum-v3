from pathlib import Path

from scripts.product_adapter import compute
from src.institutional.ai_intelligence import (
    answer_ai_question,
    build_ai_brief,
    build_ai_status,
)


ROOT = Path(__file__).resolve().parents[1]


def test_ai_status_is_visible_and_fail_closed_by_default(monkeypatch):
    for name in ("AURUM_AI_LIVE_ENABLED", "AURUM_AI_EXTERNAL_APPROVED", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    status = build_ai_status(ROOT)

    assert status["service"] == "AURUM Intelligence"
    assert status["provider_mode"] == "LOCAL_GROUNDED"
    assert status["external_transmission"] is False
    assert status["execution_enabled"] is False
    assert "Ask AURUM" in status["capabilities"]


def test_ai_brief_is_grounded_in_current_decision_and_governance(monkeypatch):
    for name in ("AURUM_AI_LIVE_ENABLED", "AURUM_AI_EXTERNAL_APPROVED", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    decision = compute()
    brief = build_ai_brief(ROOT, decision)

    assert brief["decision_id"] == decision["decision_id"]
    assert brief["mode"] == "LOCAL_GROUNDED"
    assert brief["decision_rationale"]
    assert brief["risk_flags"]
    assert brief["execution_enabled"] is False
    assert brief["research_promotion"] == "RESEARCH_ONLY"
    assert "SPY" in brief["executive_summary"] or "stress" in brief["executive_summary"].lower()


def test_ask_aurum_returns_bounded_read_only_answer(monkeypatch):
    for name in ("AURUM_AI_LIVE_ENABLED", "AURUM_AI_EXTERNAL_APPROVED", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    answer = answer_ai_question(ROOT, compute(), "What is the main risk in this allocation?")

    assert answer["answer"]
    assert answer["mode"] == "LOCAL_GROUNDED"
    assert answer["execution_enabled"] is False
    assert answer["research_promotion"] == "RESEARCH_ONLY"
    assert len(answer["question"]) <= 1200
