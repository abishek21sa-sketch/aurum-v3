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
PORTFOLIO_SIMULATION_STREAM = "portfolio_simulation"

RESULTS_DIR = Path("results/simulation")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RESULTS_DIR / "portfolio_rebalance_simulation.json"


ASSET_ASSUMPTIONS = {
    "SPY": {"expected_return": 0.085, "volatility": 0.165, "cvar": 0.235, "max_drawdown": 0.230},
    "QQQ": {"expected_return": 0.110, "volatility": 0.230, "cvar": 0.320, "max_drawdown": 0.310},
    "DIA": {"expected_return": 0.075, "volatility": 0.145, "cvar": 0.210, "max_drawdown": 0.200},
    "TLT": {"expected_return": 0.040, "volatility": 0.135, "cvar": 0.170, "max_drawdown": 0.160},
    "GLD": {"expected_return": 0.055, "volatility": 0.155, "cvar": 0.190, "max_drawdown": 0.170},
    "CASH": {"expected_return": 0.030, "volatility": 0.005, "cvar": 0.002, "max_drawdown": 0.001},
}


CORRELATION_PENALTY = {
    "risk_on": 1.10,
    "neutral": 1.00,
    "defensive": 0.92,
    "crisis": 0.85,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_redis_client() -> redis.Redis:
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


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


def portfolio_expected_return(weights: Dict[str, float]) -> float:
    return sum(
        float(weight) * ASSET_ASSUMPTIONS.get(asset, ASSET_ASSUMPTIONS["CASH"])["expected_return"]
        for asset, weight in weights.items()
    )


def portfolio_volatility(weights: Dict[str, float], regime: str) -> float:
    weighted_vol = sum(
        abs(float(weight)) * ASSET_ASSUMPTIONS.get(asset, ASSET_ASSUMPTIONS["CASH"])["volatility"]
        for asset, weight in weights.items()
    )

    diversification_discount = 0.58
    regime_penalty = CORRELATION_PENALTY.get(regime, 1.0)

    return weighted_vol * diversification_discount * regime_penalty


def portfolio_cvar(weights: Dict[str, float], regime: str) -> float:
    weighted_cvar = sum(
        abs(float(weight)) * ASSET_ASSUMPTIONS.get(asset, ASSET_ASSUMPTIONS["CASH"])["cvar"]
        for asset, weight in weights.items()
    )

    regime_penalty = CORRELATION_PENALTY.get(regime, 1.0)

    return weighted_cvar * regime_penalty


def portfolio_max_drawdown(weights: Dict[str, float], regime: str) -> float:
    weighted_dd = sum(
        abs(float(weight)) * ASSET_ASSUMPTIONS.get(asset, ASSET_ASSUMPTIONS["CASH"])["max_drawdown"]
        for asset, weight in weights.items()
    )

    regime_penalty = CORRELATION_PENALTY.get(regime, 1.0)

    return weighted_dd * regime_penalty


def calculate_metrics(weights: Dict[str, float], regime: str) -> Dict[str, float]:
    expected_return = portfolio_expected_return(weights)
    volatility = portfolio_volatility(weights, regime)
    cvar = portfolio_cvar(weights, regime)
    max_drawdown = portfolio_max_drawdown(weights, regime)

    sharpe = expected_return / volatility if volatility > 0 else 0.0

    return {
        "expected_return": round(expected_return, 6),
        "volatility": round(volatility, 6),
        "sharpe": round(sharpe, 6),
        "cvar": round(cvar, 6),
        "max_drawdown": round(max_drawdown, 6),
    }


def compare_metrics(current: Dict[str, float], recommended: Dict[str, float]) -> Dict[str, Any]:
    return {
        "expected_return_change": round(
            recommended["expected_return"] - current["expected_return"], 6
        ),
        "volatility_change": round(
            recommended["volatility"] - current["volatility"], 6
        ),
        "sharpe_change": round(
            recommended["sharpe"] - current["sharpe"], 6
        ),
        "cvar_change": round(
            recommended["cvar"] - current["cvar"], 6
        ),
        "max_drawdown_change": round(
            recommended["max_drawdown"] - current["max_drawdown"], 6
        ),
        "risk_reduction": {
            "volatility_reduction": round(
                current["volatility"] - recommended["volatility"], 6
            ),
            "cvar_reduction": round(
                current["cvar"] - recommended["cvar"], 6
            ),
            "drawdown_reduction": round(
                current["max_drawdown"] - recommended["max_drawdown"], 6
            ),
        },
    }


def build_simulation() -> Dict[str, Any]:
    client = get_redis_client()

    optimized = read_latest_stream_event(client, OPTIMIZED_PORTFOLIO_STREAM)
    recommendation = read_latest_stream_event(client, REBALANCING_RECOMMENDATIONS_STREAM)

    if not optimized:
        raise RuntimeError(
            "No optimized portfolio found. Run "
            "`python -m src.optimization.realtime_portfolio_reoptimizer` first."
        )

    current_weights = optimized.get("current_weights", {})
    recommended_weights = optimized.get("recommended_weights", {})
    regime = optimized.get("regime", "neutral")

    current_metrics = calculate_metrics(current_weights, regime)
    recommended_metrics = calculate_metrics(recommended_weights, regime)
    improvement = compare_metrics(current_metrics, recommended_metrics)

    simulation = {
        "event_type": "portfolio_rebalance_simulation",
        "timestamp": utc_now(),
        "portfolio_id": optimized.get("portfolio_id", "AURUM_LIVE_PORTFOLIO"),
        "regime": regime,
        "simulation_method": "deterministic_regime_adjusted_assumption_model",
        "current_portfolio": {
            "weights": current_weights,
            "metrics": current_metrics,
        },
        "recommended_portfolio": {
            "weights": recommended_weights,
            "metrics": recommended_metrics,
        },
        "improvement": improvement,
        "execution_context": {
            "execution_decision": recommendation.get("execution_decision"),
            "rebalance_urgency": recommendation.get("rebalance_urgency"),
            "turnover": optimized.get("execution_summary", {}).get("turnover"),
            "estimated_transaction_cost": optimized.get("execution_summary", {}).get(
                "estimated_transaction_cost"
            ),
        },
        "source": {
            "optimized_portfolio_timestamp": optimized.get("timestamp"),
            "recommendation_timestamp": recommendation.get("timestamp"),
        },
    }

    return simulation


def publish_simulation(client: redis.Redis, simulation: Dict[str, Any]) -> str:
    return client.xadd(
        PORTFOLIO_SIMULATION_STREAM,
        {
            "event_type": simulation["event_type"],
            "timestamp": simulation["timestamp"],
            "portfolio_id": simulation["portfolio_id"],
            "regime": simulation["regime"],
            "payload": json.dumps(simulation),
        },
    )


def save_to_disk(simulation: Dict[str, Any]) -> None:
    OUTPUT_PATH.write_text(json.dumps(simulation, indent=2), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO REBALANCE SIMULATION ENGINE")
    print("=" * 80)

    client = get_redis_client()
    simulation = build_simulation()

    save_to_disk(simulation)

    try:
        event_id = publish_simulation(client, simulation)
        redis_status = (
            f"published to Redis stream '{PORTFOLIO_SIMULATION_STREAM}' "
            f"| event_id={event_id}"
        )
    except Exception as exc:
        redis_status = f"Redis publish failed: {exc}"

    current = simulation["current_portfolio"]["metrics"]
    recommended = simulation["recommended_portfolio"]["metrics"]
    improvement = simulation["improvement"]

    print(f"Portfolio ID: {simulation['portfolio_id']}")
    print(f"Timestamp: {simulation['timestamp']}")
    print(f"Regime: {simulation['regime']}")
    print("-" * 80)

    print("CURRENT PORTFOLIO METRICS")
    for key, value in current.items():
        print(f"{key:<20} {value:>10.4f}")

    print("-" * 80)
    print("RECOMMENDED PORTFOLIO METRICS")
    for key, value in recommended.items():
        print(f"{key:<20} {value:>10.4f}")

    print("-" * 80)
    print("EXPECTED IMPROVEMENT")
    for key, value in improvement.items():
        if isinstance(value, dict):
            continue
        print(f"{key:<25} {value:>10.4f}")

    print("-" * 80)
    print("RISK REDUCTION")
    for key, value in improvement["risk_reduction"].items():
        print(f"{key:<25} {value:>10.4f}")

    print("-" * 80)
    print(redis_status)
    print(f"Saved simulation: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()