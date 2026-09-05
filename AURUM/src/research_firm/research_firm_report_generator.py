from pathlib import Path
import json


RESULTS_DIR = Path("results/research_firm")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    state = load_json(RESULTS_DIR / "ai_research_firm_mode.json")
    summary = state["executive_summary"]

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM AI RESEARCH FIRM DAILY REPORT")
    lines.append("=" * 80)
    lines.append(f"Status: {state['status']}")
    lines.append(f"Stages: {state['stage_count']}")
    lines.append("")

    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Firm View: {summary['firm_view']}")
    lines.append(f"Asset Universe Size: {summary['asset_universe_size']}")
    lines.append(f"Best Alpha: {summary['best_alpha']}")
    lines.append(f"Best Alpha Score: {summary['best_alpha_score']}")
    lines.append(f"Hypotheses Generated: {summary['hypotheses_generated']}")
    lines.append(f"Worst Portfolio Scenario: {summary['worst_portfolio_scenario']}")
    lines.append(f"Worst Portfolio Impact: {summary['worst_portfolio_impact']:.2%}")
    lines.append(f"CIO Recommended Action: {summary['cio_recommended_action']}")
    lines.append(f"CIO Risk Posture: {summary['cio_risk_posture']}")
    lines.append(f"Top Research Entity: {summary['top_ranked_research_entity']}")
    lines.append("")

    lines.append("STAGE TRACE")
    lines.append("-" * 80)

    for stage in state["stages"]:
        lines.append(f"{stage['stage']} | status={stage['status']}")
        if stage["output_summary"]:
            lines.append(f"  {stage['output_summary']}")

    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append(summary["interpretation"])
    lines.append("=" * 80)

    report = "\n".join(lines)

    (RESULTS_DIR / "daily_research_firm_report.txt").write_text(
        report,
        encoding="utf-8",
    )

    print(report)


if __name__ == "__main__":
    main()