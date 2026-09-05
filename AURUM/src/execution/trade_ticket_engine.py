# src/execution/trade_ticket_engine.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

EXECUTION_ORDERS_STREAM = "execution_orders"
TRADE_TICKETS_STREAM = "trade_tickets"

OUTPUT_DIR = Path("results/execution")
STATE_DIR = Path("results/execution/state")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_ORDERS_PATH = STATE_DIR / "processed_order_ids.json"


@dataclass
class TradeTicket:
    ticket_id: str
    idempotency_key: str
    order_id: str
    timestamp: str
    portfolio_id: str
    strategy: str
    ticker: str
    action: str
    target_weight: float
    current_weight: float
    trade_size: float
    quantity_pct: float
    priority: str
    reason: str
    status: str = "SUBMITTED"


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


def load_processed_order_ids() -> set[str]:
    return set(load_json(PROCESSED_ORDERS_PATH, []))


def save_processed_order_ids(processed: set[str]) -> None:
    save_json(PROCESSED_ORDERS_PATH, sorted(processed))


def load_orders_from_redis(max_count: int = 100) -> List[Dict[str, Any]]:
    r = get_redis_client()
    entries = r.xrange(EXECUTION_ORDERS_STREAM, count=max_count)

    orders: List[Dict[str, Any]] = []
    for _, fields in entries:
        payload = fields.get("payload")
        if payload:
            orders.append(json.loads(payload))

    return orders


def load_existing_tickets() -> List[Dict[str, Any]]:
    path = OUTPUT_DIR / "trade_tickets.json"
    return load_json(path, [])


def create_trade_ticket(
    order: Dict[str, Any],
    sequence: int,
    strategy: str = "Regime Aware",
) -> TradeTicket:
    action_sign = 1 if order["action"] == "BUY" else -1
    trade_size = action_sign * float(order["quantity_pct"])
    idempotency_key = f"TICKET::{order['order_id']}"

    return TradeTicket(
        ticket_id=f"TT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{sequence:03d}",
        idempotency_key=idempotency_key,
        order_id=order["order_id"],
        timestamp=now_utc(),
        portfolio_id=order.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
        strategy=strategy,
        ticker=order["ticker"],
        action=order["action"],
        target_weight=float(order["target_weight"]),
        current_weight=float(order["current_weight"]),
        trade_size=round(trade_size, 6),
        quantity_pct=float(order["quantity_pct"]),
        priority=order.get("priority", "MEDIUM"),
        reason=order.get("reason", "Portfolio Rebalance"),
    )


def publish_ticket_to_redis(ticket: TradeTicket) -> None:
    r = get_redis_client()
    payload = asdict(ticket)

    r.xadd(
        TRADE_TICKETS_STREAM,
        {
            "event_type": "trade_ticket",
            "payload": json.dumps(payload),
            "ticker": ticket.ticker,
            "action": ticket.action,
            "status": ticket.status,
            "priority": ticket.priority,
            "idempotency_key": ticket.idempotency_key,
            "timestamp": ticket.timestamp,
        },
    )


def run_trade_ticket_engine() -> List[Dict[str, Any]]:
    orders = load_orders_from_redis()
    processed_order_ids = load_processed_order_ids()
    existing_tickets = load_existing_tickets()

    new_tickets: List[TradeTicket] = []
    sequence_start = len(existing_tickets) + 1

    for order in orders:
        order_id = order["order_id"]

        if order_id in processed_order_ids:
            continue

        ticket = create_trade_ticket(order, sequence=len(new_tickets) + sequence_start)
        new_tickets.append(ticket)
        processed_order_ids.add(order_id)

    new_ticket_dicts = [asdict(ticket) for ticket in new_tickets]
    all_tickets = existing_tickets + new_ticket_dicts

    save_json(OUTPUT_DIR / "trade_tickets.json", all_tickets)
    save_processed_order_ids(processed_order_ids)

    for ticket in new_tickets:
        publish_ticket_to_redis(ticket)

    return new_ticket_dicts


def main() -> None:
    print("=" * 80)
    print("AURUM TRADE TICKET ENGINE - IDEMPOTENT")
    print("=" * 80)

    tickets = run_trade_ticket_engine()

    if not tickets:
        print("No new trade tickets generated. Previously processed orders skipped.")
        return

    for ticket in tickets:
        print(
            f"{ticket['ticket_id']} | {ticket['action']} {ticket['ticker']} "
            f"{ticket['quantity_pct']:.2%} | status={ticket['status']}"
        )

    print("-" * 80)
    print(f"New tickets generated: {len(tickets)}")
    print(f"Saved: {OUTPUT_DIR / 'trade_tickets.json'}")
    print(f"State: {PROCESSED_ORDERS_PATH}")
    print(f"Redis stream: {TRADE_TICKETS_STREAM}")


if __name__ == "__main__":
    main()