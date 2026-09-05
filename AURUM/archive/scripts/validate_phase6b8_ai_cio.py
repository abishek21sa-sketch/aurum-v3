from pathlib import Path
import importlib
import json

from src.cio.chief_investment_officer_agent import ChiefInvestmentOfficerAgent


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6B.8 AI CHIEF INVESTMENT OFFICER VALIDATION")
    print("=" * 80)

    importlib.import_module("src.cio.chief_investment_officer_agent")
    importlib.import_module("src.cio.cio_brief_generator")
    importlib.import_module("src.cio.cio_report_generator")
    check(True, "CIO modules import")

    result = ChiefInvestmentOfficerAgent().run()

    required_paths = [
        Path("results/cio/cio_market_thesis.json"),
        Path("results/cio/cio_portfolio_directive.json"),
        Path("results/cio/chief_investment_officer_agent.json"),
    ]

    for path in required_paths:
        check(path.exists(), f"{path} exists")

    thesis = json.loads(
        Path("results/cio/cio_market_thesis.json").read_text(encoding="utf-8")
    )

    directive = json.loads(
        Path("results/cio/cio_portfolio_directive.json").read_text(encoding="utf-8")
    )

    check(thesis.get("market_view"), "market thesis generated")
    check(thesis.get("investment_thesis"), "investment thesis explanation generated")
    check(thesis.get("top_alpha"), "top alpha included in thesis")
    check(thesis.get("preferred_factors") is not None, "preferred factors included")

    check(directive.get("risk_posture"), "portfolio directive risk posture generated")
    check(directive.get("recommended_action"), "portfolio directive action generated")
    check(directive.get("execution_permission") is not None, "execution permission included")
    check(0 <= directive.get("confidence", 0) <= 1, "directive confidence valid")

    expected_inputs = {
        "portfolio_os",
        "portfolio_directive",
        "alpha_rankings",
        "factor_rotation",
        "cross_asset",
        "portfolio_lab",
        "research_scientist",
        "autonomous_research",
        "reliability",
    }

    used = set(result.get("inputs_used", []))

    for item in expected_inputs:
        check(item in used, f"CIO consumed {item}")

    print("=" * 80)
    print("[PASS] PHASE 6B.8 AI CHIEF INVESTMENT OFFICER COMPLETE")
    print("AURUM now has a CIO layer that synthesizes research into investment direction.")
    print("=" * 80)


if __name__ == "__main__":
    main()