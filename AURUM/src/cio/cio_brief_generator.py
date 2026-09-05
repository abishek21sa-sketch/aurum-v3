from pathlib import Path
import json


RESULTS_DIR = Path("results/cio")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    thesis = load_json(RESULTS_DIR / "cio_market_thesis.json")
    directive = load_json(RESULTS_DIR / "cio_portfolio_directive.json")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM CIO BRIEF")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Market View: {thesis['market_view']}")
    lines.append(f"Primary Risk: {thesis['primary_risk']}")
    lines.append(f"Primary Risk Impact: {thesis['primary_risk_impact']:.2%}")
    lines.append(f"Factor Posture: {thesis['factor_posture']}")
    lines.append(f"Preferred Factors: {', '.join(thesis['preferred_factors'])}")
    lines.append(f"Top Alpha: {thesis['top_alpha']}")
    lines.append("")
    lines.append("Portfolio Directive")
    lines.append("-" * 80)
    lines.append(f"Risk Posture: {directive['risk_posture']}")
    lines.append(f"Recommended Action: {directive['recommended_action']}")
    lines.append(f"Execution Permission: {directive['execution_permission']}")
    lines.append(f"Confidence: {directive['confidence']:.2f}")
    lines.append("")
    lines.append("CIO Thesis")
    lines.append("-" * 80)
    lines.append(thesis["investment_thesis"])
    lines.append("=" * 80)

    brief = "\n".join(lines)

    (RESULTS_DIR / "cio_brief.txt").write_text(brief, encoding="utf-8")
    print(brief)


if __name__ == "__main__":
    main()