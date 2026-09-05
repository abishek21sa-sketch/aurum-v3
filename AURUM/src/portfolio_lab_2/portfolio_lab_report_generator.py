from pathlib import Path
import json


RESULTS_DIR = Path("results/portfolio_lab_2")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    results = load_json(RESULTS_DIR / "portfolio_lab_results.json")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM PORTFOLIO LABORATORY 2.0 REPORT")
    lines.append("=" * 80)
    lines.append(f"Scenario Count: {results['scenario_count']}")
    lines.append(f"Critical:       {results['critical_count']}")
    lines.append(f"High:           {results['high_count']}")
    lines.append(f"Medium:         {results['medium_count']}")
    lines.append(f"Low:            {results['low_count']}")
    lines.append("")

    worst = results["worst_scenario"]
    lines.append("WORST SCENARIO")
    lines.append("-" * 80)
    lines.append(f"{worst['scenario_id']} | {worst['name']}")
    lines.append(f"Question: {worst['question']}")
    lines.append(f"Impact:   {worst['portfolio_impact']:.2%}")
    lines.append(f"Severity: {worst['severity']}")
    lines.append(f"Response: {worst['recommended_response']}")
    lines.append("")

    lines.append("SCENARIO RESULTS")
    lines.append("-" * 80)

    for scenario in results["scenario_results"]:
        lines.append(
            f"{scenario['scenario_id']:32} | "
            f"impact={scenario['portfolio_impact']:8.2%} | "
            f"severity={scenario['severity']}"
        )
        lines.append(f"Logic:    {scenario['institutional_logic']}")
        lines.append(f"Response: {scenario['recommended_response']}")
        lines.append("")

    report = "\n".join(lines)

    (RESULTS_DIR / "portfolio_lab_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()