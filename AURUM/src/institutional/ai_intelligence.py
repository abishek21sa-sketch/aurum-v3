"""Read-only AI intelligence surface for the AURUM product runtime.

The product needs to show where its AI is doing useful work without implying
that a language model is an execution engine.  This module creates a small,
evidence-grounded CIO brief and question-answering contract from the current
MARS-CVaR decision.  It runs locally by default.  An external model is only
called when the operator explicitly enables it and confirms external data
transmission with environment flags.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


AI_SCHEMA_VERSION = "1.0"
MAX_QUESTION_LENGTH = 1200


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _load_settings(root: Path) -> dict[str, Any]:
    path = root / "config" / "ai_settings.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _live_configuration(root: Path) -> dict[str, Any]:
    settings = _load_settings(root)
    live_enabled = _truthy("AURUM_AI_LIVE_ENABLED")
    external_approved = _truthy("AURUM_AI_EXTERNAL_APPROVED")
    has_api_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    provider = os.getenv("AURUM_AI_PROVIDER", "local").strip().lower()
    model = os.getenv("AURUM_AI_MODEL", "").strip() or str(settings.get("default_model", "gpt-4o-mini"))
    allowed = provider == "openai" and live_enabled and external_approved and has_api_key
    return {
        "allowed": allowed,
        "provider": provider,
        "model": model,
        "live_enabled": live_enabled,
        "external_approved": external_approved,
        "api_key_present": has_api_key,
    }


def build_ai_status(root: Path) -> dict[str, Any]:
    """Describe the active AI mode without exposing credentials or secrets."""
    config = _live_configuration(root)
    if config["allowed"]:
        mode = "OPENAI_LIVE"
        label = "Live model connected"
        note = "External model calls are enabled by explicit operator configuration."
        external_transmission = True
    else:
        mode = "LOCAL_GROUNDED"
        label = "Grounded analyst active"
        note = "Local evidence-grounded reasoning is active; no portfolio data leaves this runtime."
        external_transmission = False
    return {
        "schema_version": AI_SCHEMA_VERSION,
        "service": "AURUM Intelligence",
        "provider_mode": mode,
        "provider_label": label,
        "model": config["model"] if mode == "OPENAI_LIVE" else "AURUM grounded analyst",
        "live_model_enabled": mode == "OPENAI_LIVE",
        "external_transmission": external_transmission,
        "grounding": "Current MARS-CVaR decision, regime evidence, CVaR lab, walk-forward validation, and governance state.",
        "capabilities": [
            "CIO brief",
            "decision rationale",
            "risk challenge",
            "Ask AURUM",
        ],
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
        "safety_boundary": "AI interprets evidence for human review; it cannot change solver outputs, authorize orders, or promote research.",
        "operator_note": note,
        "configuration": {
            "live_flag_enabled": config["live_enabled"],
            "external_approval_flag_enabled": config["external_approved"],
            "api_key_present": config["api_key_present"],
        },
    }


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _percent(value: Any, digits: int = 2) -> str:
    return f"{100 * _number(value):.{digits}f}%"


def _decision_summary(decision: dict[str, Any]) -> dict[str, Any]:
    raw = decision.get("raw", {}) if isinstance(decision, dict) else {}
    market = decision.get("market_regime", {}) if isinstance(decision, dict) else {}
    risk = decision.get("risk_lab", {}) if isinstance(decision, dict) else {}
    transaction = decision.get("transaction_analysis", {}) if isinstance(decision, dict) else {}
    governance = decision.get("governance", {}) if isinstance(decision, dict) else {}
    workspace = decision.get("portfolio_workspace", {}) if isinstance(decision, dict) else {}
    actions = decision.get("actions", []) if isinstance(decision, dict) else []
    changes = [row for row in actions if abs(_number(str(row.get("change", "0")).replace("%", ""))) > 0.005]
    return {
        "decision_id": decision.get("decision_id"),
        "regime": market.get("current_regime", "unknown"),
        "stress_probability": _number((market.get("decision_input_next_regime_probabilities") or {}).get("stress")),
        "entropy": _number(market.get("probability_entropy_normalized")),
        "expected_return": _number(raw.get("expected_return")),
        "cvar_loss": _number(risk.get("cvar_loss_signed", raw.get("cvar_loss"))),
        "downside": _number(risk.get("downside_loss_magnitude")),
        "turnover": _number(transaction.get("aggregate_l1_turnover", raw.get("turnover"))),
        "alpha": _number(risk.get("confidence_alpha", (raw.get("parameters") or {}).get("alpha"))),
        "actions": actions,
        "material_changes": changes,
        "dominant_tail_scenarios": risk.get("dominant_tail_scenarios", []),
        "scenario_count": risk.get("scenario_count", raw.get("scenario_count")),
        "data_class": (decision.get("data_provenance") or {}).get("decision_data_class", "unknown"),
        "scenario_data_class": (decision.get("data_provenance") or {}).get("scenario_data_class", "unknown"),
        "walk_forward_periods": (decision.get("walk_forward_research") or {}).get("summary", {}).get("periods"),
        "no_lookahead": (decision.get("walk_forward_research") or {}).get("no_lookahead"),
        "optimization_authorization": decision.get("optimization_authorization", governance.get("optimization_authorization")),
        "execution_enabled": governance.get("execution_enabled", False),
        "research_promotion": decision.get("research_promotion", governance.get("research_promotion", "RESEARCH_ONLY")),
        "current_weights": workspace.get("current_weights", {}),
        "target_weights": workspace.get("target_weights", {}),
    }


def _local_brief(decision: dict[str, Any]) -> dict[str, Any]:
    summary = _decision_summary(decision)
    changes = summary["material_changes"]
    if changes:
        moves = "; ".join(
            f"{row.get('asset')} {row.get('change')} to {row.get('target_weight')}"
            for row in changes
        )
    else:
        moves = "No material target-weight changes are present."

    risk_flags: list[str] = []
    if summary["turnover"] > 0.25:
        risk_flags.append(f"Implementation friction: L1 turnover is {_percent(summary['turnover'])}, so liquidity and transaction-cost review matters.")
    if summary["entropy"] >= 0.75:
        risk_flags.append(f"Regime uncertainty: normalized probability entropy is {summary['entropy']:.2f}; the model is not expressing a concentrated regime view.")
    if str(summary["scenario_data_class"]).upper().find("SIMULATED") >= 0:
        risk_flags.append("Scenario limitation: tail evidence is simulated/reference data and should not be read as a live loss forecast.")
    if summary["research_promotion"] != "PROMOTED":
        risk_flags.append("Governance boundary: this is research-only evidence and is not a production recommendation or order instruction.")
    if not risk_flags:
        risk_flags.append("No additional rule-based risk flag was triggered; human review remains required.")

    rationale = [
        f"The current lens is {summary['regime']} with a {_percent(summary['stress_probability'], 0)} modeled next-regime stress input.",
        f"The optimizer proposes {moves}, while holding the other assets at their current target where applicable.",
        f"The modeled expected return is {_percent(summary['expected_return'], 3)} and signed CVaR is {_percent(summary['cvar_loss'], 3)} at alpha {summary['alpha']:.2f}; these are reference-period evidence, not realized performance.",
    ]
    if summary["no_lookahead"] is True:
        rationale.append(f"The walk-forward artifact contains {summary['walk_forward_periods']} no-lookahead periods, but its promotion state remains {summary['research_promotion']}.")

    return {
        "schema_version": AI_SCHEMA_VERSION,
        "mode": "LOCAL_GROUNDED",
        "provider_mode": "LOCAL_GROUNDED",
        "external_transmission": False,
        "generated_at_utc": _now_utc(),
        "decision_id": summary["decision_id"],
        "title": "AURUM Intelligence brief",
        "headline": f"{summary['regime'].title()} regime lens · human review required",
        "executive_summary": (
            f"AURUM Intelligence reads this decision as a risk-aware, evidence-bounded portfolio lens. "
            f"It is responding to a {summary['stress_probability']:.0%} stress input with a modeled "
            f"{_percent(summary['expected_return'], 3)} reference-period return and {_percent(summary['turnover'])} L1 turnover. "
            "The AI is interpreting the repository-native evidence; it is not producing a market forecast."
        ),
        "decision_rationale": rationale,
        "risk_flags": risk_flags,
        "what_would_change_my_view": [
            "Validated live inputs with an explicit missing-data and freshness record.",
            "Out-of-sample evidence that survives transaction costs, regime variation, and an independent review.",
            "A committee-approved implementation plan covering liquidity, limits, and the material SPY/GLD move.",
        ],
        "review_focus": [
            "Challenge the stress-regime assumption and the confidence implied by the transition matrix.",
            "Review the material allocation changes and their implementation cost before any downstream action.",
            "Keep optimization authorization separate from empirical research promotion.",
        ],
        "confidence": "Moderate · grounded in the current deterministic evidence payload",
        "grounding": [
            "Current MARS-CVaR decision payload",
            "Market/regime transition evidence",
            "CVaR scenario lab",
            "Walk-forward validation and governance state",
        ],
        "citations": [
            {"label": "Decision", "value": summary["decision_id"]},
            {"label": "Data class", "value": summary["data_class"]},
            {"label": "Scenario class", "value": summary["scenario_data_class"]},
            {"label": "Promotion", "value": summary["research_promotion"]},
        ],
        "execution_enabled": False,
        "research_promotion": summary["research_promotion"],
        "safety_boundary": "AI interprets evidence for human review; it cannot change solver outputs, authorize orders, or promote research.",
    }


def _compact_context(decision: dict[str, Any]) -> str:
    summary = _decision_summary(decision)
    return json.dumps({
        "decision_id": summary["decision_id"],
        "regime": summary["regime"],
        "stress_probability": summary["stress_probability"],
        "expected_return": summary["expected_return"],
        "cvar_loss_signed": summary["cvar_loss"],
        "turnover": summary["turnover"],
        "alpha": summary["alpha"],
        "actions": summary["actions"],
        "risk_flags": [summary["scenario_data_class"], summary["research_promotion"]],
        "execution_enabled": False,
    }, sort_keys=True)


def _parse_json_response(content: str) -> dict[str, Any] | None:
    text = str(content or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _optional_live_overlay(root: Path, question: str, decision: dict[str, Any], base: dict[str, Any]) -> dict[str, Any] | None:
    config = _live_configuration(root)
    if not config["allowed"]:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        prompt = (
            "You are the AURUM research-only CIO analyst. Use only the supplied JSON. "
            "Do not invent market facts, returns, or events. Do not give an order or execution instruction. "
            "Return JSON with keys executive_summary, decision_rationale, risk_flags, "
            "what_would_change_my_view, review_focus, confidence. Keep each list to at most 4 items.\n\n"
            f"Question: {question or 'Prepare the CIO brief.'}\n"
            f"Evidence: {_compact_context(decision)}"
        )
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": "AURUM Intelligence is read-only, human-gated, and research-only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        parsed = _parse_json_response(response.choices[0].message.content)
        if not parsed:
            return None
        overlay = {
            key: parsed[key]
            for key in ("executive_summary", "decision_rationale", "risk_flags", "what_would_change_my_view", "review_focus", "confidence")
            if key in parsed
        }
        if not overlay:
            return None
        overlay.update({"mode": "OPENAI_LIVE", "provider_mode": "OPENAI_LIVE", "external_transmission": True})
        return overlay
    except Exception:
        # A live model is an enhancement, never a dependency or a silent source
        # of stale data.  The caller will return the grounded local brief.
        return None


def build_ai_brief(root: Path, decision: dict[str, Any], question: str = "") -> dict[str, Any]:
    """Build a grounded brief, optionally overlaying an explicitly enabled LLM."""
    base = _local_brief(decision)
    question = str(question or "").strip()[:MAX_QUESTION_LENGTH]
    overlay = _optional_live_overlay(root, question, decision, base)
    if overlay:
        base.update(overlay)
    base["question"] = question or None
    return base


def answer_ai_question(root: Path, decision: dict[str, Any], question: str) -> dict[str, Any]:
    """Answer a bounded Ask AURUM question against the current decision."""
    question = str(question or "").strip()[:MAX_QUESTION_LENGTH]
    if not question:
        question = "What is the most important thing to review in this decision?"
    brief = build_ai_brief(root, decision, question)
    if brief.get("mode") == "OPENAI_LIVE":
        answer = brief.get("executive_summary", "")
    else:
        normalized = question.lower()
        if any(token in normalized for token in ("risk", "fragile", "downside", "tail", "crash")):
            answer = " ".join(brief["risk_flags"][:2])
        elif any(token in normalized for token in ("why", "allocation", "move", "change", "portfolio")):
            answer = " ".join(brief["decision_rationale"][:2])
        elif any(token in normalized for token in ("confidence", "regime", "certain", "probability")):
            answer = brief["decision_rationale"][0] + " " + brief["risk_flags"][1 if len(brief["risk_flags"]) > 1 else 0]
        else:
            answer = brief["executive_summary"]
    return {
        "schema_version": AI_SCHEMA_VERSION,
        "mode": brief.get("mode", "LOCAL_GROUNDED"),
        "provider_mode": brief.get("provider_mode", "LOCAL_GROUNDED"),
        "external_transmission": bool(brief.get("external_transmission", False)),
        "generated_at_utc": _now_utc(),
        "question": question,
        "answer": answer,
        "grounding": brief.get("grounding", []),
        "decision_id": brief.get("decision_id"),
        "execution_enabled": False,
        "research_promotion": brief.get("research_promotion", "RESEARCH_ONLY"),
        "safety_boundary": brief.get("safety_boundary"),
    }
