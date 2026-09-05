from pathlib import Path
import json


RESULTS_DIR = Path("results/alpha")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    registry = load_json(RESULTS_DIR / "alpha_registry.json")
    scorecard = load_json(RESULTS_DIR / "alpha_scorecard.json")
    rankings = load_json(RESULTS_DIR / "top_alpha_rankings.json")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM ALPHA RESEARCH FACTORY REPORT")
    lines.append("=" * 80)
    lines.append(f"Alpha Count: {registry['alpha_count']}")
    lines.append("")

    lines.append("TOP ALPHA RANKINGS")
    lines.append("-" * 80)

    for idx, alpha in enumerate(rankings["top_alphas"], start=1):
        lines.append(
            f"{idx}. {alpha['alpha_id']} | {alpha['name']} | "
            f"score={alpha['alpha_score']} | sharpe={alpha['sharpe']} | "
            f"cvar={alpha['cvar']} | drawdown={alpha['max_drawdown']}"
        )

    lines.append("")
    lines.append("FULL SCORECARD")
    lines.append("-" * 80)

    for alpha in scorecard["scorecard"]:
        lines.append(
            f"{alpha['alpha_id']:24} | "
            f"{alpha['category']:12} | "
            f"score={alpha['alpha_score']:6.2f} | "
            f"consistency={alpha['consistency']:.2f}"
        )

    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append(rankings["institutional_interpretation"])

    report = "\n".join(lines)

    (RESULTS_DIR / "alpha_factory_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()