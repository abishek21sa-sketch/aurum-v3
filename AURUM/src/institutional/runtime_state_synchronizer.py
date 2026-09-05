from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = RESULTS_DIR / "latest_institutional_runtime_state.json"
OUTPUT_TXT = RESULTS_DIR / "latest_institutional_runtime_state.txt"


STREAMS = [
    "market_signals",
    "risk_events",
    "portfolio_decisions",
    "execution_orders",
    "trade_tickets",
    "governance_events",
]


def latest_stream_event(client, stream: str) -> Dict[str, Any]:
    try:
        rows = client.xrevrange(stream, count=1)
        if not rows:
            return {}

        return rows[0][1]
    except Exception:
        return {}


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def extract_runtime_state() -> Dict[str, Any]:
    import redis

    client = redis.Redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True,
    )

    runtime = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "streams": {},
    }

    for stream in STREAMS:
        runtime["streams"][stream] = latest_stream_event(client, stream)

    runtime["governance_report"] = load_json(
        Path("results/governance/execution_governance_report.json")
    )

    runtime["integrity_audit"] = load_json(
        Path("results/institutional/runtime_integrity_audit.json")
    )

    runtime["coherence_gate"] = load_json(
        Path("results/institutional/runtime_coherence_gate.json")
    )

    return runtime


def build_summary(runtime: Dict[str, Any]) -> Dict[str, Any]:
    signal = runtime["streams"].get("market_signals", {})
    risk = runtime["streams"].get("risk_events", {})
    decision = runtime["streams"].get("portfolio_decisions", {})
    governance = runtime.get("governance_report", {})
    gate = runtime.get("coherence_gate", {})

    return {
        "current_regime": signal.get("current_regime"),
        "state_label": signal.get("state_label"),
        "stress_score": signal.get("market_stress_score"),
        "risk_level": risk.get("risk_level"),
        "portfolio_action": decision.get("action"),
        "recommended_posture": decision.get("recommended_posture"),
        "governance_status": governance.get("governance_status"),
        "gate_status": gate.get("gate_status"),
        "allow_execution": gate.get("allow_execution_release"),
    }


def save(runtime: Dict[str, Any], summary: Dict[str, Any]) -> None:
    payload = {
        "runtime_state": runtime,
        "summary": summary,
    }

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM LATEST INSTITUTIONAL RUNTIME STATE")
    lines.append("=" * 80)

    for key, value in summary.items():
        lines.append(f"{key}: {value}")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


def run_runtime_state_synchronizer() -> Dict[str, Any]:
    runtime = extract_runtime_state()
    summary = build_summary(runtime)

    save(runtime, summary)

    return {
        "status": "PASS",
        "summary": summary,
    }


if __name__ == "__main__":
    result = run_runtime_state_synchronizer()

    print("=" * 80)
    print("AURUM RUNTIME STATE SYNCHRONIZER")
    print("=" * 80)

    for k, v in result["summary"].items():
        print(f"{k}: {v}")

    print(f"\nSaved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")