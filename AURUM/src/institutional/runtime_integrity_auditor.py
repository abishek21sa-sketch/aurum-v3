from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


STREAMS = [
    "market_ticks",
    "market_features",
    "market_signals",
    "risk_events",
    "optimizer_events",
    "portfolio_decisions",
    "execution_orders",
    "trade_tickets",
    "alerts",
]


@dataclass
class IntegrityFinding:
    check: str
    status: str
    severity: str
    message: str
    evidence: Dict[str, Any]


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


class RuntimeIntegrityAuditor:
    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self.redis_url = redis_url
        self.findings: list[IntegrityFinding] = []

    def add(
        self,
        check: str,
        status: str,
        severity: str,
        message: str,
        evidence: Dict[str, Any],
    ) -> None:
        self.findings.append(
            IntegrityFinding(
                check=check,
                status=status,
                severity=severity,
                message=message,
                evidence=evidence,
            )
        )

    def redis_client(self):
        import redis

        return redis.Redis.from_url(self.redis_url, decode_responses=True)

    def latest_event(self, client, stream: str) -> Dict[str, Any]:
        rows = client.xrevrange(stream, count=1)
        if not rows:
            return {}

        return rows[0][1]

    def stream_lengths(self, client) -> Dict[str, int]:
        lengths = {}
        for stream in STREAMS:
            try:
                lengths[stream] = int(client.xlen(stream))
            except Exception:
                lengths[stream] = 0
        return lengths

    def audit_stream_presence(self, lengths: Dict[str, int]) -> None:
        for stream, length in lengths.items():
            if length > 0:
                self.add(
                    "stream_presence",
                    "PASS",
                    "info",
                    f"{stream} is active.",
                    {"stream": stream, "length": length},
                )
            else:
                self.add(
                    "stream_presence",
                    "FAIL",
                    "critical",
                    f"{stream} is missing or empty.",
                    {"stream": stream, "length": length},
                )

    def audit_freshness(self, events: Dict[str, Dict[str, Any]]) -> None:
        now = datetime.now(timezone.utc)

        freshness_rules = {
            "market_ticks": 300,
            "market_features": 300,
            "market_signals": 600,
            "risk_events": 600,
            "optimizer_events": 3600,
            "portfolio_decisions": 3600,
            "execution_orders": 3600,
            "trade_tickets": 3600,
            "alerts": 3600,
        }

        timestamp_keys = [
            "timestamp_utc",
            "timestamp",
            "computed_at",
            "ingested_at",
        ]

        for stream, event in events.items():
            found_dt = None
            found_key = None

            for key in timestamp_keys:
                if key in event:
                    found_dt = parse_dt(event.get(key))
                    found_key = key
                    if found_dt:
                        break

            if not found_dt:
                self.add(
                    "freshness",
                    "FAIL",
                    "high",
                    f"{stream} has no parseable timestamp.",
                    {"stream": stream, "event": event},
                )
                continue

            age_seconds = (now - found_dt).total_seconds()
            max_age = freshness_rules.get(stream, 3600)

            if age_seconds <= max_age:
                self.add(
                    "freshness",
                    "PASS",
                    "info",
                    f"{stream} is fresh.",
                    {
                        "stream": stream,
                        "timestamp_key": found_key,
                        "age_seconds": round(age_seconds, 2),
                        "max_allowed_seconds": max_age,
                    },
                )
            else:
                self.add(
                    "freshness",
                    "FAIL",
                    "critical" if stream in ["market_ticks", "market_features"] else "high",
                    f"{stream} is stale.",
                    {
                        "stream": stream,
                        "timestamp_key": found_key,
                        "age_seconds": round(age_seconds, 2),
                        "max_allowed_seconds": max_age,
                    },
                )

    def audit_source_quality(self, events: Dict[str, Dict[str, Any]]) -> None:
        tick = events.get("market_ticks", {})
        raw = str(tick.get("raw", "")).lower()
        source = str(tick.get("source", "")).lower()

        if "synthetic" in raw or source in {"demo", "synthetic", "test"}:
            self.add(
                "source_quality",
                "FAIL",
                "high",
                "Latest market tick appears to be demo/synthetic data.",
                {"source": source, "raw": raw[:500]},
            )
        else:
            self.add(
                "source_quality",
                "PASS",
                "info",
                "Latest market tick source appears production-like.",
                {"source": source, "raw": raw[:500]},
            )

    def audit_regime_decision_consistency(self, events: Dict[str, Dict[str, Any]]) -> None:
        signal = events.get("market_signals", {})
        decision = events.get("portfolio_decisions", {})

        signal_regime = str(signal.get("current_regime", "")).lower()
        decision_regime = str(decision.get("current_regime", "")).lower()
        action = str(decision.get("action", "")).lower()
        risk_level = str(decision.get("risk_level", "")).lower()
        state_label = str(signal.get("state_label", "")).lower()

        inconsistent = False
        reasons = []

        if signal_regime and decision_regime and signal_regime != decision_regime:
            inconsistent = True
            reasons.append("market signal regime differs from portfolio decision regime")

        if state_label == "critical" and action in {"hold", "risk_on_rotation", "increase_risk"}:
            inconsistent = True
            reasons.append("critical state produced non-defensive action")

        if risk_level == "critical" and "risk_off" not in action and "reduce" not in action:
            inconsistent = True
            reasons.append("critical risk did not produce risk-off/reduction action")

        if inconsistent:
            self.add(
                "regime_decision_consistency",
                "FAIL",
                "critical",
                "; ".join(reasons),
                {
                    "signal_regime": signal_regime,
                    "decision_regime": decision_regime,
                    "state_label": state_label,
                    "risk_level": risk_level,
                    "action": action,
                },
            )
        else:
            self.add(
                "regime_decision_consistency",
                "PASS",
                "info",
                "Market state and portfolio decision are consistent.",
                {
                    "signal_regime": signal_regime,
                    "decision_regime": decision_regime,
                    "state_label": state_label,
                    "risk_level": risk_level,
                    "action": action,
                },
            )

    def audit_timestamp_order(self, events: Dict[str, Dict[str, Any]]) -> None:
        order = [
            "market_signals",
            "risk_events",
            "optimizer_events",
            "portfolio_decisions",
            "execution_orders",
            "trade_tickets",
        ]

        extracted = {}

        for stream in order:
            event = events.get(stream, {})
            dt = (
                parse_dt(event.get("timestamp_utc"))
                or parse_dt(event.get("timestamp"))
                or parse_dt(event.get("computed_at"))
                or parse_dt(event.get("ingested_at"))
            )
            extracted[stream] = dt.isoformat() if dt else None

        parsed = {k: parse_dt(v) for k, v in extracted.items() if v}

        violations = []

        for earlier, later in zip(order, order[1:]):
            if earlier in parsed and later in parsed and parsed[later] < parsed[earlier]:
                violations.append(f"{later} is older than {earlier}")

        if violations:
            self.add(
                "timestamp_order",
                "FAIL",
                "high",
                "; ".join(violations),
                extracted,
            )
        else:
            self.add(
                "timestamp_order",
                "PASS",
                "info",
                "Runtime event timestamps are in acceptable order.",
                extracted,
            )

    def audit_decision_traceability(self, events: Dict[str, Dict[str, Any]]) -> None:
        decision = events.get("portfolio_decisions", {})
        required_fields = [
            "action",
            "urgency",
            "should_optimize",
            "current_regime",
            "recommended_posture",
            "risk_level",
            "projected_var_95",
            "projected_cvar_95",
            "projected_drawdown",
            "recommended_changes",
            "reason",
        ]

        missing = [field for field in required_fields if field not in decision]

        if missing:
            self.add(
                "decision_traceability",
                "FAIL",
                "high",
                "Portfolio decision is missing required traceability fields.",
                {"missing_fields": missing, "decision": decision},
            )
        else:
            self.add(
                "decision_traceability",
                "PASS",
                "info",
                "Portfolio decision contains required traceability fields.",
                {"fields": required_fields},
            )

    def audit_execution_lifecycle(self, events: Dict[str, Dict[str, Any]]) -> None:
        order = events.get("execution_orders", {})
        ticket = events.get("trade_tickets", {})

        order_payload = order.get("payload")
        ticket_payload = ticket.get("payload")

        try:
            order_data = json.loads(order_payload) if order_payload else order
        except Exception:
            order_data = order

        try:
            ticket_data = json.loads(ticket_payload) if ticket_payload else ticket
        except Exception:
            ticket_data = ticket

        order_id = order_data.get("order_id")
        ticket_order_id = ticket_data.get("order_id")
        ticker_match = order_data.get("ticker") == ticket_data.get("ticker")
        action_match = order_data.get("action") == ticket_data.get("action")

        if order_id and ticket_order_id == order_id and ticker_match and action_match:
            self.add(
                "execution_lifecycle",
                "PASS",
                "info",
                "Execution order is linked to matching trade ticket.",
                {
                    "order_id": order_id,
                    "ticket_order_id": ticket_order_id,
                    "ticker_match": ticker_match,
                    "action_match": action_match,
                },
            )
        else:
            self.add(
                "execution_lifecycle",
                "FAIL",
                "critical",
                "Execution order is not cleanly linked to latest trade ticket.",
                {
                    "order_id": order_id,
                    "ticket_order_id": ticket_order_id,
                    "order": order_data,
                    "ticket": ticket_data,
                },
            )

    def run(self) -> Dict[str, Any]:
        try:
            client = self.redis_client()
            client.ping()
        except Exception as exc:
            self.add(
                "redis_connection",
                "FAIL",
                "critical",
                "Redis is unavailable.",
                {"error": str(exc)},
            )
            return self.build_report({})

        lengths = self.stream_lengths(client)
        events = {stream: self.latest_event(client, stream) for stream in STREAMS}

        self.add(
            "redis_connection",
            "PASS",
            "info",
            "Redis connection established.",
            {"redis_url": self.redis_url},
        )

        self.audit_stream_presence(lengths)
        self.audit_freshness(events)
        self.audit_source_quality(events)
        self.audit_regime_decision_consistency(events)
        self.audit_timestamp_order(events)
        self.audit_decision_traceability(events)
        self.audit_execution_lifecycle(events)

        return self.build_report(events)

    def build_report(self, events: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        findings = [asdict(f) for f in self.findings]

        critical = [f for f in findings if f["status"] == "FAIL" and f["severity"] == "critical"]
        high = [f for f in findings if f["status"] == "FAIL" and f["severity"] == "high"]

        if critical:
            readiness = "NOT_READY"
        elif high:
            readiness = "CONDITIONALLY_READY"
        else:
            readiness = "READY"

        report = {
            "platform": "AURUM",
            "phase": "Phase 4G",
            "layer": "Institutional Runtime Integrity",
            "readiness_status": readiness,
            "finding_count": len(findings),
            "critical_failures": len(critical),
            "high_failures": len(high),
            "findings": findings,
            "latest_events": events,
        }

        output_json = RESULTS_DIR / "runtime_integrity_audit.json"
        output_txt = RESULTS_DIR / "runtime_integrity_audit.txt"

        with output_json.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM RUNTIME INTEGRITY AUDIT")
        lines.append("=" * 80)
        lines.append(f"Readiness Status: {readiness}")
        lines.append(f"Findings: {len(findings)}")
        lines.append(f"Critical Failures: {len(critical)}")
        lines.append(f"High Failures: {len(high)}")
        lines.append("")
        lines.append("FINDINGS")
        lines.append("-" * 80)

        for finding in findings:
            lines.append(
                f"[{finding['status']}] "
                f"{finding['severity'].upper()} | "
                f"{finding['check']} | "
                f"{finding['message']}"
            )

        output_txt.write_text("\n".join(lines), encoding="utf-8")

        return report


def run_runtime_integrity_audit() -> Dict[str, Any]:
    auditor = RuntimeIntegrityAuditor()
    return auditor.run()


if __name__ == "__main__":
    result = run_runtime_integrity_audit()
    print("=" * 80)
    print("AURUM RUNTIME INTEGRITY AUDIT")
    print("=" * 80)
    print(f"Readiness Status: {result['readiness_status']}")
    print(f"Critical Failures: {result['critical_failures']}")
    print(f"High Failures: {result['high_failures']}")
    print("Saved: results/institutional/runtime_integrity_audit.json")
    print("Saved: results/institutional/runtime_integrity_audit.txt")