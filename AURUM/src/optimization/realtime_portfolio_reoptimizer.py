import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import redis

from src.optimization.regime_allocation_engine import get_regime_allocation_policy


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

PORTFOLIO_STATE_STREAM = "portfolio_state"
MARKET_SIGNALS_STREAM = "market_signals"
RISK_EVENTS_STREAM = "risk_events"
OPTIMIZER_EVENTS_STREAM = "optimizer_events"
OPTIMIZED_PORTFOLIO_STREAM = "optimized_portfolio"

RESULTS_DIR = Path("results/optimization")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RESULTS_DIR / "realtime_optimized_portfolio.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )


def parse_payload(entry: Dict[str, Any]) -> Dict[str, Any]:
    payload = entry.get("payload")

    if payload:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {}

    return entry


def read_latest_stream_event(client: redis.Redis, stream: str) -> Dict[str, Any]:
    events = client.xrevrange(stream, count=1)

    if not events:
        return {}

    _, event_data = events[0]
    return parse_payload(event_data)


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(float(v) for v in weights.values())

    if total <= 0:
        return weights

    return {
        asset: round(float(weight) / total, 6)
        for asset, weight in weights.items()
    }


def detect_regime(
    market_signal: Dict[str, Any],
    risk_event: Dict[str, Any],
) -> str:
    regime = (
        market_signal.get("regime")
        or market_signal.get("current_regime")
        or market_signal.get("regime_label")
        or market_signal.get("decision")
    )

    if isinstance(regime, str):
        regime = regime.lower()

        if "crisis" in regime or "critical" in regime:
            return "crisis"
        if "defensive" in regime or "risk_off" in regime:
            return "defensive"
        if "risk_on" in regime or "bull" in regime:
            return "risk_on"
        if "neutral" in regime or "normal" in regime:
            return "neutral"

    stress_score = (
        risk_event.get("market_stress_score")
        or risk_event.get("stress_score")
        or risk_event.get("risk_score")
        or 0.0
    )

    try:
        stress_score = float(stress_score)
    except Exception:
        stress_score = 0.0

    if stress_score >= 0.85:
        return "crisis"
    if stress_score >= 0.60:
        return "defensive"
    if stress_score <= 0.25:
        return "risk_on"

    return "neutral"


def blend_with_current(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    rebalance_strength: float,
) -> Dict[str, float]:
    assets = sorted(set(current_weights) | set(target_weights))
    blended = {}

    for asset in assets:
        current = float(current_weights.get(asset, 0.0))
        target = float(target_weights.get(asset, 0.0))
        blended[asset] = current + rebalance_strength * (target - current)

    return normalize_weights(blended)


def calculate_rebalance_trades(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
) -> Dict[str, float]:
    assets = sorted(set(current_weights) | set(target_weights))

    return {
        asset: round(
            float(target_weights.get(asset, 0.0))
            - float(current_weights.get(asset, 0.0)),
            6,
        )
        for asset in assets
    }


def calculate_turnover(trades: Dict[str, float]) -> float:
    return round(sum(abs(v) for v in trades.values()) / 2.0, 6)


def estimate_transaction_cost(turnover: float, cost_bps: float = 5.0) -> float:
    return round(turnover * (cost_bps / 10_000), 8)


def build_optimized_portfolio() -> Dict[str, Any]:
    client = get_redis_client()

    portfolio_state = read_latest_stream_event(client, PORTFOLIO_STATE_STREAM)
    market_signal = read_latest_stream_event(client, MARKET_SIGNALS_STREAM)
    risk_event = read_latest_stream_event(client, RISK_EVENTS_STREAM)
    optimizer_event = read_latest_stream_event(client, OPTIMIZER_EVENTS_STREAM)

    current_weights = portfolio_state.get("current_weights", {})

    if not current_weights:
        current_weights = {
            "SPY": 0.25,
            "QQQ": 0.25,
            "DIA": 0.15,
            "TLT": 0.15,
            "GLD": 0.10,
            "CASH": 0.10,
        }

    current_weights = normalize_weights(current_weights)

    regime = detect_regime(market_signal, risk_event)

    allocation_policy = get_regime_allocation_policy(regime)

    base_target = allocation_policy["target_weights"]
    rebalance_strength = allocation_policy["rebalance_strength"]
    max_turnover = allocation_policy["max_turnover"]
    rebalance_urgency = allocation_policy["rebalance_urgency"]
    risk_budget = allocation_policy["risk_budget"]

    target_weights = blend_with_current(
        current_weights=current_weights,
        target_weights=base_target,
        rebalance_strength=rebalance_strength,
    )

    trades = calculate_rebalance_trades(current_weights, target_weights)
    turnover = calculate_turnover(trades)
    transaction_cost = estimate_transaction_cost(turnover)

    turnover_status = "within_limit" if turnover <= max_turnover else "above_limit"

    optimized = {
        "event_type": "optimized_portfolio",
        "timestamp": utc_now(),
        "portfolio_id": portfolio_state.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
        "regime": regime,
        "optimizer": {
            "method": "regime_aware_realtime_reoptimizer",
            "status": "success",
        },
        "inputs": {
            "portfolio_state_timestamp": portfolio_state.get("timestamp"),
            "market_signal_type": market_signal.get("event_type"),
            "risk_event_type": risk_event.get("event_type"),
            "optimizer_event_type": optimizer_event.get("event_type"),
        },
        "allocation_policy": {
            "rebalance_urgency": rebalance_urgency,
            "rebalance_strength": rebalance_strength,
            "max_turnover": max_turnover,
            "risk_budget": risk_budget,
        },
        "current_weights": current_weights,
        "base_regime_target": base_target,
        "recommended_weights": target_weights,
        "rebalance_trades": trades,
        "execution_summary": {
            "turnover": turnover,
            "max_turnover": max_turnover,
            "turnover_status": turnover_status,
            "estimated_transaction_cost": transaction_cost,
            "cost_bps": 5.0,
        },
    }

    return optimized


def publish_optimized_portfolio(client: redis.Redis, optimized: Dict[str, Any]) -> str:
    return client.xadd(
        OPTIMIZED_PORTFOLIO_STREAM,
        {
            "event_type": optimized["event_type"],
            "timestamp": optimized["timestamp"],
            "portfolio_id": optimized["portfolio_id"],
            "regime": optimized["regime"],
            "payload": json.dumps(optimized),
        },
    )


def save_to_disk(optimized: Dict[str, Any]) -> None:
    OUTPUT_PATH.write_text(json.dumps(optimized, indent=2), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM REAL-TIME PORTFOLIO REOPTIMIZER")
    print("=" * 80)

    client = get_redis_client()
    optimized = build_optimized_portfolio()

    save_to_disk(optimized)

    try:
        event_id = publish_optimized_portfolio(client, optimized)
        redis_status = (
            f"published to Redis stream '{OPTIMIZED_PORTFOLIO_STREAM}' "
            f"| event_id={event_id}"
        )
    except Exception as exc:
        redis_status = f"Redis publish failed: {exc}"

    print(f"Portfolio ID: {optimized['portfolio_id']}")
    print(f"Timestamp: {optimized['timestamp']}")
    print(f"Detected Regime: {optimized['regime']}")
    print(f"Optimizer Method: {optimized['optimizer']['method']}")
    print(f"Rebalance Urgency: {optimized['allocation_policy']['rebalance_urgency']}")
    print("-" * 80)

    print("CURRENT PORTFOLIO")
    for asset, weight in optimized["current_weights"].items():
        print(f"{asset:<6} {weight:>8.2%}")

    print("-" * 80)
    print("RECOMMENDED PORTFOLIO")
    for asset, weight in optimized["recommended_weights"].items():
        print(f"{asset:<6} {weight:>8.2%}")

    print("-" * 80)
    print("REBALANCE TRADES")
    for asset, trade in optimized["rebalance_trades"].items():
        sign = "+" if trade >= 0 else ""
        print(f"{asset:<6} {sign}{trade:>8.2%}")

    print("-" * 80)
    print(f"Turnover: {optimized['execution_summary']['turnover']:.2%}")
    print(f"Max Turnover: {optimized['execution_summary']['max_turnover']:.2%}")
    print(f"Turnover Status: {optimized['execution_summary']['turnover_status']}")
    print(
        "Estimated Transaction Cost: "
        f"{optimized['execution_summary']['estimated_transaction_cost']:.6f}"
    )
    print(redis_status)
    print(f"Saved optimized portfolio: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()