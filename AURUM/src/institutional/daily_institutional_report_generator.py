from pathlib import Path
import json


RESULTS_DIR = Path("results/institutional")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    cycle = load_json(RESULTS_DIR / "daily_institutional_cycle.json")
    summary = cycle["executive_summary"]

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM DAILY INSTITUTIONAL OPERATING REPORT")
    lines.append("=" * 80)
    lines.append(f"Status: {cycle['status']}")
    lines.append(f"Stages: {cycle['stage_count']}")
    lines.append("")

    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Firm View: {summary['firm_view']}")
    lines.append(f"Best Alpha: {summary['best_alpha']}")
    lines.append(f"Primary Risk: {summary['primary_risk']}")
    lines.append(f"CIO Action: {summary['cio_action']}")
    lines.append(f"CIO Risk Posture: {summary['cio_risk_posture']}")
    lines.append(f"Execution Permission: {summary['execution_permission']}")
    lines.append(f"Readiness Score: {summary['readiness_score']}")
    lines.append("")

    lines.append("STAGE TRACE")
    lines.append("-" * 80)

    for stage in cycle["stages"]:
        lines.append(f"{stage['stage']} | {stage['status']} | {stage['timestamp']}")

    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 80)
    lines.append(summary["interpretation"])
    lines.append("=" * 80)

    report = "\n".join(lines)

    (RESULTS_DIR / "daily_institutional_report.txt").write_text(
        report,
        encoding="utf-8",
    )

    print(report)


if __name__ == "__main__":
    main()