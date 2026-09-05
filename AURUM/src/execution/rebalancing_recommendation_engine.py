import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import redis


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

OPTIMIZED_PORTFOLIO_STREAM = "optimized_portfolio"
REBALANCING_RECOMMENDATIONS_STREAM = "rebalancing_recommendations"

RESULTS_DIR = Path("results/execution")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RESULTS_DIR / "rebalancing_recommendations.json"


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


def classify_trade_action(weight_change: float, threshold: float = 0.0025) -> str:
    if weight_change > threshold:
        return "increase"
    if weight_change < -threshold:
        return "reduce"
    return "hold"


def classify_trade_size(abs_change: float) -> str:
    if abs_change >= 0.075:
        return "large"
    if abs_change >= 0.035:
        return "medium"
    if abs_change >= 0.01:
        return "small"
    return "minimal"


def build_trade_recommendations(optimized: Dict[str, Any]) -> Dict[str, Any]:
    current_weights = optimized.get("current_weights", {})
    recommended_weights = optimized.get("recommended_weights", {})
    rebalance_trades = optimized.get("rebalance_trades", {})

    recommendations = []

    for asset in sorted(set(current_weights) | set(recommended_weights) | set(rebalance_trades)):
        current_weight = float(current_weights.get(asset, 0.0))
        target_weight = float(recommended_weights.get(asset, 0.0))
        trade_weight = float(rebalance_trades.get(asset, target_weight - current_weight))

        action = classify_trade_action(trade_weight)
        trade_size = classify_trade_size(abs(trade_weight))

        recommendations.append(
            {
                "asset": asset,
                "current_weight": round(current_weight, 6),
                "target_weight": round(target_weight, 6),
                "trade_weight": round(trade_weight, 6),
                "action": action,
                "trade_size": trade_size,
                "priority": (
                    "high"
                    if trade_size in {"large", "medium"} and action != "hold"
                    else "normal"
                ),
            }
        )

    return {
        "recommendations": recommendations,
        "number_of_recommendations": len(recommendations),
    }


def build_rebalancing_recommendation() -> Dict[str, Any]:
    client = get_redis_client()
    optimized = read_latest_stream_event(client, OPTIMIZED_PORTFOLIO_STREAM)

    if not optimized:
        raise RuntimeError(
            "No optimized portfolio found. Run "
            "`python -m src.optimization.realtime_portfolio_reoptimizer` first."
        )

    trade_block = build_trade_recommendations(optimized)

    execution_summary = optimized.get("execution_summary", {})
    allocation_policy = optimized.get("allocation_policy", {})

    turnover = float(execution_summary.get("turnover", 0.0))
    max_turnover = float(execution_summary.get("max_turnover", 0.0))
    estimated_transaction_cost = float(
        execution_summary.get("estimated_transaction_cost", 0.0)
    )

    if turnover <= 0.01:
        execution_decision = "no_rebalance_required"
    elif max_turnover and turnover > max_turnover:
        execution_decision = "rebalance_blocked_turnover_limit"
    else:
        execution_decision = "rebalance_recommended"

    recommendation = {
        "event_type": "rebalancing_recommendation",
        "timestamp": utc_now(),
        "portfolio_id": optimized.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
        "regime": optimized.get("regime", "unknown"),
        "rebalance_urgency": allocation_policy.get("rebalance_urgency", "unknown"),
        "execution_decision": execution_decision,
        "trade_recommendations": trade_block["recommendations"],
        "summary": {
            "number_of_recommendations": trade_block["number_of_recommendations"],
            "turnover": turnover,
            "max_turnover": max_turnover,
            "turnover_status": execution_summary.get("turnover_status"),
            "estimated_transaction_cost": estimated_transaction_cost,
            "cost_bps": execution_summary.get("cost_bps", 5.0),
        },
        "source": {
            "optimized_portfolio_timestamp": optimized.get("timestamp"),
            "optimizer_method": optimized.get("optimizer", {}).get("method"),
        },
    }

    return recommendation


def publish_recommendation(client: redis.Redis, recommendation: Dict[str, Any]) -> str:
    return client.xadd(
        REBALANCING_RECOMMENDATIONS_STREAM,
        {
            "event_type": recommendation["event_type"],
            "timestamp": recommendation["timestamp"],
            "portfolio_id": recommendation["portfolio_id"],
            "regime": recommendation["regime"],
            "execution_decision": recommendation["execution_decision"],
            "payload": json.dumps(recommendation),
        },
    )


def save_to_disk(recommendation: Dict[str, Any]) -> None:
    OUTPUT_PATH.write_text(json.dumps(recommendation, indent=2), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM REBALANCING RECOMMENDATION ENGINE")
    print("=" * 80)

    client = get_redis_client()
    recommendation = build_rebalancing_recommendation()

    save_to_disk(recommendation)

    try:
        event_id = publish_recommendation(client, recommendation)
        redis_status = (
            f"published to Redis stream '{REBALANCING_RECOMMENDATIONS_STREAM}' "
            f"| event_id={event_id}"
        )
    except Exception as exc:
        redis_status = f"Redis publish failed: {exc}"

    print(f"Portfolio ID: {recommendation['portfolio_id']}")
    print(f"Timestamp: {recommendation['timestamp']}")
    print(f"Regime: {recommendation['regime']}")
    print(f"Rebalance Urgency: {recommendation['rebalance_urgency']}")
    print(f"Execution Decision: {recommendation['execution_decision']}")
    print("-" * 80)

    print("TRADE RECOMMENDATIONS")
    for rec in recommendation["trade_recommendations"]:
        sign = "+" if rec["trade_weight"] >= 0 else ""
        print(
            f"{rec['asset']:<6} "
            f"{rec['action']:<8} "
            f"{sign}{rec['trade_weight']:>8.2%} "
            f"| current={rec['current_weight']:>7.2%} "
            f"target={rec['target_weight']:>7.2%} "
            f"| size={rec['trade_size']:<7} "
            f"priority={rec['priority']}"
        )

    print("-" * 80)
    print(f"Turnover: {recommendation['summary']['turnover']:.2%}")
    print(f"Max Turnover: {recommendation['summary']['max_turnover']:.2%}")
    print(f"Turnover Status: {recommendation['summary']['turnover_status']}")
    print(
        "Estimated Transaction Cost: "
        f"{recommendation['summary']['estimated_transaction_cost']:.6f}"
    )
    print(redis_status)
    print(f"Saved recommendation: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()