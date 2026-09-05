from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


INPUT_PATH = Path("results/institutional/canonical_runtime_state.json")

OUTPUT_DIR = Path("results/institutional")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "decision_explanation.json"
OUTPUT_TXT = OUTPUT_DIR / "decision_explanation.txt"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_key_drivers(state: Dict[str, Any]) -> List[str]:
    drivers = []

    if state.get("should_optimize"):
        drivers.append("Optimizer trigger is active.")

    if state.get("recommended_posture") == "reduce_risk":
        drivers.append("Recommended posture is risk reduction.")

    if state.get("risk_level") in {"moderate", "high", "critical"}:
        drivers.append(f"Risk level is {state.get('risk_level')}.")

    stress = float(state.get("stress_score", 0.0) or 0.0)

    if stress >= 0.8:
        drivers.append("Market stress is elevated above institutional review threshold.")
    elif stress >= 0.4:
        drivers.append("Market stress is in watch range.")
    else:
        drivers.append("Market stress is currently low.")

    if state.get("state_label") in {"watch", "stressed", "critical"}:
        drivers.append(f"Digital twin state is {state.get('state_label')}.")

    return drivers


def build_risk_context(state: Dict[str, Any]) -> List[str]:
    return [
        f"Projected VaR 95: {float(state.get('projected_var_95', 0.0)):.4f}",
        f"Projected CVaR 95: {float(state.get('projected_cvar_95', 0.0)):.4f}",
        f"Projected drawdown: {float(state.get('projected_drawdown', 0.0)):.4f}",
        f"Risk level: {state.get('risk_level')}",
    ]


def build_governance_context(state: Dict[str, Any]) -> List[str]:
    return [
        f"Governance status: {state.get('governance_status')}",
        f"Governance score: {state.get('governance_score')}",
        f"Readiness status: {state.get('readiness_status')}",
        f"Coherence gate: {state.get('gate_status')}",
        f"Execution allowed: {state.get('allow_execution')}",
    ]


def build_alternatives(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    action = state.get("portfolio_action")

    alternatives = [
        {
            "alternative": "hold",
            "status": "rejected" if action != "hold" else "selected",
            "reason": "Holding would avoid turnover but would not respond to current risk-reduction posture.",
        },
        {
            "alternative": "reduce_equity",
            "status": "selected" if action == "reduce_equity" else "available",
            "reason": "Reduces equity beta and increases defensive exposure.",
        },
        {
            "alternative": "risk_off_rotation",
            "status": "not_required",
            "reason": "Reserved for crisis or critical risk conditions.",
        },
        {
            "alternative": "increase_cash",
            "status": "not_required",
            "reason": "Reserved for liquidity stress or explicit cash-raising posture.",
        },
    ]

    return alternatives


def build_confidence(state: Dict[str, Any]) -> float:
    confidence = 0.70

    if state.get("consistency_status") in {
        "CONSISTENT",
        "CONDITIONALLY_CONSISTENT",
    }:
        confidence += 0.10

    if state.get("governance_status") == "CLEAR":
        confidence += 0.10

    if state.get("research_ready"):
        confidence += 0.05

    if not state.get("allow_execution"):
        confidence -= 0.10

    return max(0.0, min(confidence, 0.95))


def generate_decision_explanation() -> Dict[str, Any]:
    state = load_json(INPUT_PATH)

    if not state:
        raise RuntimeError(
            "canonical_runtime_state.json not found. "
            "Run src.institutional.canonical_runtime_state_engine first."
        )

    explanation = {
        "platform": "AURUM",
        "phase": "Phase 4K",
        "module": "Decision Explanation Engine",
        "decision": state.get("portfolio_action"),
        "decision_reason": state.get("decision_reason"),
        "current_regime": state.get("current_regime"),
        "state_label": state.get("state_label"),
        "risk_level": state.get("risk_level"),
        "recommended_posture": state.get("recommended_posture"),
        "confidence": build_confidence(state),
        "key_drivers": build_key_drivers(state),
        "risk_context": build_risk_context(state),
        "governance_context": build_governance_context(state),
        "alternatives_considered": build_alternatives(state),
        "execution_permission": {
            "allow_decision": state.get("allow_decision"),
            "allow_execution": state.get("allow_execution"),
            "gate_status": state.get("gate_status"),
            "production_ready": state.get("production_ready"),
            "research_ready": state.get("research_ready"),
        },
        "institutional_summary": build_institutional_summary(state),
    }

    save_explanation(explanation)
    return explanation


def build_institutional_summary(state: Dict[str, Any]) -> str:
    action = state.get("portfolio_action")
    regime = state.get("current_regime")
    risk = state.get("risk_level")
    posture = state.get("recommended_posture")
    gate = state.get("gate_status")
    allow_execution = state.get("allow_execution")

    summary = (
        f"AURUM recommends {action} under a {regime} regime with {risk} risk. "
        f"The active posture is {posture}. "
    )

    if allow_execution:
        summary += "Execution is currently permitted by runtime controls."
    else:
        summary += (
            f"Execution is not currently released because the coherence gate is {gate}."
        )

    return summary


def save_explanation(explanation: Dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(json.dumps(explanation, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM DECISION EXPLANATION")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Decision: {explanation['decision']}")
    lines.append(f"Reason: {explanation['decision_reason']}")
    lines.append(f"Confidence: {explanation['confidence']:.2f}")
    lines.append("")
    lines.append("INSTITUTIONAL SUMMARY")
    lines.append("-" * 80)
    lines.append(explanation["institutional_summary"])
    lines.append("")
    lines.append("KEY DRIVERS")
    lines.append("-" * 80)

    for item in explanation["key_drivers"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("RISK CONTEXT")
    lines.append("-" * 80)

    for item in explanation["risk_context"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("GOVERNANCE CONTEXT")
    lines.append("-" * 80)

    for item in explanation["governance_context"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("ALTERNATIVES CONSIDERED")
    lines.append("-" * 80)

    for alt in explanation["alternatives_considered"]:
        lines.append(
            f"- {alt['alternative']} | {alt['status']} | {alt['reason']}"
        )

    lines.append("")
    lines.append("EXECUTION PERMISSION")
    lines.append("-" * 80)

    for key, value in explanation["execution_permission"].items():
        lines.append(f"{key}: {value}")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = generate_decision_explanation()

    print("=" * 80)
    print("AURUM DECISION EXPLANATION ENGINE")
    print("=" * 80)
    print(f"Decision: {result['decision']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")