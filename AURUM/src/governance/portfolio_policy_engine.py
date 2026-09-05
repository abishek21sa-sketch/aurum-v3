from pathlib import Path
import json
from datetime import datetime


RESULTS_DIR = Path("results/governance")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def build_policy_constraints() -> dict:
    return {
        "policy_name": "AURUM Institutional Portfolio Policy",
        "generated_at": datetime.now().isoformat(),
        "asset_class_limits": {
            "equity": {"min": 0.20, "max": 0.70},
            "bond": {"min": 0.05, "max": 0.40},
            "commodity": {"min": 0.00, "max": 0.20},
            "crypto": {"min": 0.00, "max": 0.10},
            "cash": {"min": 0.02, "max": 0.25},
        },
        "single_asset_limits": {
            "max_single_asset_weight": 0.30,
            "max_crypto_asset_weight": 0.08,
            "max_cash_weight": 0.25,
        },
        "portfolio_risk_limits": {
            "max_drawdown_warning": -0.05,
            "max_drawdown_hedge": -0.10,
            "max_drawdown_derisk": -0.15,
            "max_drawdown_emergency": -0.20,
            "max_annualized_volatility": 0.20,
            "min_sharpe_ratio": 0.50,
        },
        "liquidity_policy": {
            "minimum_cash_buffer": 0.02,
            "preferred_cash_buffer": 0.05,
            "liquidity_stress_cash_buffer": 0.10,
        },
        "governance_rules": {
            "requires_committee_review_if_non_compliant": True,
            "block_execution_on_critical_violation": True,
            "allow_execution_with_warnings": True,
        },
    }


def save_policy_constraints(policy: dict) -> None:
    output_path = RESULTS_DIR / "policy_constraints.json"
    output_path.write_text(json.dumps(policy, indent=4), encoding="utf-8")


def run_portfolio_policy_engine() -> dict:
    policy = build_policy_constraints()
    save_policy_constraints(policy)
    return policy


def main() -> None:
    print("=" * 80)
    print("AURUM PORTFOLIO POLICY ENGINE")
    print("=" * 80)

    policy = run_portfolio_policy_engine()

    print("\nPOLICY CREATED")
    print("-" * 80)
    print(f"Policy name: {policy['policy_name']}")
    print(f"Asset class policies: {len(policy['asset_class_limits'])}")
    print(f"Risk limit policies: {len(policy['portfolio_risk_limits'])}")
    print(f"Output: results/governance/policy_constraints.json")


if __name__ == "__main__":
    main()