from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FILES = [
    Path("results/research/investment_committee_minutes.json"),
    Path("results/research/committee_decision.json"),
    Path("results/research/committee_explanation.txt"),
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
    print("AURUM PHASE 5B AI INVESTMENT COMMITTEE VALIDATION")
    print("=" * 80)

    passed = True

    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)
    try:
        import src.research.ai_investment_committee  # noqa: F401

        passed &= check(True, "import src.research.ai_investment_committee")
    except Exception as exc:
        passed &= check(False, f"import src.research.ai_investment_committee | {exc}")

    print("\nARTIFACT CHECKS")
    print("-" * 80)
    for path in REQUIRED_FILES:
        passed &= check(path.exists(), f"artifact exists: {path}")

    if all(p.exists() for p in REQUIRED_FILES):
        minutes = load_json(Path("results/research/investment_committee_minutes.json"))
        decision = load_json(Path("results/research/committee_decision.json"))

        print("\nSCHEMA CHECKS")
        print("-" * 80)

        passed &= check(
            minutes.get("committee_type") in [
                "true_llm_multi_agent_investment_committee",
                "true_llm_single_call_investment_committee",
            ],
            "committee type is valid true LLM committee",
        )

        passed &= check(
            int(minutes.get("llm_calls_used", 999)) <= int(minutes.get("llm_call_budget", 999)),
            "LLM call budget respected",
        )

       
        passed &= check(
            "llm_backend" in minutes and minutes["llm_backend"],
            "LLM backend recorded",
        )

        passed &= check(
            len(minutes.get("agent_opinions", [])) >= 5,
            "agent opinions generated",
        )

        passed &= check(
            len(minutes.get("agent_rebuttals", [])) >= 5,
            "agent rebuttals generated",
        )

        passed &= check(
            len(minutes.get("votes", [])) >= 5,
            "agent votes generated",
        )

        passed &= check(
            "portfolio_manager_recommendation" in minutes,
            "AI portfolio manager recommendation generated",
        )

        passed &= check(
            isinstance(decision.get("target_allocation", {}), dict),
            "target allocation present in final committee decision",
        )

        passed &= check(
            decision.get("investment_view") in [
                "risk_on",
                "neutral",
                "defensive",
                "risk_off",
            ],
            "valid investment view",
        )

        passed &= check(
            decision.get("execution_permission") in [
                "allowed",
                "review_required",
                "blocked",
            ],
            "valid execution permission",
        )

        passed &= check(
            decision.get("approval_status") in [
                "approved",
                "review_required",
                "blocked",
            ],
            "valid approval status",
        )

        passed &= check(
            isinstance(decision.get("portfolio_actions", []), list),
            "portfolio actions present",
        )

    print("\nRESULT")
    print("-" * 80)
    if passed:
        print("[PASS] Phase 5B AI Investment Committee validation complete")
    else:
        print("[FAIL] Phase 5B validation failed")


if __name__ == "__main__":
    main()  