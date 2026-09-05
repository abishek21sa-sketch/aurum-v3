from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import redis


REDIS_URL = "redis://localhost:6379/0"

OUTPUT_DIR = Path("results/institutional")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CANONICAL_JSON = OUTPUT_DIR / "canonical_runtime_state.json"
CANONICAL_TXT = OUTPUT_DIR / "canonical_runtime_state.txt"


STREAMS = {
    "market_signals": "live_digital_twin_state",
    "risk_events": "risk_projection",
    "portfolio_decisions": "portfolio_decision",
    "execution_orders": "execution_order",
    "trade_tickets": "trade_ticket",
    "governance_events": "governance_report",
}


@dataclass
class CanonicalRuntimeState:
    timestamp_utc: str
    platform: str
    state_version: str

    current_regime: str
    state_label: str
    stress_score: float
    latest_ticker: str
    latest_price: float

    risk_level: str
    projected_var_95: float
    projected_cvar_95: float
    projected_drawdown: float

    portfolio_action: str
    recommended_posture: str
    should_optimize: bool
    decision_reason: str

    execution_action: str
    execution_ticker: str
    execution_priority: str
    trade_ticket_status: str

    governance_status: str
    governance_score: int

    readiness_status: str
    gate_status: str
    allow_decision: bool
    allow_execution: bool

    consistency_status: str
    production_ready: bool
    research_ready: bool


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def decode_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    if "payload" in event:
        try:
            payload = json.loads(event["payload"])
            if isinstance(payload, dict):
                merged = event.copy()
                merged.update(payload)
                return merged
        except Exception:
            pass

    decoded = {}

    for key, value in event.items():
        try:
            decoded[key] = json.loads(value)
        except Exception:
            decoded[key] = value

    return decoded


def latest_event(client: redis.Redis, stream: str, event_type: Optional[str] = None) -> Dict[str, Any]:
    try:
        rows = client.xrevrange(stream, count=100)
    except Exception:
        return {}

    for _, raw in rows:
        event = decode_payload(raw)
        if event_type is None or event.get("event_type") == event_type:
            return event

    return {}


def determine_consistency(
    regime: str,
    state_label: str,
    stress_score: float,
    risk_level: str,
    governance_status: str,
    readiness_status: str,
) -> str:
    contradictions = []

    if state_label in {"critical", "breach"} and risk_level in {"low", "moderate"}:
        contradictions.append("critical_state_with_noncritical_risk")

    if stress_score >= 0.8 and risk_level not in {"high", "critical", "breach"}:
        contradictions.append("high_stress_with_low_risk")

    if governance_status == "CLEAR" and readiness_status == "NOT_READY":
        contradictions.append("governance_clear_but_not_ready")

    if regime == "normal" and state_label in {"critical", "breach"}:
        contradictions.append("normal_regime_with_critical_state")

    if contradictions:
        return "INCONSISTENT"

    if readiness_status in {"RESEARCH_READY", "CONDITIONALLY_READY"}:
        return "CONDITIONALLY_CONSISTENT"

    return "CONSISTENT"


def build_canonical_state() -> CanonicalRuntimeState:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    market = latest_event(client, "market_signals", "live_digital_twin_state")
    risk = latest_event(client, "risk_events", "risk_projection")
    decision = latest_event(client, "portfolio_decisions", "portfolio_decision")
    order = latest_event(client, "execution_orders", "execution_order")
    ticket = latest_event(client, "trade_tickets", "trade_ticket")
    governance_event = latest_event(client, "governance_events", "governance_report")

    governance_report = load_json(Path("results/governance/execution_governance_report.json"))
    readiness_report = load_json(Path("results/institutional/institutional_readiness_report.json"))
    gate = load_json(Path("results/institutional/runtime_coherence_gate.json"))

    current_regime = str(market.get("current_regime", "unknown"))
    state_label = str(market.get("state_label", "unknown"))
    stress_score = safe_float(market.get("market_stress_score", 0.0))

    risk_level = str(risk.get("risk_level", "unknown"))

    governance_status = str(
        governance_report.get(
            "governance_status",
            governance_event.get("governance_status", "UNKNOWN"),
        )
    )

    readiness_status = str(readiness_report.get("overall_status", "UNKNOWN"))

    consistency_status = determine_consistency(
        regime=current_regime,
        state_label=state_label,
        stress_score=stress_score,
        risk_level=risk_level,
        governance_status=governance_status,
        readiness_status=readiness_status,
    )

    return CanonicalRuntimeState(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        platform="AURUM",
        state_version="4J.1",

        current_regime=current_regime,
        state_label=state_label,
        stress_score=stress_score,
        latest_ticker=str(market.get("latest_ticker", "unknown")),
        latest_price=safe_float(market.get("latest_price", 0.0)),

        risk_level=risk_level,
        projected_var_95=safe_float(risk.get("projected_var_95", 0.0)),
        projected_cvar_95=safe_float(risk.get("projected_cvar_95", 0.0)),
        projected_drawdown=safe_float(
            risk.get("projected_drawdown", risk.get("projected_expected_drawdown", 0.0))
        ),

        portfolio_action=str(decision.get("action", "unknown")),
        recommended_posture=str(decision.get("recommended_posture", "unknown")),
        should_optimize=safe_bool(decision.get("should_optimize", False)),
        decision_reason=str(decision.get("reason", "")),

        execution_action=str(order.get("action", "unknown")),
        execution_ticker=str(order.get("ticker", "unknown")),
        execution_priority=str(order.get("priority", "unknown")),
        trade_ticket_status=str(ticket.get("status", "unknown")),

        governance_status=governance_status,
        governance_score=safe_int(governance_report.get("governance_score", 0)),

        readiness_status=readiness_status,
        gate_status=str(gate.get("gate_status", "UNKNOWN")),
        allow_decision=bool(gate.get("allow_new_portfolio_decision", False)),
        allow_execution=bool(gate.get("allow_execution_release", False)),

        consistency_status=consistency_status,
        production_ready=bool(readiness_report.get("production_ready", False)),
        research_ready=bool(readiness_report.get("research_ready", False)),
    )


def save_state(state: CanonicalRuntimeState) -> None:
    payload = asdict(state)

    CANONICAL_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM CANONICAL RUNTIME STATE")
    lines.append("=" * 80)

    for key, value in payload.items():
        lines.append(f"{key}: {value}")

    CANONICAL_TXT.write_text("\n".join(lines), encoding="utf-8")


def run_canonical_runtime_state_engine() -> Dict[str, Any]:
    state = build_canonical_state()
    save_state(state)
    return asdict(state)


if __name__ == "__main__":
    state = run_canonical_runtime_state_engine()

    print("=" * 80)
    print("AURUM CANONICAL RUNTIME STATE ENGINE")
    print("=" * 80)
    print(f"Regime: {state['current_regime']}")
    print(f"State: {state['state_label']}")
    print(f"Risk: {state['risk_level']}")
    print(f"Governance: {state['governance_status']}")
    print(f"Readiness: {state['readiness_status']}")
    print(f"Consistency: {state['consistency_status']}")
    print(f"Allow Execution: {state['allow_execution']}")
    print(f"Saved: {CANONICAL_JSON}")
    print(f"Saved: {CANONICAL_TXT}")