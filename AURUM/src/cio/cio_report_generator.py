from pathlib import Path
import json


RESULTS_DIR = Path("results/cio")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    thesis = load_json(RESULTS_DIR / "cio_market_thesis.json")
    directive = load_json(RESULTS_DIR / "cio_portfolio_directive.json")
    agent = load_json(RESULTS_DIR / "chief_investment_officer_agent.json")

    lines = []
    lines.append("# AURUM CIO Quarterly Letter")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        "AURUM's AI Chief Investment Officer has synthesized the current institutional "
        "research stack into a unified investment view."
    )
    lines.append("")
    lines.append(f"Market view: {thesis['market_view']}.")
    lines.append(f"Primary risk: {thesis['primary_risk']}.")
    lines.append(f"Current portfolio posture: {directive['risk_posture']}.")
    lines.append("")
    lines.append("## Market Thesis")
    lines.append("")
    lines.append(thesis["investment_thesis"])
    lines.append("")
    lines.append("## Portfolio Directive")
    lines.append("")
    lines.append(f"Recommended action: {directive['recommended_action']}.")
    lines.append(f"Execution permission: {directive['execution_permission']}.")
    lines.append(f"Confidence: {directive['confidence']:.2f}.")
    lines.append("")
    lines.append("## Research Inputs Used")
    lines.append("")
    for item in agent["inputs_used"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Closing View")
    lines.append("")
    lines.append(
        "AURUM remains governed, risk-aware, and research-driven. The current CIO view "
        "emphasizes disciplined monitoring, defensive preparedness, and continued "
        "alpha research through the autonomous research loop."
    )

    letter = "\n".join(lines)

    (RESULTS_DIR / "cio_quarterly_letter.txt").write_text(letter, encoding="utf-8")
    print(letter)


if __name__ == "__main__":
    main()