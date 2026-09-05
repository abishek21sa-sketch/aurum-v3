# scripts/validate_phase4b_realtime_decision_layer.py

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

REQUIRED_STREAMS = {
    "market_signals": ["live_digital_twin_state", "regime_decision"],
    "risk_events": ["risk_projection"],
    "optimizer_events": ["optimizer_trigger"],
    "portfolio_decisions": ["portfolio_decision"],
}


def decode_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    decoded = {}

    for key, value in raw_event.items():
        try:
            decoded[key] = json.loads(value)
        except Exception:
            decoded[key] = value

    return decoded


def latest_event(
    r: redis.Redis,
    stream: str,
    event_type: str,
    lookback: int = 100,
) -> Optional[Dict[str, Any]]:
    rows = r.xrevrange(stream, count=lookback)

    for _, raw_event in rows:
        event = decode_event(raw_event)

        if event.get("event_type") == event_type:
            return event

    return None


def check_required_fields(
    event: Dict[str, Any],
    required_fields: list[str],
) -> list[str]:
    missing = []

    for field in required_fields:
        if field not in event:
            missing.append(field)

    return missing


def main() -> None:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    print("=" * 80)
    print("AURUM PHASE 4B REAL-TIME DECISION LAYER VALIDATION")
    print("=" * 80)

    total_checks = 0
    passed_checks = 0

    def mark_pass(message: str) -> None:
        nonlocal total_checks, passed_checks
        total_checks += 1
        passed_checks += 1
        print(f"[PASS] {message}")

    def mark_fail(message: str) -> None:
        nonlocal total_checks
        total_checks += 1
        print(f"[FAIL] {message}")

    print("\nSTREAM EXISTENCE CHECKS")
    print("-" * 80)

    for stream in REQUIRED_STREAMS:
        length = r.xlen(stream)

        if length > 0:
            mark_pass(f"{stream} active | length={length}")
        else:
            mark_fail(f"{stream} inactive | length=0")

    print("\nEVENT TYPE CHECKS")
    print("-" * 80)

    found_events: Dict[str, Dict[str, Any]] = {}

    for stream, event_types in REQUIRED_STREAMS.items():
        for event_type in event_types:
            event = latest_event(r, stream, event_type)

            if event:
                key = f"{stream}:{event_type}"
                found_events[key] = event
                mark_pass(f"{event_type} found in {stream}")
            else:
                mark_fail(f"{event_type} missing from {stream}")

    print("\nSCHEMA CHECKS")
    print("-" * 80)

    schema_requirements = {
        "market_signals:live_digital_twin_state": [
            "event_type",
            "state_label",
            "market_stress_score",
            "volatility_state",
            "liquidity_state",
            "alert_state",
        ],
        "risk_events:risk_projection": [
            "event_type",
            "projected_var_95",
            "projected_cvar_95",
            "projected_drawdown",
            "risk_level",
        ],
        "market_signals:regime_decision": [
            "event_type",
            "current_regime",
            "confidence",
            "recommended_posture",
            "risk_level",
        ],
        "optimizer_events:optimizer_trigger": [
            "event_type",
            "should_optimize",
            "trigger_reason",
            "urgency",
            "current_regime",
        ],
        "portfolio_decisions:portfolio_decision": [
            "event_type",
            "action",
            "urgency",
            "should_optimize",
            "recommended_changes",
            "reason",
        ],
    }

    for key, fields in schema_requirements.items():
        event = found_events.get(key)

        if not event:
            mark_fail(f"{key} schema skipped because event is missing")
            continue

        missing = check_required_fields(event, fields)

        if not missing:
            mark_pass(f"{key} schema valid")
        else:
            mark_fail(f"{key} missing fields: {missing}")

    print("\nLATEST DECISION SNAPSHOT")
    print("-" * 80)

    decision = found_events.get("portfolio_decisions:portfolio_decision")

    if decision:
        print(f"Action: {decision.get('action')}")
        print(f"Urgency: {decision.get('urgency')}")
        print(f"Should Optimize: {decision.get('should_optimize')}")
        print(f"Current Regime: {decision.get('current_regime')}")
        print(f"Risk Level: {decision.get('risk_level')}")
        print(f"Reason: {decision.get('reason')}")
        print(f"Recommended Changes: {decision.get('recommended_changes')}")

    print("\nSUMMARY")
    print("-" * 80)
    print(f"Passed Checks: {passed_checks}/{total_checks}")

    if passed_checks == total_checks:
        print("[PASS] Phase 4B real-time decision layer is operational.")
    else:
        print("[FAIL] Phase 4B real-time decision layer needs fixes.")


if __name__ == "__main__":
    main()