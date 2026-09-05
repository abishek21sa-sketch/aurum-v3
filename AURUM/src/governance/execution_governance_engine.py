from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

GOVERNANCE_EVENTS_STREAM = "governance_events"

STATE_PATH = Path("results/portfolio/institutional_portfolio_state.json")
CANONICAL_RUNTIME_STATE_PATH = Path(
    "results/institutional/latest_institutional_runtime_state.json"
)

OUTPUT_DIR = Path("results/governance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GOVERNANCE_REPORT_PATH = OUTPUT_DIR / "execution_governance_report.json"


@dataclass
class GovernanceViolation:
    rule: str
    observed: float | str
    limit: float | str
    severity: str
    message: str


@dataclass
class GovernanceReport:
    timestamp: str
    portfolio_id: str
    governance_status: str
    governance_score: int
    violations: List[Dict[str, Any]]
    checks_run: int
    state_version: str
    source_of_truth: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_canonical_runtime_summary() -> Dict[str, Any]:
    payload = load_json(CANONICAL_RUNTIME_STATE_PATH, {})
    if not payload:
        return {}

    return payload.get("summary", {}) or {}


def add_violation(
    violations: List[GovernanceViolation],
    rule: str,
    observed: float | str,
    limit: float | str,
    severity: str,
    message: str,
) -> None:
    violations.append(
        GovernanceViolation(
            rule=rule,
            observed=observed,
            limit=limit,
            severity=severity,
            message=message,
        )
    )


def run_governance_checks(state: Dict[str, Any]) -> GovernanceReport:
    portfolio_id = state.get("portfolio_id", "AURUM_LIVE_PORTFOLIO")

    position_state = state.get("position_state", {})
    execution_state = state.get("execution_state", {})
    risk_state = state.get("risk_state", {})
    market_state = state.get("market_state", {})

    canonical_runtime = load_canonical_runtime_summary()

    violations: List[GovernanceViolation] = []

    gross_exposure = float(position_state.get("gross_exposure", 0.0) or 0.0)
    cash_weight = float(position_state.get("cash_weight", 0.0) or 0.0)
    fill_ratio = float(execution_state.get("aggregate_fill_ratio", 0.0) or 0.0)
    total_cost_bps = float(execution_state.get("total_execution_cost_bps", 0.0) or 0.0)
    report_count = int(execution_state.get("report_count", 0) or 0)
    avg_cost_bps = total_cost_bps / report_count if report_count > 0 else 0.0

    stress_score = float(market_state.get("stress_score", 0.0) or 0.0)
    risk_level = str(risk_state.get("risk_level", "unknown")).lower()
    source_of_truth = "portfolio_state"

    if canonical_runtime:
        if canonical_runtime.get("stress_score") is not None:
            stress_score = float(canonical_runtime.get("stress_score") or 0.0)

        if canonical_runtime.get("risk_level") is not None:
            risk_level = str(canonical_runtime.get("risk_level")).lower()

        source_of_truth = "canonical_institutional_runtime_state"

    if gross_exposure > 1.10:
        add_violation(
            violations,
            "gross_exposure_limit",
            gross_exposure,
            1.10,
            "HIGH",
            "Gross exposure exceeds institutional limit.",
        )

    if cash_weight < 0.05:
        add_violation(
            violations,
            "minimum_cash_weight",
            cash_weight,
            0.05,
            "MEDIUM",
            "Cash weight below minimum liquidity buffer.",
        )

    if fill_ratio < 0.90:
        add_violation(
            violations,
            "execution_fill_rate",
            fill_ratio,
            0.90,
            "HIGH",
            "Execution fill ratio below minimum threshold.",
        )

    if avg_cost_bps > 25.0:
        add_violation(
            violations,
            "average_execution_cost",
            avg_cost_bps,
            25.0,
            "MEDIUM",
            "Average execution cost exceeds threshold.",
        )

    if stress_score >= 0.80:
        add_violation(
            violations,
            "market_stress_limit",
            stress_score,
            0.80,
            "HIGH",
            "Market stress score requires review.",
        )

    if risk_level in {"high", "critical", "breach"}:
        add_violation(
            violations,
            "risk_state_limit",
            risk_level,
            "not high/critical/breach",
            "HIGH",
            "Risk state requires governance review.",
        )

    severity_penalty = {
        "LOW": 5,
        "MEDIUM": 15,
        "HIGH": 30,
        "CRITICAL": 50,
    }

    score = 100

    for violation in violations:
        score -= severity_penalty.get(violation.severity, 10)

    score = max(score, 0)

    if any(v.severity in {"HIGH", "CRITICAL"} for v in violations):
        status = "REVIEW_REQUIRED"
    elif violations:
        status = "WARNING"
    else:
        status = "CLEAR"

    return GovernanceReport(
        timestamp=now_utc(),
        portfolio_id=portfolio_id,
        governance_status=status,
        governance_score=score,
        violations=[asdict(v) for v in violations],
        checks_run=6,
        state_version=state.get("state_version", "unknown"),
        source_of_truth=source_of_truth,
    )


def publish_governance_report(report: GovernanceReport) -> None:
    r = get_redis_client()
    payload = asdict(report)

    r.xadd(
        GOVERNANCE_EVENTS_STREAM,
        {
            "event_type": "governance_report",
            "payload": json.dumps(payload),
            "portfolio_id": report.portfolio_id,
            "governance_status": report.governance_status,
            "governance_score": str(report.governance_score),
            "source_of_truth": report.source_of_truth,
            "timestamp": report.timestamp,
        },
    )


def run_execution_governance_engine() -> Dict[str, Any]:
    state = load_json(STATE_PATH, {})
    report = run_governance_checks(state)
    report_dict = asdict(report)

    save_json(GOVERNANCE_REPORT_PATH, report_dict)
    publish_governance_report(report)

    return report_dict


def main() -> None:
    print("=" * 80)
    print("AURUM EXECUTION GOVERNANCE ENGINE")
    print("=" * 80)

    report = run_execution_governance_engine()

    print(f"Portfolio ID: {report['portfolio_id']}")
    print(f"Governance Status: {report['governance_status']}")
    print(f"Governance Score: {report['governance_score']}")
    print(f"Source of Truth: {report['source_of_truth']}")
    print(f"Violations: {len(report['violations'])}")
    print("-" * 80)

    for violation in report["violations"]:
        print(
            f"[{violation['severity']}] {violation['rule']} | "
            f"observed={violation['observed']} limit={violation['limit']}"
        )

    print("-" * 80)
    print(f"Saved: {GOVERNANCE_REPORT_PATH}")
    print(f"Redis stream: {GOVERNANCE_EVENTS_STREAM}")


if __name__ == "__main__":
    main()