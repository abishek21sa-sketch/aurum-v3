from pathlib import Path
import importlib
import json

from src.alpha_ranking.alpha_scorecard import InstitutionalAlphaScorecard
from src.alpha_ranking.strategy_ranker import StrategyRanker


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
    print("AURUM PHASE 6B.9 INSTITUTIONAL ALPHA RANKING VALIDATION")
    print("=" * 80)

    importlib.import_module("src.alpha_ranking.alpha_scorecard")
    importlib.import_module("src.alpha_ranking.strategy_ranker")
    importlib.import_module("src.alpha_ranking.alpha_ranking_report_generator")
    check(True, "alpha ranking modules import")

    scorecard = InstitutionalAlphaScorecard().build_scorecard()
    rankings = StrategyRanker().build_rankings()

    required_paths = [
        Path("results/alpha_ranking/institutional_alpha_scorecard.json"),
        Path("results/alpha_ranking/institutional_research_rankings.json"),
    ]

    for path in required_paths:
        check(path.exists(), f"{path} exists")

    check(scorecard["alpha_count"] >= 6, "at least 6 alphas ranked", str(scorecard["alpha_count"]))
    check(scorecard["best_alpha"] is not None, "best alpha identified")
    check(rankings["entity_count"] >= 8, "research entities ranked", str(rankings["entity_count"]))
    check(rankings["top_entity"] is not None, "top research entity identified")

    alpha_scores = [
        alpha["institutional_score"]
        for alpha in scorecard["ranked_alphas"]
    ]

    check(alpha_scores == sorted(alpha_scores, reverse=True), "alpha scorecard sorted descending")

    entity_scores = [
        entity["score"]
        for entity in rankings["ranked_entities"]
    ]

    check(entity_scores == sorted(entity_scores, reverse=True), "research rankings sorted descending")

    entity_types = rankings["entity_type_counts"]

    for entity_type in ["signal", "factor", "agent", "strategy"]:
        check(entity_type in entity_types, f"{entity_type} entities ranked")

    for alpha in scorecard["ranked_alphas"]:
        check("cio_relevance_bonus" in alpha, f"{alpha['alpha_id']} has CIO relevance bonus")
        check("research_status_bonus" in alpha, f"{alpha['alpha_id']} has research status bonus")
        check("ranking_basis" in alpha, f"{alpha['alpha_id']} has ranking basis")

    print("=" * 80)
    print("[PASS] PHASE 6B.9 INSTITUTIONAL ALPHA RANKING COMPLETE")
    print("AURUM now ranks alphas, factors, agents, and strategies institutionally.")
    print("=" * 80)


if __name__ == "__main__":
    main()