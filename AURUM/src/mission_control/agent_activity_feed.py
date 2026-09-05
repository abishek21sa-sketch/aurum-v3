"""
AURUM Mission Control 3
Agent Activity Feed

Purpose:
Creates a live-feeling institutional activity feed from AURUM outputs.

Output:
    results/mission_control/agent_activity.jsonl

Run:
    python -m src.mission_control.agent_activity_feed
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
MISSION_DIR = RESULTS_DIR / "mission_control"

DASHBOARD_STATE_PATH = MISSION_DIR / "dashboard_state.json"
LATEST_REFRESH_PATH = MISSION_DIR / "latest_refresh.json"
AGENT_ACTIVITY_PATH = MISSION_DIR / "agent_activity.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def make_event(
    agent: str,
    event_type: str,
    message: str,
    severity: str = "info",
    timestamp: str | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": timestamp or utc_now(),
        "agent": agent,
        "event_type": event_type,
        "message": message,
        "severity": severity,
    }


def load_existing_events(limit: int = 100) -> list[dict[str, Any]]:
    if not AGENT_ACTIVITY_PATH.exists():
        return []

    events: list[dict[str, Any]] = []
    try:
        lines = AGENT_ACTIVITY_PATH.read_text(encoding="utf-8").splitlines()
        for line in lines[-limit:]:
            if line.strip():
                events.append(json.loads(line))
    except Exception:
        return []

    return events


def event_key(event: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(event.get("agent", "")),
        str(event.get("event_type", "")),
        str(event.get("message", "")),
    )


def generate_activity_events() -> list[dict[str, Any]]:
    dashboard_state = read_json(DASHBOARD_STATE_PATH, {})
    latest_refresh = read_json(LATEST_REFRESH_PATH, {})

    status = dashboard_state.get("status", {})
    mission = dashboard_state.get("mission_control", {})
    risk_regime = dashboard_state.get("risk_regime", {})
    live_markets = dashboard_state.get("live_markets", [])
    system_health = dashboard_state.get("system_health", {})

    timestamp = utc_now()
    events: list[dict[str, Any]] = []

    market_data_status = status.get("market_data_status") or latest_refresh.get("market_data_status")
    market_count = len(live_markets) if isinstance(live_markets, list) else 0

    if market_data_status == "fresh":
        events.append(
            make_event(
                "Market Data Agent",
                "market_refresh",
                f"Live market data refreshed successfully for {market_count} assets.",
                "success",
                timestamp,
            )
        )
    elif market_data_status in {"aging", "stale"}:
        events.append(
            make_event(
                "Market Data Agent",
                "market_refresh",
                f"Market data is {market_data_status}; refresh may be needed.",
                "warning",
                timestamp,
            )
        )
    else:
        events.append(
            make_event(
                "Market Data Agent",
                "market_refresh",
                "Market data status is unavailable.",
                "warning",
                timestamp,
            )
        )

    regime = mission.get("current_regime", "unknown")
    events.append(
        make_event(
            "Regime Agent",
            "regime_update",
            f"Regime Agent updated market state to {regime}.",
            "info" if regime != "unknown" else "warning",
            timestamp,
        )
    )

    posture = mission.get("portfolio_posture", "unknown")
    events.append(
        make_event(
            "Portfolio Agent",
            "posture_update",
            f"Portfolio posture is currently {posture}.",
            "info" if posture != "unknown" else "warning",
            timestamp,
        )
    )

    biggest_risk = mission.get("biggest_risk", "No dominant risk identified yet")
    severity = "warning" if biggest_risk and biggest_risk != "No dominant risk identified yet" else "info"
    events.append(
        make_event(
            "Risk Agent",
            "risk_update",
            f"Biggest active risk: {biggest_risk}.",
            severity,
            timestamp,
        )
    )

    cvar = risk_regime.get("cvar")
    if cvar is not None:
        events.append(
            make_event(
                "Risk Agent",
                "tail_risk_update",
                f"CVaR metric updated to {cvar}.",
                "warning",
                timestamp,
            )
        )

    anomalies = risk_regime.get("anomalies", [])
    if isinstance(anomalies, list) and anomalies:
        events.append(
            make_event(
                "Anomaly Agent",
                "anomaly_detected",
                f"Detected {len(anomalies)} anomaly alert(s).",
                "warning",
                timestamp,
            )
        )
    else:
        events.append(
            make_event(
                "Anomaly Agent",
                "anomaly_scan",
                "No active anomaly alerts detected.",
                "success",
                timestamp,
            )
        )

    confidence = mission.get("cio_confidence", 0.0)
    recommended_action = mission.get("recommended_action", "maintain_current_portfolio")
    events.append(
        make_event(
            "CIO Agent",
            "cio_directive",
            f"CIO issued directive: {recommended_action} with confidence {confidence}.",
            "success" if confidence and float(confidence) >= 0.75 else "info",
            timestamp,
        )
    )

    permission = mission.get("execution_permission", "unknown")
    if permission == "blocked":
        events.append(
            make_event(
                "Governance Agent",
                "execution_review",
                "Governance reviewed action and blocked execution.",
                "critical",
                timestamp,
            )
        )
    elif permission == "allowed":
        events.append(
            make_event(
                "Governance Agent",
                "execution_review",
                "Governance reviewed action and allowed execution.",
                "success",
                timestamp,
            )
        )
    else:
        events.append(
            make_event(
                "Governance Agent",
                "execution_review",
                "Execution permission is not yet clear.",
                "warning",
                timestamp,
            )
        )

    redis_status = system_health.get("redis_status", "unknown")
    database_status = system_health.get("database_status", "unknown")
    events.append(
        make_event(
            "System Health Agent",
            "health_check",
            f"System health checked. Redis={redis_status}, Database={database_status}.",
            "info",
            timestamp,
        )
    )

    return events


def update_activity_feed(max_events: int = 200) -> list[dict[str, Any]]:
    """
    Adds new activity events while avoiding exact duplicate spam.
    Keeps the latest max_events lines.
    """
    MISSION_DIR.mkdir(parents=True, exist_ok=True)

    existing = load_existing_events(limit=max_events)

    # Drop events older than 24 hours
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    fresh_existing = []
    for event in existing:
        try:
            ts = event.get("timestamp", "")
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.astimezone(timezone.utc) >= cutoff:
                fresh_existing.append(event)
        except Exception:
            fresh_existing.append(event)

    existing_keys = {event_key(event) for event in fresh_existing}

    new_events = generate_activity_events()

    merged = fresh_existing[:]
    for event in new_events:
        if event_key(event) not in existing_keys:
            merged.append(event)
            existing_keys.add(event_key(event))

    merged = merged[-max_events:]
    write_jsonl(AGENT_ACTIVITY_PATH, merged)
    return merged


def print_summary(events: list[dict[str, Any]]) -> None:
    latest = events[-8:] if len(events) >= 8 else events

    print("=" * 80)
    print("AURUM AGENT ACTIVITY FEED")
    print("=" * 80)
    print(f"Saved: {AGENT_ACTIVITY_PATH.relative_to(ROOT)}")
    print(f"Events: {len(events)}")
    print("-" * 80)

    for event in latest:
        print(
            f"{event.get('timestamp')} | "
            f"{event.get('severity', '').upper():8} | "
            f"{event.get('agent')} | "
            f"{event.get('message')}"
        )

    print("=" * 80)


def main() -> None:
    events = update_activity_feed()
    print_summary(events)


if __name__ == "__main__":
    main()