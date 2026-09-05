import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


RESULTS_DIR = Path("results/optimization")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RESULTS_DIR / "regime_allocation_policy.json"


REGIME_ALLOCATION_POLICY = {
    "risk_on": {
        "target_weights": {
            "SPY": 0.28,
            "QQQ": 0.32,
            "DIA": 0.15,
            "TLT": 0.08,
            "GLD": 0.07,
            "CASH": 0.10,
        },
        "risk_budget": {
            "equity": 0.75,
            "fixed_income": 0.08,
            "commodity": 0.07,
            "cash": 0.10,
        },
        "rebalance_urgency": "medium",
        "rebalance_strength": 0.70,
        "max_turnover": 0.25,
    },
    "neutral": {
        "target_weights": {
            "SPY": 0.25,
            "QQQ": 0.25,
            "DIA": 0.15,
            "TLT": 0.15,
            "GLD": 0.10,
            "CASH": 0.10,
        },
        "risk_budget": {
            "equity": 0.65,
            "fixed_income": 0.15,
            "commodity": 0.10,
            "cash": 0.10,
        },
        "rebalance_urgency": "low",
        "rebalance_strength": 0.50,
        "max_turnover": 0.15,
    },
    "defensive": {
        "target_weights": {
            "SPY": 0.18,
            "QQQ": 0.17,
            "DIA": 0.13,
            "TLT": 0.22,
            "GLD": 0.15,
            "CASH": 0.15,
        },
        "risk_budget": {
            "equity": 0.48,
            "fixed_income": 0.22,
            "commodity": 0.15,
            "cash": 0.15,
        },
        "rebalance_urgency": "high",
        "rebalance_strength": 0.85,
        "max_turnover": 0.35,
    },
    "crisis": {
        "target_weights": {
            "SPY": 0.10,
            "QQQ": 0.08,
            "DIA": 0.10,
            "TLT": 0.28,
            "GLD": 0.19,
            "CASH": 0.25,
        },
        "risk_budget": {
            "equity": 0.28,
            "fixed_income": 0.28,
            "commodity": 0.19,
            "cash": 0.25,
        },
        "rebalance_urgency": "critical",
        "rebalance_strength": 1.00,
        "max_turnover": 0.50,
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_regime_allocation_policy(regime: str) -> Dict[str, Any]:
    regime = (regime or "neutral").lower()

    if regime not in REGIME_ALLOCATION_POLICY:
        regime = "neutral"

    policy = REGIME_ALLOCATION_POLICY[regime].copy()
    policy["regime"] = regime
    policy["timestamp"] = utc_now()
    policy["event_type"] = "regime_allocation_policy"

    return policy


def save_policy(policy: Dict[str, Any]) -> None:
    OUTPUT_PATH.write_text(json.dumps(policy, indent=2), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM REGIME ALLOCATION ENGINE")
    print("=" * 80)

    for regime in ["risk_on", "neutral", "defensive", "crisis"]:
        policy = get_regime_allocation_policy(regime)

        print("-" * 80)
        print(f"REGIME: {regime.upper()}")
        print(f"Urgency: {policy['rebalance_urgency']}")
        print(f"Rebalance Strength: {policy['rebalance_strength']}")
        print(f"Max Turnover: {policy['max_turnover']:.2%}")

        print("Target Weights:")
        for asset, weight in policy["target_weights"].items():
            print(f"  {asset:<6} {weight:>8.2%}")

        print("Risk Budget:")
        for asset_class, budget in policy["risk_budget"].items():
            print(f"  {asset_class:<15} {budget:>8.2%}")

    latest_policy = get_regime_allocation_policy("defensive")
    save_policy(latest_policy)

    print("-" * 80)
    print(f"Saved sample policy: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()