# src/monitoring/live_performance_engine.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PORTFOLIO_STATE_PATH = Path("results/portfolio/institutional_portfolio_state.json")
APPROVAL_PATH = Path("results/orchestrator/decision_approval.json")
OPERATING_CYCLE_PATH = Path("results/orchestrator/operating_cycle.json")

OUTPUT_DIR = Path("results/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_PATH = OUTPUT_DIR / "live_performance_snapshot.json"
HISTORY_PATH = OUTPUT_DIR / "performance_history.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "live_performance_summary.json"


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


class LivePerformanceEngine:
    def __init__(self) -> None:
        self.portfolio_state = load_json(PORTFOLIO_STATE_PATH, {})
        self.approval = load_json(APPROVAL_PATH, {})
        self.operating_cycle = load_json(OPERATING_CYCLE_PATH, {})

    def build_snapshot(self) -> Dict[str, Any]:
        position_state = self.portfolio_state.get("position_state", {})
        performance_state = self.portfolio_state.get("performance_state", {})
        governance_state = self.portfolio_state.get("governance_state", {})
        market_state = self.portfolio_state.get("market_state", {})
        risk_state = self.portfolio_state.get("risk_state", {})
        execution_state = self.portfolio_state.get("execution_state", {})

        daily_pnl = safe_float(performance_state.get("daily_pnl_proxy", 0.0))
        mtd_pnl = safe_float(performance_state.get("mtd_pnl_proxy", daily_pnl))
        ytd_pnl = safe_float(performance_state.get("ytd_pnl_proxy", daily_pnl))

        cash_weight = safe_float(
            position_state.get("cash_weight", position_state.get("positions", {}).get("cash", 0.0))
        )
        gross_exposure = safe_float(position_state.get("gross_exposure", 1.0 - cash_weight))
        net_exposure = safe_float(position_state.get("net_exposure", gross_exposure))
        deployment_ratio = safe_float(performance_state.get("deployment_ratio", gross_exposure))
        dry_powder_ratio = safe_float(performance_state.get("dry_powder_ratio", cash_weight))

        nav_proxy = 1.0 + ytd_pnl

        return {
            "event_type": "live_performance_snapshot",
            "timestamp": now_utc(),
            "portfolio_id": self.portfolio_state.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
            "cycle_id": self.operating_cycle.get("cycle_id", "UNKNOWN"),
            "nav_proxy": round(nav_proxy, 6),
            "daily_pnl_proxy": round(daily_pnl, 6),
            "mtd_pnl_proxy": round(mtd_pnl, 6),
            "ytd_pnl_proxy": round(ytd_pnl, 6),
            "cash_weight": round(cash_weight, 6),
            "gross_exposure": round(gross_exposure, 6),
            "net_exposure": round(net_exposure, 6),
            "deployment_ratio": round(deployment_ratio, 6),
            "dry_powder_ratio": round(dry_powder_ratio, 6),
            "market_regime": market_state.get("regime", market_state.get("market_regime", "unknown")),
            "market_stress": safe_float(market_state.get("stress_score", market_state.get("market_stress", 0.0))),
            "risk_level": risk_state.get("risk_level", "unknown"),
            "governance_status": governance_state.get(
                "governance_status",
                governance_state.get("status", "UNKNOWN"),
            ),
            "approval_status": self.approval.get("status", "UNKNOWN"),
            "execution_fill_ratio": safe_float(execution_state.get("aggregate_fill_ratio", 0.0)),
            "execution_cost_bps": safe_float(execution_state.get("total_execution_cost_bps", 0.0)),
            "operating_status": self.operating_cycle.get("overall_status", "UNKNOWN"),
        }

    def build_summary(self, latest_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        history = load_jsonl(HISTORY_PATH)

        nav_values = [
            safe_float(row.get("nav_proxy", 1.0))
            for row in history
            if row.get("nav_proxy") is not None
        ]

        if nav_values:
            peak_nav = max(nav_values)
            latest_nav = safe_float(latest_snapshot.get("nav_proxy", 1.0))
            drawdown_from_peak = latest_nav / peak_nav - 1.0 if peak_nav else 0.0
        else:
            peak_nav = safe_float(latest_snapshot.get("nav_proxy", 1.0))
            drawdown_from_peak = 0.0

        escalated_count = sum(
            1 for row in history if row.get("approval_status") == "ESCALATED"
        )
        review_count = sum(
            1 for row in history if row.get("governance_status") == "REVIEW_REQUIRED"
        )

        return {
            "event_type": "live_performance_summary",
            "timestamp": now_utc(),
            "history_points": len(history),
            "latest_nav_proxy": latest_snapshot.get("nav_proxy", 1.0),
            "peak_nav_proxy": round(peak_nav, 6),
            "drawdown_from_peak": round(drawdown_from_peak, 6),
            "latest_daily_pnl_proxy": latest_snapshot.get("daily_pnl_proxy", 0.0),
            "latest_mtd_pnl_proxy": latest_snapshot.get("mtd_pnl_proxy", 0.0),
            "latest_ytd_pnl_proxy": latest_snapshot.get("ytd_pnl_proxy", 0.0),
            "latest_cash_weight": latest_snapshot.get("cash_weight", 0.0),
            "latest_gross_exposure": latest_snapshot.get("gross_exposure", 0.0),
            "latest_risk_level": latest_snapshot.get("risk_level", "unknown"),
            "latest_governance_status": latest_snapshot.get("governance_status", "UNKNOWN"),
            "latest_approval_status": latest_snapshot.get("approval_status", "UNKNOWN"),
            "escalated_cycles": escalated_count,
            "review_required_cycles": review_count,
        }

    def run(self) -> Dict[str, Any]:
        snapshot = self.build_snapshot()

        save_json(SNAPSHOT_PATH, snapshot)
        append_jsonl(HISTORY_PATH, snapshot)

        summary = self.build_summary(snapshot)
        save_json(SUMMARY_PATH, summary)

        return {
            "snapshot": snapshot,
            "summary": summary,
        }


def run_live_performance_engine() -> Dict[str, Any]:
    return LivePerformanceEngine().run()


def main() -> None:
    print("=" * 80)
    print("AURUM LIVE PERFORMANCE ENGINE")
    print("=" * 80)

    result = run_live_performance_engine()
    snapshot = result["snapshot"]
    summary = result["summary"]

    print(f"Portfolio ID: {snapshot['portfolio_id']}")
    print(f"Cycle ID:     {snapshot['cycle_id']}")
    print("-" * 80)
    print(f"NAV Proxy:       {snapshot['nav_proxy']:.6f}")
    print(f"Daily PnL Proxy: {snapshot['daily_pnl_proxy']:.2%}")
    print(f"MTD PnL Proxy:   {snapshot['mtd_pnl_proxy']:.2%}")
    print(f"YTD PnL Proxy:   {snapshot['ytd_pnl_proxy']:.2%}")
    print("-" * 80)
    print(f"Cash Weight:     {snapshot['cash_weight']:.2%}")
    print(f"Gross Exposure:  {snapshot['gross_exposure']:.2%}")
    print(f"Risk Level:      {snapshot['risk_level']}")
    print(f"Governance:      {snapshot['governance_status']}")
    print(f"Approval:        {snapshot['approval_status']}")
    print("-" * 80)
    print(f"History Points:  {summary['history_points']}")
    print(f"Peak NAV:        {summary['peak_nav_proxy']}")
    print(f"Drawdown Peak:   {summary['drawdown_from_peak']:.2%}")
    print("-" * 80)
    print(f"Saved Snapshot:  {SNAPSHOT_PATH}")
    print(f"Saved History:   {HISTORY_PATH}")
    print(f"Saved Summary:   {SUMMARY_PATH}")


if __name__ == "__main__":
    main()