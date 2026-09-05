# src/portfolio/position_management_engine.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

EXECUTION_REPORTS_STREAM = "execution_reports"
LIVE_POSITIONS_STREAM = "live_positions"

OUTPUT_DIR = Path("results/portfolio")
EXECUTION_DIR = Path("results/execution")
STATE_DIR = Path("results/portfolio/state")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

LIVE_POSITIONS_PATH = OUTPUT_DIR / "live_positions.json"
POSITION_SNAPSHOT_PATH = OUTPUT_DIR / "position_snapshot.json"
PROCESSED_EXECUTIONS_PATH = STATE_DIR / "processed_execution_ids.json"


DEFAULT_PORTFOLIO = {
    "SPY": 0.25,
    "QQQ": 0.25,
    "TLT": 0.15,
    "GLD": 0.10,
    "BTC-USD": 0.05,
    "cash": 0.20,
}


@dataclass
class PositionSnapshot:
    timestamp: str
    portfolio_id: str
    positions: Dict[str, float]
    gross_exposure: float
    net_exposure: float
    cash_weight: float
    total_execution_cost_bps: float
    realized_pnl_proxy: float
    unrealized_pnl_proxy: float
    processed_executions: int
    status: str


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


def load_current_positions() -> Dict[str, float]:
    if LIVE_POSITIONS_PATH.exists():
        data = load_json(LIVE_POSITIONS_PATH, {})
        if isinstance(data, dict) and "positions" in data:
            return {k: float(v) for k, v in data["positions"].items()}

    current_path = Path("results/portfolio/current_portfolio.json")
    if current_path.exists():
        data = load_json(current_path, DEFAULT_PORTFOLIO)
        return {k: float(v) for k, v in data.items()}

    return dict(DEFAULT_PORTFOLIO)


def load_processed_execution_ids() -> set[str]:
    return set(load_json(PROCESSED_EXECUTIONS_PATH, []))


def save_processed_execution_ids(processed: set[str]) -> None:
    save_json(PROCESSED_EXECUTIONS_PATH, sorted(processed))


def load_execution_reports_from_file() -> List[Dict[str, Any]]:
    return load_json(EXECUTION_DIR / "execution_reports.json", [])


def load_execution_reports_from_redis(max_count: int = 200) -> List[Dict[str, Any]]:
    r = get_redis_client()
    entries = r.xrange(EXECUTION_REPORTS_STREAM, count=max_count)

    reports: List[Dict[str, Any]] = []
    for _, fields in entries:
        payload = fields.get("payload")
        if payload:
            reports.append(json.loads(payload))

    return reports


def normalize_positions(positions: Dict[str, float]) -> Dict[str, float]:
    cleaned = {k: round(float(v), 8) for k, v in positions.items()}

    for ticker, value in list(cleaned.items()):
        if abs(value) < 1e-10:
            cleaned[ticker] = 0.0

    total = sum(cleaned.values())

    if total <= 0:
        return dict(DEFAULT_PORTFOLIO)

    drift = 1.0 - total
    cleaned["cash"] = round(cleaned.get("cash", 0.0) + drift, 8)

    return cleaned


def apply_execution_report(
    positions: Dict[str, float],
    report: Dict[str, Any],
) -> Dict[str, float]:
    ticker = report["ticker"]
    action = report["action"]
    executed_pct = float(report["executed_pct"])

    signed_trade = executed_pct if action == "BUY" else -executed_pct

    positions[ticker] = float(positions.get(ticker, 0.0)) + signed_trade
    positions["cash"] = float(positions.get("cash", 0.0)) - signed_trade

    cost_weight = float(report.get("total_cost_bps", 0.0)) / 10000.0
    positions["cash"] = positions["cash"] - cost_weight

    return positions


def compute_snapshot(
    positions: Dict[str, float],
    processed_count: int,
    total_execution_cost_bps: float,
    portfolio_id: str = "AURUM_LIVE_PORTFOLIO",
) -> PositionSnapshot:
    risky_positions = {
        ticker: weight
        for ticker, weight in positions.items()
        if ticker.lower() != "cash"
    }

    gross_exposure = sum(abs(v) for v in risky_positions.values())
    net_exposure = sum(v for v in risky_positions.values())
    cash_weight = positions.get("cash", 0.0)

    realized_pnl_proxy = -total_execution_cost_bps / 10000.0
    unrealized_pnl_proxy = 0.0

    if cash_weight < -0.02:
        status = "CASH_BREACH"
    elif gross_exposure > 1.10:
        status = "EXPOSURE_BREACH"
    else:
        status = "ACTIVE"

    return PositionSnapshot(
        timestamp=now_utc(),
        portfolio_id=portfolio_id,
        positions={k: round(v, 6) for k, v in sorted(positions.items())},
        gross_exposure=round(gross_exposure, 6),
        net_exposure=round(net_exposure, 6),
        cash_weight=round(cash_weight, 6),
        total_execution_cost_bps=round(total_execution_cost_bps, 4),
        realized_pnl_proxy=round(realized_pnl_proxy, 8),
        unrealized_pnl_proxy=round(unrealized_pnl_proxy, 8),
        processed_executions=processed_count,
        status=status,
    )


def publish_live_positions(snapshot: PositionSnapshot) -> None:
    r = get_redis_client()
    payload = asdict(snapshot)

    r.xadd(
        LIVE_POSITIONS_STREAM,
        {
            "event_type": "live_positions",
            "payload": json.dumps(payload),
            "portfolio_id": snapshot.portfolio_id,
            "status": snapshot.status,
            "timestamp": snapshot.timestamp,
        },
    )


def run_position_management_engine() -> Dict[str, Any]:
    try:
        reports = load_execution_reports_from_redis()
    except Exception:
        reports = []

    if not reports:
        reports = load_execution_reports_from_file()

    positions = load_current_positions()
    processed_execution_ids = load_processed_execution_ids()

    new_reports = []
    total_execution_cost_bps = 0.0

    for report in reports:
        execution_id = report["execution_id"]

        if execution_id in processed_execution_ids:
            continue

        positions = apply_execution_report(positions, report)
        processed_execution_ids.add(execution_id)
        new_reports.append(report)
        total_execution_cost_bps += float(report.get("total_cost_bps", 0.0))

    positions = normalize_positions(positions)

    snapshot = compute_snapshot(
        positions=positions,
        processed_count=len(new_reports),
        total_execution_cost_bps=total_execution_cost_bps,
    )

    snapshot_dict = asdict(snapshot)

    save_json(LIVE_POSITIONS_PATH, snapshot_dict)
    save_json(POSITION_SNAPSHOT_PATH, snapshot_dict)
    save_processed_execution_ids(processed_execution_ids)

    publish_live_positions(snapshot)

    return snapshot_dict


def main() -> None:
    print("=" * 80)
    print("AURUM POSITION MANAGEMENT ENGINE")
    print("=" * 80)

    snapshot = run_position_management_engine()

    print(f"Portfolio ID: {snapshot['portfolio_id']}")
    print(f"Timestamp: {snapshot['timestamp']}")
    print(f"Status: {snapshot['status']}")
    print(f"Processed New Executions: {snapshot['processed_executions']}")
    print("-" * 80)

    print("LIVE POSITIONS")
    for ticker, weight in snapshot["positions"].items():
        print(f"{ticker:<10} {weight:>10.2%}")

    print("-" * 80)
    print(f"Gross Exposure: {snapshot['gross_exposure']:.2%}")
    print(f"Net Exposure:   {snapshot['net_exposure']:.2%}")
    print(f"Cash Weight:    {snapshot['cash_weight']:.2%}")
    print(f"Execution Cost: {snapshot['total_execution_cost_bps']} bps")
    print(f"Saved: {LIVE_POSITIONS_PATH}")
    print(f"Redis stream: {LIVE_POSITIONS_STREAM}")


if __name__ == "__main__":
    main()