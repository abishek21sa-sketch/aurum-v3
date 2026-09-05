from pathlib import Path
import json


RESULTS_DIR = Path("results/alpha_ranking")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    scorecard = load_json(RESULTS_DIR / "institutional_alpha_scorecard.json")
    rankings = load_json(RESULTS_DIR / "institutional_research_rankings.json")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM INSTITUTIONAL ALPHA RANKING REPORT")
    lines.append("=" * 80)
    lines.append(f"Alpha Count:  {scorecard['alpha_count']}")
    lines.append(f"Entity Count: {rankings['entity_count']}")
    lines.append("")

    lines.append("ALPHA SCORECARD")
    lines.append("-" * 80)

    for idx, alpha in enumerate(scorecard["ranked_alphas"], start=1):
        lines.append(
            f"{idx}. {alpha['alpha_id']} | {alpha['name']} | "
            f"institutional_score={alpha['institutional_score']} | "
            f"base_score={alpha['alpha_score']}"
        )

    lines.append("")
    lines.append("INSTITUTIONAL RESEARCH RANKINGS")
    lines.append("-" * 80)

    for idx, entity in enumerate(rankings["ranked_entities"], start=1):
        lines.append(
            f"{idx}. {entity['entity_type']} | {entity['entity_id']} | "
            f"score={entity['score']} | basis={entity['basis']}"
        )

    report = "\n".join(lines)

    (RESULTS_DIR / "alpha_ranking_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()