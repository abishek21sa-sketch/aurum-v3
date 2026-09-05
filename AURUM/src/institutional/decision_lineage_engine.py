from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import redis


REDIS_URL = "redis://localhost:6379/0"

OUTPUT_DIR = Path("results/institutional")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "decision_lineage.json"
OUTPUT_TXT = OUTPUT_DIR / "decision_lineage.txt"


LINEAGE_STREAMS = {
    "market_signal": ("market_signals", "live_digital_twin_state"),
    "risk_projection": ("risk_events", "risk_projection"),
    "portfolio_decision": ("portfolio_decisions", "portfolio_decision"),
    "execution_order": ("execution_orders", "execution_order"),
    "trade_ticket": ("trade_tickets", "trade_ticket"),
    "governance": ("governance_events", "governance_report"),
}


STATIC_ARTIFACTS = {
    "canonical_runtime_state": Path("results/institutional/canonical_runtime_state.json"),
    "readiness_report": Path("results/institutional/institutional_readiness_report.json"),
    "decision_explanation": Path("results/institutional/decision_explanation.json"),
    "coherence_gate": Path("results/institutional/runtime_coherence_gate.json"),
    "governance_report": Path("results/governance/execution_governance_report.json"),
    "mars_cvar_decision": Path("results/institutional/mars_cvar_decision.json"),
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def decode_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    decoded = {}

    for key, value in event.items():
        try:
            decoded[key] = json.loads(value)
        except Exception:
            decoded[key] = value

    if "payload" in decoded and isinstance(decoded["payload"], str):
        try:
            payload = json.loads(decoded["payload"])
            if isinstance(payload, dict):
                decoded.update(payload)
        except Exception:
            pass

    return decoded


def latest_stream_event(
    client: redis.Redis,
    stream: str,
    event_type: Optional[str],
    lookback: int = 100,
) -> Dict[str, Any]:
    try:
        rows = client.xrevrange(stream, count=lookback)
    except Exception:
        return {}

    for redis_id, raw_event in rows:
        event = decode_payload(raw_event)

        if event_type is None or event.get("event_type") == event_type:
            event["_redis_stream"] = stream
            event["_redis_id"] = redis_id
            return event

    return {}


def event_timestamp(event: Dict[str, Any]) -> str:
    for key in ["timestamp_utc", "timestamp", "computed_at", "ingested_at"]:
        if event.get(key):
            return str(event[key])
    return ""


def short_event_summary(event: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "event_type",
        "current_regime",
        "state_label",
        "market_stress_score",
        "risk_level",
        "projected_var_95",
        "projected_cvar_95",
        "projected_drawdown",
        "action",
        "recommended_posture",
        "reason",
        "ticker",
        "priority",
        "status",
        "governance_status",
        "governance_score",
    ]

    return {
        key: event.get(key)
        for key in keys
        if key in event
    }


def build_chain_id(parts: Dict[str, Any]) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"AURUM-CHAIN-{digest}"


def evaluate_lineage_quality(nodes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    missing_nodes = [
        name
        for name, payload in nodes.items()
        if not payload.get("present")
    ]

    if missing_nodes:
        status = "INCOMPLETE"
    else:
        status = "COMPLETE"

    timestamps = {
        name: payload.get("timestamp")
        for name, payload in nodes.items()
        if payload.get("timestamp")
    }

    return {
        "lineage_status": status,
        "missing_nodes": missing_nodes,
        "timestamp_count": len(timestamps),
    }


def generate_decision_lineage() -> Dict[str, Any]:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    stream_nodes: Dict[str, Dict[str, Any]] = {}

    for node_name, (stream, event_type) in LINEAGE_STREAMS.items():
        event = latest_stream_event(client, stream, event_type)

        stream_nodes[node_name] = {
            "present": bool(event),
            "source": stream,
            "event_type": event_type,
            "redis_id": event.get("_redis_id"),
            "timestamp": event_timestamp(event),
            "summary": short_event_summary(event),
            "raw_event": event,
        }

    artifacts = {
        name: load_json(path)
        for name, path in STATIC_ARTIFACTS.items()
    }

    chain_seed = {
        "market_signal_id": stream_nodes["market_signal"].get("redis_id"),
        "risk_projection_id": stream_nodes["risk_projection"].get("redis_id"),
        "portfolio_decision_id": stream_nodes["portfolio_decision"].get("redis_id"),
        "execution_order_id": stream_nodes["execution_order"].get("redis_id"),
        "trade_ticket_id": stream_nodes["trade_ticket"].get("redis_id"),
        "governance_id": stream_nodes["governance"].get("redis_id"),
        "decision": artifacts.get("decision_explanation", {}).get("decision"),
    }

    chain_id = build_chain_id(chain_seed)
    quality = evaluate_lineage_quality(stream_nodes)

    lineage = {
        "platform": "AURUM",
        "phase": "Phase 4L",
        "module": "Decision Lineage Engine",
        "generated_at": now_utc(),
        "decision_chain_id": chain_id,
        "lineage_quality": quality,
        "chain_seed": chain_seed,
        "nodes": stream_nodes,
        "artifacts": {
            "canonical_runtime_state": {
                "present": bool(artifacts["canonical_runtime_state"]),
                "summary": artifacts["canonical_runtime_state"],
            },
            "readiness_report": {
                "present": bool(artifacts["readiness_report"]),
                "overall_status": artifacts["readiness_report"].get("overall_status"),
                "platform_score": artifacts["readiness_report"].get("platform_score"),
                "research_ready": artifacts["readiness_report"].get("research_ready"),
                "production_ready": artifacts["readiness_report"].get("production_ready"),
            },
            "decision_explanation": {
                "present": bool(artifacts["decision_explanation"]),
                "decision": artifacts["decision_explanation"].get("decision"),
                "confidence": artifacts["decision_explanation"].get("confidence"),
                "institutional_summary": artifacts["decision_explanation"].get(
                    "institutional_summary"
                ),
            },
            "coherence_gate": {
                "present": bool(artifacts["coherence_gate"]),
                "gate_status": artifacts["coherence_gate"].get("gate_status"),
                "allow_decision": artifacts["coherence_gate"].get(
                    "allow_new_portfolio_decision"
                ),
                "allow_execution": artifacts["coherence_gate"].get(
                    "allow_execution_release"
                ),
            },
            "mars_cvar_decision": {
                "present": bool(artifacts["mars_cvar_decision"]),
                "decision_id": artifacts["mars_cvar_decision"].get("decision_id"),
                "authorized": artifacts["mars_cvar_decision"].get("authorized"),
                "cvar_loss": artifacts["mars_cvar_decision"].get("cvar_loss"),
                "turnover": artifacts["mars_cvar_decision"].get("turnover"),
            },
            "governance_report": {
                "present": bool(artifacts["governance_report"]),
                "governance_status": artifacts["governance_report"].get(
                    "governance_status"
                ),
                "governance_score": artifacts["governance_report"].get(
                    "governance_score"
                ),
            },
        },
    }

    save_lineage(lineage)
    return lineage


def save_lineage(lineage: Dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(json.dumps(lineage, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM DECISION LINEAGE")
    lines.append("=" * 80)
    lines.append(f"Decision Chain ID: {lineage['decision_chain_id']}")
    lines.append(f"Lineage Status: {lineage['lineage_quality']['lineage_status']}")
    lines.append(f"Generated At: {lineage['generated_at']}")
    lines.append("")

    lines.append("CHAIN NODES")
    lines.append("-" * 80)

    for name, node in lineage["nodes"].items():
        lines.append(
            f"{name}: present={node['present']} | "
            f"stream={node['source']} | "
            f"redis_id={node.get('redis_id')} | "
            f"timestamp={node.get('timestamp')}"
        )
        lines.append(f"  summary={node.get('summary')}")
        lines.append("")

    lines.append("ARTIFACTS")
    lines.append("-" * 80)

    for name, artifact in lineage["artifacts"].items():
        lines.append(f"{name}: present={artifact.get('present')}")

    explanation = lineage["artifacts"]["decision_explanation"]

    lines.append("")
    lines.append("DECISION EXPLANATION")
    lines.append("-" * 80)
    lines.append(f"Decision: {explanation.get('decision')}")
    lines.append(f"Confidence: {explanation.get('confidence')}")
    lines.append(f"Summary: {explanation.get('institutional_summary')}")

    gate = lineage["artifacts"]["coherence_gate"]

    lines.append("")
    lines.append("EXECUTION PERMISSION")
    lines.append("-" * 80)
    lines.append(f"Gate Status: {gate.get('gate_status')}")
    lines.append(f"Allow Decision: {gate.get('allow_decision')}")
    lines.append(f"Allow Execution: {gate.get('allow_execution')}")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = generate_decision_lineage()

    print("=" * 80)
    print("AURUM DECISION LINEAGE ENGINE")
    print("=" * 80)
    print(f"Decision Chain ID: {result['decision_chain_id']}")
    print(f"Lineage Status: {result['lineage_quality']['lineage_status']}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")