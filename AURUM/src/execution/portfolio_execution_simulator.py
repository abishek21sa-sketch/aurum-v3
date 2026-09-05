# src/execution/portfolio_execution_simulator.py

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

TRADE_TICKETS_STREAM = "trade_tickets"
EXECUTION_REPORTS_STREAM = "execution_reports"

OUTPUT_DIR = Path("results/execution")
STATE_DIR = Path("results/execution/state")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_TICKETS_PATH = STATE_DIR / "processed_ticket_ids.json"

random.seed(42)


@dataclass
class ExecutionReport:
    execution_id: str
    idempotency_key: str
    ticket_id: str
    order_id: str
    timestamp: str
    portfolio_id: str
    ticker: str
    action: str
    requested_pct: float
    executed_pct: float
    unfilled_pct: float
    fill_ratio: float
    slippage_bps: float
    market_impact_bps: float
    transaction_cost_bps: float
    total_cost_bps: float
    execution_delay_ms: int
    status: str
    reason: str


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


def load_processed_ticket_ids() -> set[str]:
    return set(load_json(PROCESSED_TICKETS_PATH, []))


def save_processed_ticket_ids(processed: set[str]) -> None:
    save_json(PROCESSED_TICKETS_PATH, sorted(processed))


def load_existing_reports() -> List[Dict[str, Any]]:
    return load_json(OUTPUT_DIR / "execution_reports.json", [])


def load_tickets_from_redis(max_count: int = 100) -> List[Dict[str, Any]]:
    r = get_redis_client()
    entries = r.xrange(TRADE_TICKETS_STREAM, count=max_count)

    tickets: List[Dict[str, Any]] = []
    for _, fields in entries:
        payload = fields.get("payload")
        if payload:
            tickets.append(json.loads(payload))

    return tickets


def simulate_fill_ratio(priority: str, quantity_pct: float) -> float:
    base = {
        "HIGH": random.uniform(0.92, 1.00),
        "MEDIUM": random.uniform(0.85, 0.98),
        "LOW": random.uniform(0.75, 0.95),
    }.get(priority, random.uniform(0.80, 0.95))

    if quantity_pct > 0.07:
        base -= 0.05
    elif quantity_pct > 0.04:
        base -= 0.025

    return round(max(0.0, min(base, 1.0)), 6)


def simulate_execution_report(ticket: Dict[str, Any], sequence: int) -> ExecutionReport:
    requested_pct = float(ticket["quantity_pct"])
    fill_ratio = simulate_fill_ratio(ticket.get("priority", "MEDIUM"), requested_pct)

    executed_pct = round(requested_pct * fill_ratio, 6)
    unfilled_pct = round(requested_pct - executed_pct, 6)

    slippage_bps = round(random.uniform(1.0, 8.0) + requested_pct * 50, 4)
    market_impact_bps = round(random.uniform(0.5, 6.0) + requested_pct * 35, 4)
    transaction_cost_bps = round(random.uniform(0.5, 2.5), 4)
    total_cost_bps = round(slippage_bps + market_impact_bps + transaction_cost_bps, 4)

    execution_delay_ms = random.randint(100, 2500)

    if fill_ratio >= 0.995:
        status = "FILLED"
    elif fill_ratio > 0.0:
        status = "PARTIALLY_FILLED"
    else:
        status = "REJECTED"

    idempotency_key = f"EXECUTION::{ticket['ticket_id']}"

    return ExecutionReport(
        execution_id=f"EXE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{sequence:03d}",
        idempotency_key=idempotency_key,
        ticket_id=ticket["ticket_id"],
        order_id=ticket["order_id"],
        timestamp=now_utc(),
        portfolio_id=ticket.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
        ticker=ticket["ticker"],
        action=ticket["action"],
        requested_pct=requested_pct,
        executed_pct=executed_pct,
        unfilled_pct=unfilled_pct,
        fill_ratio=fill_ratio,
        slippage_bps=slippage_bps,
        market_impact_bps=market_impact_bps,
        transaction_cost_bps=transaction_cost_bps,
        total_cost_bps=total_cost_bps,
        execution_delay_ms=execution_delay_ms,
        status=status,
        reason=ticket.get("reason", "Portfolio Rebalance"),
    )


def publish_execution_report_to_redis(report: ExecutionReport) -> None:
    r = get_redis_client()
    payload = asdict(report)

    r.xadd(
        EXECUTION_REPORTS_STREAM,
        {
            "event_type": "execution_report",
            "payload": json.dumps(payload),
            "ticker": report.ticker,
            "action": report.action,
            "status": report.status,
            "idempotency_key": report.idempotency_key,
            "timestamp": report.timestamp,
        },
    )


def run_portfolio_execution_simulator() -> List[Dict[str, Any]]:
    tickets = load_tickets_from_redis()
    processed_ticket_ids = load_processed_ticket_ids()
    existing_reports = load_existing_reports()

    new_reports: List[ExecutionReport] = []
    sequence_start = len(existing_reports) + 1

    for ticket in tickets:
        ticket_id = ticket["ticket_id"]

        if ticket_id in processed_ticket_ids:
            continue

        report = simulate_execution_report(
            ticket=ticket,
            sequence=len(new_reports) + sequence_start,
        )

        new_reports.append(report)
        processed_ticket_ids.add(ticket_id)

    new_report_dicts = [asdict(report) for report in new_reports]
    all_reports = existing_reports + new_report_dicts

    save_json(OUTPUT_DIR / "execution_reports.json", all_reports)
    save_processed_ticket_ids(processed_ticket_ids)

    for report in new_reports:
        publish_execution_report_to_redis(report)

    return new_report_dicts


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO EXECUTION SIMULATOR - IDEMPOTENT")
    print("=" * 80)

    reports = run_portfolio_execution_simulator()

    if not reports:
        print("No new execution reports generated. Previously processed tickets skipped.")
        return

    for report in reports:
        print(
            f"{report['execution_id']} | {report['action']} {report['ticker']} | "
            f"requested={report['requested_pct']:.2%} "
            f"executed={report['executed_pct']:.2%} "
            f"status={report['status']} "
            f"cost={report['total_cost_bps']}bps"
        )

    print("-" * 80)
    print(f"New execution reports generated: {len(reports)}")
    print(f"Saved: {OUTPUT_DIR / 'execution_reports.json'}")
    print(f"State: {PROCESSED_TICKETS_PATH}")
    print(f"Redis stream: {EXECUTION_REPORTS_STREAM}")


if __name__ == "__main__":
    main()