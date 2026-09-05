# src/portfolio/realtime_portfolio_state_engine.py

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import redis


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

PORTFOLIO_STATE_STREAM = "portfolio_state"
PORTFOLIO_DECISIONS_STREAM = "portfolio_decisions"

RESULTS_DIR = Path("results/portfolio")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

STATE_PATH = RESULTS_DIR / "realtime_portfolio_state.json"


DEFAULT_PORTFOLIO = {
    "SPY": 0.25,
    "QQQ": 0.25,
    "DIA": 0.15,
    "TLT": 0.15,
    "GLD": 0.10,
    "CASH": 0.10,
}


ASSET_CLASS_MAP = {
    "SPY": "equity",
    "QQQ": "equity",
    "DIA": "equity",
    "TLT": "fixed_income",
    "GLD": "commodity",
    "BTC": "crypto",
    "ETH": "crypto",
    "CASH": "cash",
}


RISK_BUDGET_MAP = {
    "equity": 0.55,
    "fixed_income": 0.20,
    "commodity": 0.10,
    "crypto": 0.05,
    "cash": 0.10,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(float(v) for v in weights.values())

    if total <= 0:
        return DEFAULT_PORTFOLIO.copy()

    return {
        asset: round(float(weight) / total, 6)
        for asset, weight in weights.items()
    }


def calculate_asset_class_exposure(weights: Dict[str, float]) -> Dict[str, float]:
    exposure = {}

    for asset, weight in weights.items():
        asset_class = ASSET_CLASS_MAP.get(asset, "other")
        exposure[asset_class] = exposure.get(asset_class, 0.0) + float(weight)

    return {
        asset_class: round(value, 6)
        for asset_class, value in exposure.items()
    }


def calculate_risk_budget_usage(asset_class_exposure: Dict[str, float]) -> Dict[str, Any]:
    usage = {}

    for asset_class, exposure in asset_class_exposure.items():
        budget = RISK_BUDGET_MAP.get(asset_class, 0.0)

        if budget > 0:
            utilization = exposure / budget
        else:
            utilization = None

        usage[asset_class] = {
            "exposure": round(exposure, 6),
            "budget": round(budget, 6),
            "utilization": round(utilization, 6) if utilization is not None else None,
            "status": (
                "over_budget"
                if utilization is not None and utilization > 1.05
                else "within_budget"
            ),
        }

    return usage


def calculate_portfolio_summary(weights: Dict[str, float]) -> Dict[str, Any]:
    cash_weight = weights.get("CASH", 0.0)
    invested_weight = 1.0 - cash_weight

    equity_weight = sum(
        weight
        for asset, weight in weights.items()
        if ASSET_CLASS_MAP.get(asset) == "equity"
    )

    defensive_weight = sum(
        weight
        for asset, weight in weights.items()
        if ASSET_CLASS_MAP.get(asset) in {"fixed_income", "commodity", "cash"}
    )

    return {
        "cash_weight": round(cash_weight, 6),
        "invested_weight": round(invested_weight, 6),
        "equity_weight": round(equity_weight, 6),
        "defensive_weight": round(defensive_weight, 6),
        "gross_exposure": round(sum(abs(v) for v in weights.values()), 6),
        "net_exposure": round(sum(weights.values()), 6),
        "number_of_positions": len([v for v in weights.values() if abs(v) > 1e-6]),
    }


def build_realtime_portfolio_state(
    current_weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    weights = normalize_weights(current_weights or DEFAULT_PORTFOLIO)

    asset_class_exposure = calculate_asset_class_exposure(weights)
    risk_budget_usage = calculate_risk_budget_usage(asset_class_exposure)
    portfolio_summary = calculate_portfolio_summary(weights)

    state = {
        "event_type": "realtime_portfolio_state",
        "timestamp": utc_now(),
        "portfolio_id": "AURUM_LIVE_PORTFOLIO",
        "current_weights": weights,
        "asset_class_exposure": asset_class_exposure,
        "risk_budget_usage": risk_budget_usage,
        "portfolio_summary": portfolio_summary,
        "state_quality": {
            "source": "default_live_state_engine",
            "is_normalized": True,
            "weight_sum": round(sum(weights.values()), 6),
        },
    }

    return state


def publish_state_to_redis(state: Dict[str, Any]) -> str:
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    event_id = client.xadd(
        PORTFOLIO_STATE_STREAM,
        {
            "event_type": state["event_type"],
            "timestamp": state["timestamp"],
            "portfolio_id": state["portfolio_id"],
            "payload": json.dumps(state),
        },
    )

    return event_id


def save_state_to_disk(state: Dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM REAL-TIME PORTFOLIO STATE ENGINE")
    print("=" * 80)

    state = build_realtime_portfolio_state()

    save_state_to_disk(state)

    try:
        event_id = publish_state_to_redis(state)
        redis_status = f"published to Redis stream '{PORTFOLIO_STATE_STREAM}' | event_id={event_id}"
    except Exception as exc:
        redis_status = f"Redis publish failed: {exc}"

    print(f"Portfolio ID: {state['portfolio_id']}")
    print(f"Timestamp: {state['timestamp']}")
    print("-" * 80)
    print("CURRENT WEIGHTS")
    for asset, weight in state["current_weights"].items():
        print(f"{asset:<6} {weight:>8.2%}")

    print("-" * 80)
    print("ASSET CLASS EXPOSURE")
    for asset_class, exposure in state["asset_class_exposure"].items():
        print(f"{asset_class:<15} {exposure:>8.2%}")

    print("-" * 80)
    print("PORTFOLIO SUMMARY")
    for key, value in state["portfolio_summary"].items():
        print(f"{key:<25} {value}")

    print("-" * 80)
    print(redis_status)
    print(f"Saved state: {STATE_PATH}")


if __name__ == "__main__":
    main()