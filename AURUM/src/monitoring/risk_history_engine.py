# src/monitoring/risk_history_engine.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PORTFOLIO_STATE_PATH = Path("results/portfolio/institutional_portfolio_state.json")
PERFORMANCE_SNAPSHOT_PATH = Path("results/monitoring/live_performance_snapshot.json")

OUTPUT_DIR = Path("results/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RISK_HISTORY_PATH = OUTPUT_DIR / "risk_history.jsonl"
RISK_SUMMARY_PATH = OUTPUT_DIR / "risk_history_summary.json"
RISK_SNAPSHOT_PATH = OUTPUT_DIR / "risk_snapshot.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    rows = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        try:
            rows.append(json.loads(line))
        except Exception:
            continue

    return rows


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


class RiskHistoryEngine:
    def __init__(self) -> None:
        self.portfolio_state = load_json(PORTFOLIO_STATE_PATH, {})
        self.performance_snapshot = load_json(PERFORMANCE_SNAPSHOT_PATH, {})

    def build_snapshot(self) -> Dict[str, Any]:
        market_state = self.portfolio_state.get("market_state", {})
        risk_state = self.portfolio_state.get("risk_state", {})
        governance_state = self.portfolio_state.get("governance_state", {})
        execution_state = self.portfolio_state.get("execution_state", {})

        market_regime = (
            market_state.get("regime")
            or market_state.get("market_regime")
            or market_state.get("raw", {}).get("current_regime")
            or "unknown"
        )

        stress_score = safe_float(
            market_state.get(
                "stress_score",
                market_state.get(
                    "market_stress",
                    market_state.get("raw", {}).get("market_stress_score", 0.0),
                ),
            )
        )

        var_95 = safe_float(
            risk_state.get(
                "var_95",
                risk_state.get("raw", {}).get("projected_var_95", 0.0),
            )
        )

        cvar_95 = safe_float(
            risk_state.get(
                "cvar_95",
                risk_state.get("raw", {}).get("projected_cvar_95", 0.0),
            )
        )

        drawdown = safe_float(
            risk_state.get(
                "drawdown",
                risk_state.get("raw", {}).get("projected_drawdown", 0.0),
            )
        )

        risk_level = (
            risk_state.get("risk_level")
            or risk_state.get("raw", {}).get("risk_level")
            or "unknown"
        )

        return {
            "event_type": "risk_history_snapshot",
            "timestamp": now_utc(),
            "portfolio_id": self.portfolio_state.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
            "cycle_id": self.performance_snapshot.get("cycle_id", "UNKNOWN"),
            "market_regime": market_regime,
            "stress_score": stress_score,
            "risk_level": risk_level,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "drawdown": drawdown,
            "governance_status": (
                governance_state.get("governance_status")
                or governance_state.get("status")
                or "UNKNOWN"
            ),
            "approval_status": self.performance_snapshot.get("approval_status", "UNKNOWN"),
            "execution_fill_ratio": safe_float(execution_state.get("aggregate_fill_ratio", 0.0)),
            "nav_proxy": safe_float(self.performance_snapshot.get("nav_proxy", 1.0)),
        }

    def build_summary(self, latest_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        history = load_jsonl(RISK_HISTORY_PATH)

        stress_values = [
            safe_float(row.get("stress_score"))
            for row in history
            if row.get("stress_score") is not None
        ]
        var_values = [
            abs(safe_float(row.get("var_95")))
            for row in history
            if row.get("var_95") is not None
        ]
        cvar_values = [
            abs(safe_float(row.get("cvar_95")))
            for row in history
            if row.get("cvar_95") is not None
        ]
        dd_values = [
            abs(safe_float(row.get("drawdown")))
            for row in history
            if row.get("drawdown") is not None
        ]

        critical_cycles = sum(
            1 for row in history if str(row.get("risk_level", "")).lower() == "critical"
        )
        review_cycles = sum(
            1 for row in history if row.get("governance_status") == "REVIEW_REQUIRED"
        )

        return {
            "event_type": "risk_history_summary",
            "timestamp": now_utc(),
            "history_points": len(history),
            "latest_risk_level": latest_snapshot.get("risk_level", "unknown"),
            "latest_stress_score": latest_snapshot.get("stress_score", 0.0),
            "latest_var_95": latest_snapshot.get("var_95", 0.0),
            "latest_cvar_95": latest_snapshot.get("cvar_95", 0.0),
            "latest_drawdown": latest_snapshot.get("drawdown", 0.0),
            "max_stress_score": round(max(stress_values), 6) if stress_values else 0.0,
            "max_var_95_abs": round(max(var_values), 6) if var_values else 0.0,
            "max_cvar_95_abs": round(max(cvar_values), 6) if cvar_values else 0.0,
            "max_drawdown_abs": round(max(dd_values), 6) if dd_values else 0.0,
            "critical_cycles": critical_cycles,
            "review_required_cycles": review_cycles,
        }

    def run(self) -> Dict[str, Any]:
        snapshot = self.build_snapshot()

        save_json(RISK_SNAPSHOT_PATH, snapshot)
        append_jsonl(RISK_HISTORY_PATH, snapshot)

        summary = self.build_summary(snapshot)
        save_json(RISK_SUMMARY_PATH, summary)

        return {
            "snapshot": snapshot,
            "summary": summary,
        }


def run_risk_history_engine() -> Dict[str, Any]:
    return RiskHistoryEngine().run()


def main() -> None:
    print("=" * 80)
    print("AURUM RISK HISTORY ENGINE")
    print("=" * 80)

    result = run_risk_history_engine()
    snapshot = result["snapshot"]
    summary = result["summary"]

    print(f"Portfolio ID: {snapshot['portfolio_id']}")
    print(f"Cycle ID:     {snapshot['cycle_id']}")
    print("-" * 80)
    print(f"Regime:       {snapshot['market_regime']}")
    print(f"Stress:       {snapshot['stress_score']:.2f}")
    print(f"Risk Level:   {snapshot['risk_level']}")
    print(f"VaR 95:       {snapshot['var_95']:.4f}")
    print(f"CVaR 95:      {snapshot['cvar_95']:.4f}")
    print(f"Drawdown:     {snapshot['drawdown']:.4f}")
    print("-" * 80)
    print(f"History Points:       {summary['history_points']}")
    print(f"Critical Cycles:      {summary['critical_cycles']}")
    print(f"Review Cycles:        {summary['review_required_cycles']}")
    print(f"Max Stress:           {summary['max_stress_score']}")
    print(f"Max Abs VaR:          {summary['max_var_95_abs']}")
    print(f"Max Abs CVaR:         {summary['max_cvar_95_abs']}")
    print(f"Max Abs Drawdown:     {summary['max_drawdown_abs']}")
    print("-" * 80)
    print(f"Saved Snapshot: {RISK_SNAPSHOT_PATH}")
    print(f"Saved History:  {RISK_HISTORY_PATH}")
    print(f"Saved Summary:  {RISK_SUMMARY_PATH}")


if __name__ == "__main__":
    main()