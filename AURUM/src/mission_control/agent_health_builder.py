"""
AURUM Mission Control
Agent Health Builder

Output:
    results/mission_control/agent_health.json

Run:
    python -m src.mission_control.agent_health_builder
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MISSION_DIR = ROOT / "results" / "mission_control"

AGENT_ACTIVITY_PATH = MISSION_DIR / "agent_activity.jsonl"
AGENT_HEALTH_PATH = MISSION_DIR / "agent_health.json"


EXPECTED_AGENTS = [
    "Market Data Agent",
    "Regime Agent",
    "Portfolio Agent",
    "Risk Agent",
    "Anomaly Agent",
    "CIO Agent",
    "Governance Agent",
    "System Health Agent",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                events.append(json.loads(line))
            except Exception:
                pass

    return events


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_agent_health() -> dict[str, Any]:
    events = read_jsonl(AGENT_ACTIVITY_PATH)

    latest_by_agent: dict[str, dict[str, Any]] = {}

    for event in events:
        agent = event.get("agent")
        if agent:
            latest_by_agent[agent] = event

    agents = {}

    for agent in EXPECTED_AGENTS:
        latest = latest_by_agent.get(agent, {})
        severity = latest.get("severity", "unknown")
        message = latest.get("message", "No recent event found.")
        last_seen = latest.get("timestamp")

        if not latest:
            status = "inactive"
        elif severity in {"critical", "error"}:
            status = "attention"
        else:
            status = "active"

        agents[agent] = {
            "agent": agent,
            "status": status,
            "last_seen": last_seen,
            "last_severity": severity,
            "last_message": message,
        }

    active_count = sum(1 for a in agents.values() if a["status"] == "active")
    attention_count = sum(1 for a in agents.values() if a["status"] == "attention")
    inactive_count = sum(1 for a in agents.values() if a["status"] == "inactive")

    overall = "healthy"
    if attention_count > 0:
        overall = "attention_required"
    if inactive_count > 0:
        overall = "degraded"

    payload = {
        "timestamp": utc_now(),
        "overall_agent_health": overall,
        "active_agents": active_count,
        "attention_agents": attention_count,
        "inactive_agents": inactive_count,
        "agents": agents,
    }

    write_json(AGENT_HEALTH_PATH, payload)
    return payload


def main() -> None:
    health = build_agent_health()

    print("=" * 80)
    print("AURUM AGENT HEALTH")
    print("=" * 80)
    print(f"Saved: {AGENT_HEALTH_PATH.relative_to(ROOT)}")
    print(f"Overall:   {health.get('overall_agent_health')}")
    print(f"Active:    {health.get('active_agents')}")
    print(f"Attention: {health.get('attention_agents')}")
    print(f"Inactive:  {health.get('inactive_agents')}")
    print("=" * 80)


if __name__ == "__main__":
    main()