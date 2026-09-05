from __future__ import annotations

import importlib
from pathlib import Path
from typing import List, Tuple


COPILOT_RESPONSE_JSON = Path("results/copilot/portfolio_copilot_response.json")
COPILOT_TRANSCRIPT_JSONL = Path("results/copilot/portfolio_copilot_transcript.jsonl")
COPILOT_ACTIONS_JSON = Path("results/copilot/copilot_actions_last_response.json")


MODULES = [
    "src.research.copilot_router",
    "src.research.copilot_actions",
    "src.research.portfolio_copilot",
]


TEST_QUERIES = {
    "Show top risks.": "SHOW_TOP_RISKS",
    "Compare current portfolio to defensive portfolio.": "COMPARE_PORTFOLIOS",
    "Run a Fed shock.": "RUN_FED_SHOCK",
    "What happens if NVDA falls 20%?": "RUN_ASSET_SHOCK",
    "Why are we defensive?": "DECISION_EXPLANATION",
    "Have we seen this before?": "MEMORY_LOOKUP",
    "What is governance status?": "GOVERNANCE_STATUS",
}


def print_result(name: str, passed: bool, detail: str = "") -> None:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if detail:
        print(f"       {detail}")


def check_imports() -> List[Tuple[str, bool, str]]:
    results = []

    for module in MODULES:
        try:
            importlib.import_module(module)
            results.append((module, True, "import ok"))
        except Exception as exc:
            results.append((module, False, str(exc)))

    return results


def validate_router() -> Tuple[bool, str]:
    try:
        from src.research.copilot_router import CopilotRouter

        router = CopilotRouter()

        for query, expected_action in TEST_QUERIES.items():
            route = router.route(query)
            if route.action != expected_action:
                return (
                    False,
                    f"query '{query}' routed to {route.action}, expected {expected_action}",
                )

        return True, "all test queries routed correctly"

    except Exception as exc:
        return False, str(exc)


def validate_actions() -> Tuple[bool, str]:
    try:
        from src.research.copilot_actions import CopilotActions

        actions = CopilotActions()

        action_tests = [
            ("SHOW_TOP_RISKS", {}),
            ("COMPARE_PORTFOLIOS", {}),
            ("RUN_FED_SHOCK", {}),
            ("RUN_ASSET_SHOCK", {"asset": "NVDA", "shock": "-20%"}),
            ("GOVERNANCE_STATUS", {}),
            ("MEMORY_LOOKUP", {}),
            ("DECISION_EXPLANATION", {}),
        ]

        for action, entities in action_tests:
            response = actions.execute(action, entities)
            if not response.get("answer"):
                return False, f"missing answer for action {action}"

        return True, "all copilot actions returned answers"

    except Exception as exc:
        return False, str(exc)


def validate_copilot() -> Tuple[bool, str]:
    try:
        from src.research.portfolio_copilot import AutonomousPortfolioCopilot

        copilot = AutonomousPortfolioCopilot()

        for query, expected_action in TEST_QUERIES.items():
            response = copilot.ask(query)
            action = response.get("route", {}).get("action")
            answer = response.get("response", {}).get("answer")

            if action != expected_action:
                return False, f"{query} routed to {action}, expected {expected_action}"

            if not answer:
                return False, f"missing answer for query {query}"

        return True, "portfolio copilot answered all test queries"

    except Exception as exc:
        return False, str(exc)


def validate_artifacts() -> List[Tuple[str, bool, str]]:
    return [
        ("portfolio copilot latest response", COPILOT_RESPONSE_JSON.exists(), str(COPILOT_RESPONSE_JSON)),
        ("portfolio copilot transcript", COPILOT_TRANSCRIPT_JSONL.exists(), str(COPILOT_TRANSCRIPT_JSONL)),
        ("copilot actions last response", COPILOT_ACTIONS_JSON.exists(), str(COPILOT_ACTIONS_JSON)),
    ]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5E AUTONOMOUS PORTFOLIO COPILOT VALIDATION")
    print("=" * 80)

    overall_pass = True

    print()
    print("MODULE IMPORT CHECKS")
    print("-" * 80)

    for module, passed, detail in check_imports():
        print_result(module, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("FUNCTIONAL CHECKS")
    print("-" * 80)

    for name, validator in [
        ("copilot router", validate_router),
        ("copilot actions", validate_actions),
        ("autonomous portfolio copilot", validate_copilot),
    ]:
        passed, detail = validator()
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    for name, passed, detail in validate_artifacts():
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("=" * 80)

    if overall_pass:
        print("[PASS] PHASE 5E AUTONOMOUS PORTFOLIO COPILOT COMPLETE")
        print("AURUM now has a natural-language portfolio, risk, memory, and governance assistant.")
    else:
        print("[FAIL] PHASE 5E AUTONOMOUS PORTFOLIO COPILOT NEEDS ATTENTION")

    print("=" * 80)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()