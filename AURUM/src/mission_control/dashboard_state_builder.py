"""
AURUM Mission Control 2
Dashboard State Builder

Purpose:
Converts messy backend outputs into ONE clean dashboard JSON.

The Streamlit website should read only:

    results/mission_control/dashboard_state.json

Run:
    python -m src.mission_control.dashboard_state_builder
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


INPUT_PATHS = {
    "live_market_snapshot": RESULTS_DIR / "realtime" / "live_market_snapshot.json",
    "latest_regime": RESULTS_DIR / "regimes" / "latest_regime.json",
    "latest_anomaly_alerts": RESULTS_DIR / "anomalies" / "latest_anomaly_alerts.json",
    "portfolio_directive": RESULTS_DIR / "portfolio_os" / "portfolio_directive.json",
    "cio_brief": RESULTS_DIR / "cio" / "cio_brief.txt",
    "cio_market_thesis": RESULTS_DIR / "cio" / "cio_market_thesis.json",
    "cio_portfolio_directive": RESULTS_DIR / "cio" / "cio_portfolio_directive.json",
    "ai_research_firm_mode": RESULTS_DIR / "research_firm" / "ai_research_firm_mode.json",
    "daily_institutional_cycle": RESULTS_DIR / "institutional" / "daily_institutional_cycle.json",
    "platform_health_report": RESULTS_DIR / "reliability" / "platform_health_report.json",
    "latest_refresh": MISSION_DIR / "latest_refresh.json",
    "system_status": MISSION_DIR / "system_status.json",
}


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


def read_text(path: Path, default: str = "") -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        return default
    return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def first_value(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return default

def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value:
        if isinstance(value[0], dict):
            return value[0]
    return {}

def nested_get(data: Any, *keys: str, default: Any = None) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default

def normalize_permission(value: Any) -> str:
    if isinstance(value, bool):
        return "allowed" if value else "blocked"

    text = str(value or "").lower()
    if not text:
        return "unknown"

    if "block" in text or "reject" in text or "deny" in text:
        return "blocked"
    if "allow" in text or "clear" in text or "approve" in text:
        return "allowed"
    if "review" in text:
        return "review_required"

    return text


def normalize_posture(value: Any) -> str:
    text = str(value or "").lower()
    if not text:
        return "unknown"
    if "defensive" in text or "reduce" in text or "risk_off" in text:
        return "defensive"
    if "risk-on" in text or "risk_on" in text or "aggressive" in text:
        return "risk_on"
    if "normal" in text or "neutral" in text:
        return "normal"
    return text

def market_records_from_snapshot(snapshot: Any) -> list[dict[str, Any]]:
    """
    Converts live market snapshot into clean market records.

    Important:
    Some snapshots store timestamp/source at the top level, not inside each asset.
    This function pushes global timestamp/source into every row so dashboard does
    not show timestamp=None.
    """
    if not snapshot:
        return []

    global_timestamp = None
    global_source = None

    if isinstance(snapshot, dict):
        global_timestamp = (
            snapshot.get("generated_at")
            or snapshot.get("timestamp")
            or snapshot.get("as_of")
            or snapshot.get("created_at")
        )

        global_source = (
            snapshot.get("source")
            or snapshot.get("provider")
            or "unknown"
        )

        for key in ["records", "data", "market_data", "assets"]:
            value = snapshot.get(key)

            if isinstance(value, list):
                records = []

                for item in value:
                    if isinstance(item, dict):
                        enriched = dict(item)
                        enriched.setdefault("timestamp", global_timestamp)
                        enriched.setdefault("source", global_source)
                        records.append(normalize_market_record(enriched))

                return records

        records = []

        for ticker, value in snapshot.items():
            if isinstance(value, dict):
                item = {"ticker": ticker, **value}
                item.setdefault("timestamp", global_timestamp)
                item.setdefault("source", global_source)

                if "price" in item or "close" in item or "last" in item:
                    records.append(normalize_market_record(item))

        return records

    if isinstance(snapshot, list):
        return [normalize_market_record(x) for x in snapshot if isinstance(x, dict)]

    return []


def normalize_market_record(record: dict[str, Any]) -> dict[str, Any]:
    ticker = first_value(
        record.get("ticker"),
        record.get("symbol"),
        record.get("asset"),
        record.get("name"),
        default="UNKNOWN",
    )

    price = first_value(
        record.get("price"),
        record.get("last"),
        record.get("close"),
        record.get("value"),
        default=None,
    )

    timestamp = first_value(
        record.get("timestamp"),
        record.get("time"),
        record.get("as_of"),
        record.get("generated_at"),
        default=None,
    )

    source = first_value(record.get("source"), record.get("provider"), default="unknown")

    freshness = "available"
    if timestamp:
        try:
            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            age_seconds = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
            if age_seconds <= 15 * 60:
                freshness = "fresh"
            elif age_seconds <= 60 * 60:
                freshness = "aging"
            else:
                freshness = "stale"
        except Exception:
            freshness = "available"

    return {
        "ticker": str(ticker),
        "price": price,
        "timestamp": timestamp,
        "source": source,
        "freshness": freshness,
    }


def extract_anomalies(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        for key in ["alerts", "anomalies", "events", "records"]:
            value = raw.get(key)
            if isinstance(value, list):
                return value

        if raw.get("message") or raw.get("severity"):
            return [raw]

    return []


def build_dashboard_state() -> dict[str, Any]:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)

    live_market_snapshot = read_json(INPUT_PATHS["live_market_snapshot"], {})
    latest_regime = read_json(INPUT_PATHS["latest_regime"], {})
    latest_anomaly_alerts = read_json(INPUT_PATHS["latest_anomaly_alerts"], {})
    portfolio_directive = read_json(INPUT_PATHS["portfolio_directive"], {})
    cio_brief = read_text(INPUT_PATHS["cio_brief"], "")
    cio_market_thesis = read_json(INPUT_PATHS["cio_market_thesis"], {})
    cio_portfolio_directive = read_json(INPUT_PATHS["cio_portfolio_directive"], {})
    ai_research_firm_mode = read_json(INPUT_PATHS["ai_research_firm_mode"], {})
    daily_institutional_cycle = read_json(INPUT_PATHS["daily_institutional_cycle"], {})
    platform_health_report = read_json(INPUT_PATHS["platform_health_report"], {})
    latest_refresh = read_json(INPUT_PATHS["latest_refresh"], {})
    system_status = read_json(INPUT_PATHS["system_status"], {})

    mc_summary = read_json(
        RESULTS_DIR / "digital_twin" / "monte_carlo_lab" / "monte_carlo_summary.json",
        {},
    )

    final_summary = read_json(
        RESULTS_DIR / "digital_twin" / "final_report" / "digital_twin_final_summary.json",
        {},
    )

    live_projection = read_json(
        RESULTS_DIR / "digital_twin" / "live_risk_projection" / "live_risk_projection.json",
        {},
    )

    risk_dashboard = read_json(
        RESULTS_DIR / "risk" / "risk_dashboard.json",
        {},
    )

    portfolio_risk = as_dict(risk_dashboard.get("portfolio_risk", {}))
    tail_risk = as_dict(risk_dashboard.get("tail_risk", {}))
    drawdown_risk = as_dict(risk_dashboard.get("drawdown_risk", {}))

    regime = first_value(
        latest_refresh.get("regime"),
        latest_regime.get("regime"),
        latest_regime.get("current_regime"),
        cio_market_thesis.get("regime"),
        ai_research_firm_mode.get("regime"),
        default="unknown",
    )

    posture = normalize_posture(
        first_value(
            latest_refresh.get("portfolio_posture"),
            portfolio_directive.get("portfolio_posture"),
            portfolio_directive.get("posture"),
            cio_portfolio_directive.get("portfolio_posture"),
            cio_portfolio_directive.get("posture"),
            ai_research_firm_mode.get("posture"),
            default="unknown",
        )
    )

    execution_permission = normalize_permission(
        first_value(
            latest_refresh.get("execution_permission"),
            portfolio_directive.get("execution_permission"),
            cio_portfolio_directive.get("execution_permission"),
            daily_institutional_cycle.get("execution_permission"),
            daily_institutional_cycle.get("allow_execution"),
            default="unknown",
        )
    )

    confidence = first_value(
        latest_refresh.get("confidence"),
        cio_market_thesis.get("confidence"),
        cio_portfolio_directive.get("confidence"),
        portfolio_directive.get("confidence"),
        ai_research_firm_mode.get("confidence"),
        default=0.0,
    )

    biggest_risk = first_value(
        latest_refresh.get("biggest_risk"),
        ai_research_firm_mode.get("highest_risk"),
        ai_research_firm_mode.get("biggest_risk"),
        cio_market_thesis.get("biggest_risk"),
        daily_institutional_cycle.get("biggest_risk"),
        default="No dominant risk identified yet",
    )

    recommended_action = first_value(
        portfolio_directive.get("recommended_action"),
        portfolio_directive.get("action"),
        cio_portfolio_directive.get("recommended_action"),
        cio_portfolio_directive.get("action"),
        default="maintain_current_portfolio",
    )

    risk_score = first_value(
        ai_research_firm_mode.get("risk_score"),
        ai_research_firm_mode.get("desk_risk_score"),
        cio_market_thesis.get("risk_score"),
        daily_institutional_cycle.get("risk_score"),
        live_projection.get("stress_score"),
        live_projection.get("risk_score"),
        default=None,
    )

    cvar = first_value(
        live_projection.get("cvar"),
        live_projection.get("cvar_95"),
        live_projection.get("CVaR95"),
        tail_risk.get("cvar"),
        tail_risk.get("cvar_95"),
        tail_risk.get("cvar95"),
        risk_dashboard.get("cvar"),
        risk_dashboard.get("cvar_95"),
        daily_institutional_cycle.get("cvar"),
        daily_institutional_cycle.get("cvar_95"),
        portfolio_directive.get("cvar"),
        cio_market_thesis.get("cvar"),
        mc_summary.get("cvar_95"),
        default=None,
    )

    drawdown = first_value(
        live_projection.get("drawdown"),
        live_projection.get("max_drawdown"),
        drawdown_risk.get("max_drawdown"),
        drawdown_risk.get("drawdown"),
        portfolio_risk.get("max_drawdown"),
        portfolio_risk.get("drawdown"),
        risk_dashboard.get("max_drawdown"),
        risk_dashboard.get("drawdown"),
        daily_institutional_cycle.get("drawdown"),
        daily_institutional_cycle.get("max_drawdown"),
        portfolio_directive.get("drawdown"),
        mc_summary.get("expected_max_drawdown"),
        default=None,
    )

    numeric_risk_score = None
    try:
        cvar_component = abs(float(cvar or 0.0)) * 1000
        drawdown_component = abs(float(drawdown or 0.0)) * 1000
        numeric_risk_score = min(100, round((cvar_component * 0.6) + (drawdown_component * 0.4), 2))
    except Exception:
        numeric_risk_score = None

    if risk_score is None:
        risk_score = numeric_risk_score

    digital_twin = {
        "worst_scenario": final_summary.get("worst_stress_scenario", {}).get("scenario_id"),
        "worst_scenario_name": final_summary.get("worst_stress_scenario", {}).get("name"),
        "worst_scenario_return": final_summary.get("worst_stress_scenario", {}).get("portfolio_impact"),
        "monte_carlo_result": {
            "expected_return": mc_summary.get("expected_cumulative_return"),
            "expected_volatility": mc_summary.get("expected_annualized_volatility"),
            "var95": mc_summary.get("var_95"),
            "cvar95": mc_summary.get("cvar_95"),
            "survival": mc_summary.get("survival_status"),
        },
        "stress_test_result": final_summary.get("worst_stress_scenario", {}),
        "contagion_risk": {
            "source_asset": final_summary.get("worst_contagion_source", {}).get("source_asset"),
            "portfolio_impact": final_summary.get("worst_contagion_source", {}).get("total_portfolio_impact"),
            "most_impacted_asset": final_summary.get("worst_contagion_source", {}).get("most_impacted_asset"),
        },
        "overall_status": final_summary.get("overall_digital_twin_status"),
        "live_projection": live_projection,
    }

    market_records = market_records_from_snapshot(live_market_snapshot)
    anomalies = extract_anomalies(latest_anomaly_alerts)

    state = {
        "timestamp": utc_now(),
        "title": "AURUM Mission Control",
        "status": {
            "system_status": first_value(system_status.get("mission_control_status"), latest_refresh.get("status"), default="unknown"),
            "market_status": "active" if market_records else "missing",
            "market_data_status": first_value(latest_refresh.get("market_data_status"), system_status.get("market_data_status"), default="unknown"),
            "last_refresh_time": first_value(latest_refresh.get("timestamp"), system_status.get("timestamp"), default=None),
        },
        "mission_control": {
            "current_regime": str(regime).lower(),
            "portfolio_posture": posture,
            "execution_permission": execution_permission,
            "cio_confidence": confidence,
            "biggest_risk": biggest_risk,
            "recommended_action": recommended_action,
        },
        "live_markets": market_records,
        "ai_agents": {
            "research_firm": ai_research_firm_mode,
            "cio_market_thesis": cio_market_thesis,
            "cio_brief": cio_brief,
        },
        "portfolio_directive": {
            "posture": posture,
            "recommended_action": recommended_action,
            "execution_permission": execution_permission,
            "confidence": confidence,
            "raw": portfolio_directive or cio_portfolio_directive,
        },
        "risk_regime": {
            "regime": str(regime).lower(),
            "risk_score": risk_score,
            "cvar": cvar,
            "drawdown": drawdown,
            "anomalies": anomalies,
        },
        "digital_twin": digital_twin,
        "system_health": {
            "last_refresh_time": first_value(latest_refresh.get("timestamp"), system_status.get("timestamp"), default=None),
            "data_freshness": first_value(latest_refresh.get("market_data_status"), system_status.get("market_data_status"), default="unknown"),
            "redis_status": first_value(platform_health_report.get("redis_status"), default="not_checked"),
            "database_status": first_value(platform_health_report.get("database_status"), default="not_checked"),
            "ai_artifacts_status": "available" if ai_research_firm_mode or cio_market_thesis else "missing",
            "dashboard_state_status": "ready",
            "platform_health_report": platform_health_report,
        },
        "source_files": {name: str(path.relative_to(ROOT)) for name, path in INPUT_PATHS.items()},
    }

    write_json(DASHBOARD_STATE_PATH, state)
    return state


def print_summary(state: dict[str, Any]) -> None:
    mc = state["mission_control"]
    status = state["status"]

    print("=" * 80)
    print("AURUM DASHBOARD STATE BUILDER")
    print("=" * 80)
    print(f"Saved:                {DASHBOARD_STATE_PATH.relative_to(ROOT)}")
    print(f"System Status:        {status.get('system_status')}")
    print(f"Market Status:        {status.get('market_status')}")
    print(f"Market Data:          {status.get('market_data_status')}")
    print(f"Regime:               {mc.get('current_regime')}")
    print(f"Portfolio Posture:    {mc.get('portfolio_posture')}")
    print(f"Execution Permission: {mc.get('execution_permission')}")
    print(f"CIO Confidence:       {mc.get('cio_confidence')}")
    print(f"Biggest Risk:         {mc.get('biggest_risk')}")
    print("=" * 80)


def main() -> None:
    state = build_dashboard_state()
    print_summary(state)


if __name__ == "__main__":
    main()