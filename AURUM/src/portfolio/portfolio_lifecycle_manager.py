# src/portfolio/portfolio_lifecycle_manager.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

STREAMS = {
    "market_signals": "market_signals",
    "risk_events": "risk_events",
    "portfolio_decisions": "portfolio_decisions",
    "execution_reports": "execution_reports",
    "live_positions": "live_positions",
    "institutional_portfolio_state": "institutional_portfolio_state",
}

PORTFOLIO_ID = "AURUM_LIVE_PORTFOLIO"

OUTPUT_DIR = Path("results/portfolio")
EXECUTION_DIR = Path("results/execution")
OPTIMIZATION_DIR = Path("results/optimization")
STATE_DIR = Path("results/portfolio/state")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

INSTITUTIONAL_STATE_PATH = OUTPUT_DIR / "institutional_portfolio_state.json"
LIFECYCLE_SUMMARY_PATH = OUTPUT_DIR / "portfolio_lifecycle_summary.json"


@dataclass
class InstitutionalPortfolioState:
    timestamp: str
    portfolio_id: str

    market_state: Dict[str, Any]
    risk_state: Dict[str, Any]
    decision_state: Dict[str, Any]
    optimization_state: Dict[str, Any]
    execution_state: Dict[str, Any]
    position_state: Dict[str, Any]
    performance_state: Dict[str, Any]
    governance_state: Dict[str, Any]

    lifecycle_status: str
    state_version: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def latest_stream_payload(stream_name: str) -> Optional[Dict[str, Any]]:
    try:
        r = get_redis_client()
        entries = r.xrevrange(stream_name, count=1)

        if not entries:
            return None

        _, fields = entries[0]
        payload = fields.get("payload")

        if payload:
            return json.loads(payload)

        return dict(fields)

    except Exception:
        return None


def load_latest_market_state() -> Dict[str, Any]:
    payload = latest_stream_payload(STREAMS["market_signals"])

    if payload:
        return {
            "source": "redis",
            "event_type": payload.get("event_type", "market_signal"),
            "regime": payload.get("regime")
            or payload.get("current_regime")
            or payload.get("market_regime")
            or "unknown",
            "state_label": payload.get("state_label", "unknown"),
            "stress_score": payload.get("market_stress_score")
            or payload.get("stress_score")
            or 0.0,
            "raw": payload,
        }

    return {
        "source": "fallback",
        "regime": "unknown",
        "state_label": "unknown",
        "stress_score": 0.0,
        "raw": {},
    }


def load_latest_risk_state() -> Dict[str, Any]:
    payload = latest_stream_payload(STREAMS["risk_events"])

    if payload:
        return {
            "source": "redis",
            "event_type": payload.get("event_type", "risk_event"),
            "risk_level": payload.get("risk_level")
            or payload.get("state_label")
            or "unknown",
            "var_95": payload.get("projected_var_95")
            or payload.get("var_95")
            or payload.get("VaR_95"),
            "cvar_95": payload.get("projected_cvar_95")
            or payload.get("cvar_95")
            or payload.get("CVaR_95"),
            "drawdown": payload.get("projected_drawdown")
            or payload.get("drawdown"),
            "raw": payload,
        }

    return {
        "source": "fallback",
        "risk_level": "unknown",
        "var_95": None,
        "cvar_95": None,
        "drawdown": None,
        "raw": {},
    }


def load_latest_decision_state() -> Dict[str, Any]:
    payload = latest_stream_payload(STREAMS["portfolio_decisions"])

    if payload:
        return {
            "source": "redis",
            "decision": payload.get("decision")
            or payload.get("portfolio_decision")
            or payload.get("action")
            or "unknown",
            "confidence": payload.get("confidence")
            or payload.get("decision_confidence")
            or 0.0,
            "reason": payload.get("reason")
            or payload.get("explanation")
            or "Latest portfolio decision from Redis.",
            "raw": payload,
        }

    return {
        "source": "fallback",
        "decision": "unknown",
        "confidence": 0.0,
        "reason": "No portfolio decision available.",
        "raw": {},
    }


def load_optimization_state() -> Dict[str, Any]:
    candidates = [
        OPTIMIZATION_DIR / "realtime_optimized_portfolio.json",
        OPTIMIZATION_DIR / "regime_allocation_policy.json",
        OPTIMIZATION_DIR / "final_optimizer_decision_report.json",
        OPTIMIZATION_DIR / "optimizer_report.json",
        OUTPUT_DIR / "target_portfolio.json",
        Path("results/execution/target_portfolio.json"),
    ]

    preferred_weight_keys = [
        "recommended_weights",
        "target_weights",
        "final_recommended_weights",
        "constrained_weights",
        "volatility_targeted_weights",
        "weights",
    ]

    def normalize_cash_key(weights: Dict[str, Any]) -> Dict[str, float]:
        cleaned = {}

        for key, value in weights.items():
            if not isinstance(key, str):
                continue

            try:
                ticker = "CASH" if key.lower() == "cash" else key
                cleaned[ticker] = float(value)
            except Exception:
                continue

        return cleaned

    def extract_weights(data: Dict[str, Any]) -> Dict[str, float]:
        for key in preferred_weight_keys:
            raw = data.get(key, {})
            if isinstance(raw, dict):
                cleaned = normalize_cash_key(raw)
                if cleaned:
                    return cleaned

        return {}

    for path in candidates:
        if not path.exists():
            continue

        data = load_json(path, {})

        if not isinstance(data, dict):
            continue

        weights = extract_weights(data)

        if weights:
            return {
                "source": str(path),
                "target_weights": weights,
                "target_assets": len(weights),
                "optimizer_method": data.get("optimizer", {}).get("method")
                if isinstance(data.get("optimizer"), dict)
                else data.get("selected_optimizer", "unknown"),
                "regime": data.get("regime")
                or data.get("market_regime")
                or data.get("market_conditions", {}).get("regime")
                if isinstance(data.get("market_conditions"), dict)
                else "unknown",
                "execution_summary": data.get("execution_summary", {}),
                "allocation_policy": data.get("allocation_policy", {}),
                "raw": data,
            }

    return {
        "source": "fallback",
        "target_weights": {},
        "target_assets": 0,
        "optimizer_method": "unknown",
        "regime": "unknown",
        "execution_summary": {},
        "allocation_policy": {},
        "raw": {},
    }


def load_execution_state() -> Dict[str, Any]:
    reports = load_json(EXECUTION_DIR / "execution_reports.json", [])

    if not isinstance(reports, list):
        reports = []

    total_requested = sum(float(r.get("requested_pct", 0.0)) for r in reports)
    total_executed = sum(float(r.get("executed_pct", 0.0)) for r in reports)
    total_cost_bps = sum(float(r.get("total_cost_bps", 0.0)) for r in reports)

    status_counts: Dict[str, int] = {}
    for report in reports:
        status = report.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    fill_ratio = total_executed / total_requested if total_requested > 0 else 0.0

    return {
        "source": str(EXECUTION_DIR / "execution_reports.json"),
        "report_count": len(reports),
        "total_requested_pct": round(total_requested, 6),
        "total_executed_pct": round(total_executed, 6),
        "aggregate_fill_ratio": round(fill_ratio, 6),
        "total_execution_cost_bps": round(total_cost_bps, 4),
        "status_counts": status_counts,
        "latest_reports": reports[-5:],
    }


def load_position_state() -> Dict[str, Any]:
    live_positions_path = OUTPUT_DIR / "live_positions.json"
    data = load_json(live_positions_path, {})

    if data:
        positions = data.get("positions", {})

        return {
            "source": str(live_positions_path),
            "positions": positions,
            "gross_exposure": data.get("gross_exposure", 0.0),
            "net_exposure": data.get("net_exposure", 0.0),
            "cash_weight": data.get("cash_weight", 0.0),
            "status": data.get("status", "UNKNOWN"),
            "raw": data,
        }

    return {
        "source": "fallback",
        "positions": {},
        "gross_exposure": 0.0,
        "net_exposure": 0.0,
        "cash_weight": 0.0,
        "status": "UNKNOWN",
        "raw": {},
    }


def compute_performance_state(
    execution_state: Dict[str, Any],
    position_state: Dict[str, Any],
) -> Dict[str, Any]:
    total_cost_bps = float(execution_state.get("total_execution_cost_bps", 0.0))
    realized_pnl_proxy = -total_cost_bps / 10000.0

    cash_weight = float(position_state.get("cash_weight", 0.0))
    gross_exposure = float(position_state.get("gross_exposure", 0.0))

    deployment_ratio = gross_exposure
    dry_powder_ratio = cash_weight

    return {
        "realized_pnl_proxy": round(realized_pnl_proxy, 8),
        "unrealized_pnl_proxy": 0.0,
        "daily_pnl_proxy": round(realized_pnl_proxy, 8),
        "mtd_pnl_proxy": round(realized_pnl_proxy, 8),
        "ytd_pnl_proxy": round(realized_pnl_proxy, 8),
        "deployment_ratio": round(deployment_ratio, 6),
        "dry_powder_ratio": round(dry_powder_ratio, 6),
    }


def compute_governance_state(
    market_state: Dict[str, Any],
    risk_state: Dict[str, Any],
    execution_state: Dict[str, Any],
    position_state: Dict[str, Any],
) -> Dict[str, Any]:
    alerts: List[str] = []

    cash_weight = float(position_state.get("cash_weight", 0.0))
    gross_exposure = float(position_state.get("gross_exposure", 0.0))
    fill_ratio = float(execution_state.get("aggregate_fill_ratio", 0.0))
    stress_score = float(market_state.get("stress_score", 0.0) or 0.0)

    if cash_weight < -0.02:
        alerts.append("NEGATIVE_CASH_BREACH")

    if gross_exposure > 1.10:
        alerts.append("GROSS_EXPOSURE_BREACH")

    if fill_ratio and fill_ratio < 0.90:
        alerts.append("LOW_EXECUTION_FILL_RATIO")

    if stress_score >= 0.80:
        alerts.append("HIGH_MARKET_STRESS")

    risk_level = str(risk_state.get("risk_level", "")).lower()
    if risk_level in {"critical", "high", "breach"}:
        alerts.append("HIGH_RISK_STATE")

    approval_required = bool(alerts)

    return {
        "alerts": alerts,
        "approval_required": approval_required,
        "governance_status": "REVIEW_REQUIRED" if approval_required else "CLEAR",
        "control_count": 5,
    }


def determine_lifecycle_status(
    governance_state: Dict[str, Any],
    execution_state: Dict[str, Any],
    position_state: Dict[str, Any],
) -> str:
    if governance_state.get("approval_required"):
        return "REVIEW_REQUIRED"

    if execution_state.get("report_count", 0) == 0:
        return "AWAITING_EXECUTION"

    if position_state.get("status") != "ACTIVE":
        return "POSITION_EXCEPTION"

    return "ACTIVE"


def publish_institutional_state(state: InstitutionalPortfolioState) -> None:
    r = get_redis_client()
    payload = asdict(state)

    r.xadd(
        STREAMS["institutional_portfolio_state"],
        {
            "event_type": "institutional_portfolio_state",
            "payload": json.dumps(payload),
            "portfolio_id": state.portfolio_id,
            "lifecycle_status": state.lifecycle_status,
            "timestamp": state.timestamp,
        },
    )


def run_portfolio_lifecycle_manager() -> Dict[str, Any]:
    market_state = load_latest_market_state()
    risk_state = load_latest_risk_state()
    decision_state = load_latest_decision_state()
    optimization_state = load_optimization_state()
    execution_state = load_execution_state()
    position_state = load_position_state()

    performance_state = compute_performance_state(
        execution_state=execution_state,
        position_state=position_state,
    )

    governance_state = compute_governance_state(
        market_state=market_state,
        risk_state=risk_state,
        execution_state=execution_state,
        position_state=position_state,
    )

    lifecycle_status = determine_lifecycle_status(
        governance_state=governance_state,
        execution_state=execution_state,
        position_state=position_state,
    )

    state = InstitutionalPortfolioState(
        timestamp=now_utc(),
        portfolio_id=PORTFOLIO_ID,
        market_state=market_state,
        risk_state=risk_state,
        decision_state=decision_state,
        optimization_state=optimization_state,
        execution_state=execution_state,
        position_state=position_state,
        performance_state=performance_state,
        governance_state=governance_state,
        lifecycle_status=lifecycle_status,
        state_version="4D.5",
    )

    state_dict = asdict(state)

    save_json(INSTITUTIONAL_STATE_PATH, state_dict)

    save_json(
        LIFECYCLE_SUMMARY_PATH,
        {
            "timestamp": state.timestamp,
            "portfolio_id": state.portfolio_id,
            "lifecycle_status": lifecycle_status,
            "governance_status": governance_state["governance_status"],
            "alerts": governance_state["alerts"],
            "gross_exposure": position_state.get("gross_exposure", 0.0),
            "cash_weight": position_state.get("cash_weight", 0.0),
            "aggregate_fill_ratio": execution_state.get("aggregate_fill_ratio", 0.0),
            "total_execution_cost_bps": execution_state.get(
                "total_execution_cost_bps", 0.0
            ),
        },
    )

    publish_institutional_state(state)

    return state_dict


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO LIFECYCLE MANAGER")
    print("=" * 80)

    state = run_portfolio_lifecycle_manager()

    print(f"Portfolio ID: {state['portfolio_id']}")
    print(f"Timestamp: {state['timestamp']}")
    print(f"Lifecycle Status: {state['lifecycle_status']}")
    print(f"State Version: {state['state_version']}")
    print("-" * 80)

    print("MARKET / RISK / DECISION")
    print(f"Market Regime: {state['market_state'].get('regime')}")
    print(f"Market Stress: {state['market_state'].get('stress_score')}")
    print(f"Risk Level:    {state['risk_state'].get('risk_level')}")
    print(f"Decision:      {state['decision_state'].get('decision')}")
    print(f"Optimizer Src: {state['optimization_state'].get('source')}")
    print(f"Target Assets: {state['optimization_state'].get('target_assets')}")
    print("-" * 80)

    print("EXECUTION")
    print(f"Reports:       {state['execution_state']['report_count']}")
    print(f"Fill Ratio:    {state['execution_state']['aggregate_fill_ratio']:.2%}")
    print(f"Exec Cost:     {state['execution_state']['total_execution_cost_bps']} bps")
    print("-" * 80)

    print("POSITIONS")
    positions = state["position_state"]["positions"]
    for ticker, weight in positions.items():
        print(f"{ticker:<10} {float(weight):>10.2%}")

    print("-" * 80)
    print("GOVERNANCE")
    print(f"Status: {state['governance_state']['governance_status']}")
    print(f"Alerts: {state['governance_state']['alerts']}")
    print("-" * 80)

    print(f"Saved: {INSTITUTIONAL_STATE_PATH}")
    print(f"Redis stream: {STREAMS['institutional_portfolio_state']}")


if __name__ == "__main__":
    main()