from pathlib import Path
import json


RESULTS_DIR = Path("results/autonomous_research")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    loop = load_json(RESULTS_DIR / "autonomous_research_loop.json")
    state = loop["loop_state"]
    learning = loop["learning_summary"]
    queue = loop["next_research_queue"]

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM AUTONOMOUS RESEARCH LOOP REPORT")
    lines.append("=" * 80)
    lines.append(f"Status:      {loop['status']}")
    lines.append(f"Experiments: {state['experiment_count']}")
    lines.append(f"Avg Score:   {learning['average_score']}")
    lines.append("")

    lines.append("EXPERIMENTS")
    lines.append("-" * 80)

    for exp in state["experiments"]:
        lines.append(
            f"{exp['experiment_id']} | {exp['hypothesis_id']} | "
            f"score={exp['score']} | decision={exp['decision']}"
        )
        lines.append(f"Lesson: {exp['lesson']}")
        lines.append("")

    lines.append("NEXT RESEARCH QUEUE")
    lines.append("-" * 80)

    for item in queue["queue"]:
        lines.append(
            f"{item['next_step']} | {item['hypothesis_id']} | priority={item['priority']}"
        )

    report = "\n".join(lines)

    (RESULTS_DIR / "autonomous_research_loop_report.txt").write_text(
        report,
        encoding="utf-8",
    )

    print(report)


if __name__ == "__main__":
    main()