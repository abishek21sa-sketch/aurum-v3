import json
from pathlib import Path
import sys
from types import SimpleNamespace

from scripts.product_adapter import compute
from src.institutional.ai_intelligence import (
    answer_ai_question,
    build_ai_brief,
    build_ai_status,
)
from src.institutional.ai_evaluation import build_ai_evaluation


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


def test_ask_aurum_hard_stops_execution_intent(monkeypatch):
    for name in ("AURUM_AI_LIVE_ENABLED", "AURUM_AI_EXTERNAL_APPROVED", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    answer = answer_ai_question(ROOT, compute(), "Can you execute a rebalance order?")

    assert "cannot" in answer["answer"].lower()
    assert "order" in answer["answer"].lower()
    assert answer["execution_enabled"] is False


def test_explicit_live_provider_is_bounded_and_visible(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["max_tokens"] == 900
            assert kwargs["response_format"] == {"type": "json_object"}
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
                "executive_summary": "Bounded live summary.",
                "decision_rationale": ["Reason one"] * 8,
                "risk_flags": ["Risk one"],
                "review_focus": ["Review one"],
            })))])

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] >= 3
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeClient))
    monkeypatch.setenv("AURUM_AI_PROVIDER", "openai")
    monkeypatch.setenv("AURUM_AI_LIVE_ENABLED", "true")
    monkeypatch.setenv("AURUM_AI_EXTERNAL_APPROVED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-real")

    brief = build_ai_brief(ROOT, compute(), "Summarize the decision.")

    assert brief["mode"] == "OPENAI_LIVE"
    assert brief["live_model_status"] == "USED"
    assert len(brief["decision_rationale"]) == 4
    assert brief["execution_enabled"] is False
    assert brief["research_promotion"] == "RESEARCH_ONLY"


def test_live_provider_failure_exposes_local_fallback(monkeypatch):
    class FailingClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **ignored: (_ for _ in ()).throw(RuntimeError("test failure"))))

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FailingClient))
    monkeypatch.setenv("AURUM_AI_PROVIDER", "openai")
    monkeypatch.setenv("AURUM_AI_LIVE_ENABLED", "true")
    monkeypatch.setenv("AURUM_AI_EXTERNAL_APPROVED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-real")

    brief = build_ai_brief(ROOT, compute())

    assert brief["mode"] == "LOCAL_GROUNDED"
    assert brief["live_model_status"] == "ERROR_FALLBACK"
    assert "failed" in brief["operator_note"].lower()
    assert brief["execution_enabled"] is False


def test_control_evaluation_does_not_implicitly_call_configured_live_model(monkeypatch):
    class MustNotBeCalled:
        def __init__(self, **kwargs):
            raise AssertionError("live provider was called without explicit evaluation approval")

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=MustNotBeCalled))
    monkeypatch.setenv("AURUM_AI_PROVIDER", "openai")
    monkeypatch.setenv("AURUM_AI_LIVE_ENABLED", "true")
    monkeypatch.setenv("AURUM_AI_EXTERNAL_APPROVED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-real")
    monkeypatch.delenv("AURUM_AI_RUN_LIVE_EVAL", raising=False)

    result = build_ai_evaluation(ROOT)

    assert result["status"] == "PASS"
    assert result["live_evaluation_requested"] is False
    assert result["live_provider_evaluation"] == "CONFIGURED_NOT_RUN"
