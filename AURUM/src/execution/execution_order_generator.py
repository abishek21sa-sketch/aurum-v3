# src/execution/execution_order_generator.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OUTPUT_DIR = Path("results/execution")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXECUTION_ORDERS_STREAM = "execution_orders"


@dataclass
class ExecutionOrder:
    order_id: str
    timestamp: str
    portfolio_id: str
    ticker: str
    action: str
    quantity_pct: float
    current_weight: float
    target_weight: float
    priority: str
    reason: str
    status: str = "CREATED"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def load_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def infer_priority(abs_trade_size: float) -> str:
    if abs_trade_size >= 0.05:
        return "HIGH"
    if abs_trade_size >= 0.02:
        return "MEDIUM"
    return "LOW"


def generate_execution_orders(
    current_portfolio: Dict[str, float],
    target_portfolio: Dict[str, float],
    portfolio_id: str = "AURUM_LIVE_PORTFOLIO",
    reason: str = "Portfolio Rebalance",
    min_trade_pct: float = 0.005,
) -> List[ExecutionOrder]:
    tickers = sorted(set(current_portfolio) | set(target_portfolio))
    orders: List[ExecutionOrder] = []

    timestamp = now_utc()
    order_counter = 1

    for ticker in tickers:
        if ticker.upper() in {"CASH", "USD"}:
            continue

        current_weight = float(current_portfolio.get(ticker, 0.0))
        target_weight = float(target_portfolio.get(ticker, 0.0))
        trade_size = target_weight - current_weight

        if abs(trade_size) < min_trade_pct:
            continue

        action = "BUY" if trade_size > 0 else "SELL"
        quantity_pct = round(abs(trade_size), 6)

        order = ExecutionOrder(
            order_id=f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{order_counter:03d}",
            timestamp=timestamp,
            portfolio_id=portfolio_id,
            ticker=ticker,
            action=action,
            quantity_pct=quantity_pct,
            current_weight=round(current_weight, 6),
            target_weight=round(target_weight, 6),
            priority=infer_priority(abs(trade_size)),
            reason=reason,
        )

        orders.append(order)
        order_counter += 1

    return orders


def publish_orders_to_redis(orders: List[ExecutionOrder]) -> None:
    r = get_redis_client()

    for order in orders:
        payload = asdict(order)
        r.xadd(
            EXECUTION_ORDERS_STREAM,
            {
                "event_type": "execution_order",
                "payload": json.dumps(payload),
                "ticker": order.ticker,
                "action": order.action,
                "priority": order.priority,
                "timestamp": order.timestamp,
            },
        )


def run_execution_order_generator() -> List[Dict[str, Any]]:
    current_portfolio = load_json(
        "results/portfolio/current_portfolio.json",
        default={
            "SPY": 0.25,
            "QQQ": 0.25,
            "TLT": 0.15,
            "GLD": 0.10,
            "BTC-USD": 0.05,
            "cash": 0.20,
        },
    )

    target_portfolio = load_json(
        "results/optimization/optimized_portfolio.json",
        default={
            "SPY": 0.1905,
            "QQQ": 0.1820,
            "TLT": 0.2095,
            "GLD": 0.1425,
            "BTC-USD": 0.0255,
            "cash": 0.25,
        },
    )

    if "weights" in target_portfolio:
        target_portfolio = target_portfolio["weights"]

    orders = generate_execution_orders(
        current_portfolio=current_portfolio,
        target_portfolio=target_portfolio,
        reason="Defensive Rebalance",
    )

    order_dicts = [asdict(order) for order in orders]

    save_json(OUTPUT_DIR / "execution_orders.json", order_dicts)
    publish_orders_to_redis(orders)

    return order_dicts


def main() -> None:
    print("=" * 80)
    print("AURUM EXECUTION ORDER GENERATOR")
    print("=" * 80)

    orders = run_execution_order_generator()

    if not orders:
        print("No executable orders generated.")
        return

    for order in orders:
        print(
            f"{order['order_id']} | {order['action']} {order['ticker']} "
            f"{order['quantity_pct']:.2%} | priority={order['priority']}"
        )

    print("-" * 80)
    print(f"Orders generated: {len(orders)}")
    print(f"Saved: {OUTPUT_DIR / 'execution_orders.json'}")
    print(f"Redis stream: {EXECUTION_ORDERS_STREAM}")


if __name__ == "__main__":
    main()