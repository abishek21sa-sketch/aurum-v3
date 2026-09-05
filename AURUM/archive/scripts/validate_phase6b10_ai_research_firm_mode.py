from pathlib import Path
import importlib
import json

from src.research_firm.ai_research_firm_mode import AIResearchFirmMode


REQUIRED_STAGES = {
    "multi_asset_universe",
    "cross_asset_intelligence",
    "factor_platform",
    "alpha_factory",
    "research_scientist",
    "autonomous_research_loop",
    "portfolio_lab_2",
    "ai_cio",
    "institutional_alpha_scorecard",
    "institutional_research_rankings",
}


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
    print("AURUM PHASE 6B.10 AI RESEARCH FIRM MODE VALIDATION")
    print("=" * 80)

    importlib.import_module("src.research_firm.ai_research_firm_mode")
    importlib.import_module("src.research_firm.research_firm_report_generator")
    check(True, "research firm modules import")

    state = AIResearchFirmMode().run()

    state_path = Path("results/research_firm/ai_research_firm_mode.json")
    daily_state_path = Path("results/research_firm/daily_research_firm_state.json")

    check(state_path.exists(), "ai_research_firm_mode.json exists")
    check(daily_state_path.exists(), "daily_research_firm_state.json exists")

    check(state["status"] == "complete", "research firm mode completed")
    check(state["stage_count"] >= 10, "at least 10 stages executed", str(state["stage_count"]))

    stage_names = {stage["stage"] for stage in state["stages"]}

    for stage in REQUIRED_STAGES:
        check(stage in stage_names, f"{stage} stage executed")

    for stage in state["stages"]:
        check(stage["status"] == "complete", f"{stage['stage']} completed")

    summary = state["executive_summary"]

    check(summary["asset_universe_size"] >= 20, "multi-asset universe included")
    check(summary["best_alpha"] is not None, "best alpha included")
    check(summary["hypotheses_generated"] >= 3, "research hypotheses included")
    check(summary["worst_portfolio_scenario"] is not None, "portfolio lab scenario included")
    check(summary["cio_recommended_action"] is not None, "CIO action included")
    check(summary["top_ranked_research_entity"] is not None, "top research entity included")
    check("AI Research Firm" in summary["interpretation"], "AI Research Firm interpretation generated")

    print("=" * 80)
    print("[PASS] PHASE 6B.10 AI RESEARCH FIRM MODE COMPLETE")
    print("AURUM now operates as an AI Research Firm.")
    print("=" * 80)


if __name__ == "__main__":
    main()