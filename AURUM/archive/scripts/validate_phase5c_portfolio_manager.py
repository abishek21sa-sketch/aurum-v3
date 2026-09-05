from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FILES = [
    Path("results/research/ai_portfolio_manager_plan.json"),
    Path("results/research/target_ai_portfolio.json"),
    Path("results/research/ai_portfolio_manager_explanation.txt"),
]


REQUIRED_ASSETS = [
    "SPY",
    "QQQ",
    "DIA",
    "TLT",
    "GLD",
    "BTC",
    "ETH",
    "VIX",
    "CASH",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(condition: bool, message: str) -> bool:
    if condition:
        print(f"[PASS] {message}")
        return True
    print(f"[FAIL] {message}")
    return False


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C AI PORTFOLIO MANAGER VALIDATION")
    print("=" * 80)

    passed = True

    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)
    try:
        import src.research.ai_portfolio_manager  # noqa: F401

        passed &= check(True, "import src.research.ai_portfolio_manager")
    except Exception as exc:
        passed &= check(False, f"import src.research.ai_portfolio_manager | {exc}")

    print("\nARTIFACT CHECKS")
    print("-" * 80)
    for path in REQUIRED_FILES:
        passed &= check(path.exists(), f"artifact exists: {path}")

    if all(path.exists() for path in REQUIRED_FILES):
        output = load_json(Path("results/research/ai_portfolio_manager_plan.json"))
        target = load_json(Path("results/research/target_ai_portfolio.json"))

        print("\nSCHEMA CHECKS")
        print("-" * 80)

        passed &= check(
            output.get("phase") == "5C",
            "phase is 5C",
        )

        passed &= check(
            output.get("component") == "AI Portfolio Manager",
            "component is AI Portfolio Manager",
        )

        passed &= check(
            bool(output.get("llm_backend")),
            "LLM backend recorded",
        )

        passed &= check(
            target.get("manager_view") in [
                "risk_on",
                "neutral",
                "defensive",
                "risk_off",
            ],
            "valid manager view",
        )

        passed &= check(
            target.get("execution_permission") in [
                "allowed",
                "review_required",
                "blocked",
            ],
            "valid execution permission",
        )

        passed &= check(
            target.get("portfolio_mode") in [
                "executable",
                "prepared_only",
                "blocked",
            ],
            "valid portfolio mode",
        )

        weights = target.get("target_weights", {})
        passed &= check(
            isinstance(weights, dict),
            "target weights dictionary present",
        )

        for asset in REQUIRED_ASSETS:
            passed &= check(
                asset in weights,
                f"target weight exists for {asset}",
            )

        if isinstance(weights, dict):
            try:
                total_weight = sum(float(weights.get(asset, 0.0)) for asset in REQUIRED_ASSETS)
                passed &= check(
                    0.95 <= total_weight <= 1.05,
                    f"target weights approximately sum to 1.0 | total={total_weight:.4f}",
                )
            except Exception as exc:
                passed &= check(False, f"target weights numeric check | {exc}")

        passed &= check(
            isinstance(target.get("weight_change_recommendations", []), list),
            "weight change recommendations present",
        )

        passed &= check(
            isinstance(target.get("primary_risks", []), list),
            "primary risks present",
        )

        passed &= check(
            isinstance(target.get("required_governance_actions", []), list),
            "required governance actions present",
        )

    print("\nRESULT")
    print("-" * 80)
    if passed:
        print("[PASS] Phase 5C AI Portfolio Manager validation complete")
    else:
        print("[FAIL] Phase 5C validation failed")


if __name__ == "__main__":
    main()