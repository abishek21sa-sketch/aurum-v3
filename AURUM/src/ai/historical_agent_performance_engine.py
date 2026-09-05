from pathlib import Path
import json
from datetime import datetime, UTC


PERFORMANCE_PATH = Path(
    "results/ai/agent_performance_history.json"
)


DEFAULT_AGENT_STATS = {
    "decision": {
        "total_evaluations": 0,
        "successful_evaluations": 0,
        "historical_score": 0.50,
    },

    "scenario": {
        "total_evaluations": 0,
        "successful_evaluations": 0,
        "historical_score": 0.50,
    },

    "risk": {
        "total_evaluations": 0,
        "successful_evaluations": 0,
        "historical_score": 0.50,
    },

    "committee": {
        "total_evaluations": 0,
        "successful_evaluations": 0,
        "historical_score": 0.50,
    },

    "confidence": {
        "total_evaluations": 0,
        "successful_evaluations": 0,
        "historical_score": 0.50,
    },
}


def load_agent_history():
    if not PERFORMANCE_PATH.exists():
        return DEFAULT_AGENT_STATS.copy()

    with PERFORMANCE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_agent_history(history: dict):
    PERFORMANCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with PERFORMANCE_PATH.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def update_agent_performance(
    agent: str,
    successful: bool,
):
    history = load_agent_history()

    if agent not in history:
        history[agent] = {
            "total_evaluations": 0,
            "successful_evaluations": 0,
            "historical_score": 0.50,
        }

    history[agent]["total_evaluations"] += 1

    if successful:
        history[agent]["successful_evaluations"] += 1

    total = history[agent]["total_evaluations"]
    success = history[agent]["successful_evaluations"]

    history[agent]["historical_score"] = round(
        success / total,
        4,
    )

    history["last_updated"] = datetime.now(
        UTC
    ).isoformat()

    save_agent_history(history)

    return history


def build_agent_performance_report():
    history = load_agent_history()

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM HISTORICAL AGENT PERFORMANCE ENGINE")
    lines.append("=" * 90)

    lines.append("")
    lines.append("AGENT PERFORMANCE SUMMARY")
    lines.append("-" * 70)

    sortable = []

    for agent, stats in history.items():
        if not isinstance(stats, dict):
            continue

        sortable.append(
            (
                agent,
                stats.get("historical_score", 0),
                stats.get("total_evaluations", 0),
            )
        )

    sortable.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    for agent, score, total in sortable:
        lines.append(
            f"{agent.upper():15s} "
            f"| score={score:.2f} "
            f"| evaluations={total}"
        )

    lines.append("")
    lines.append("TOP HISTORICAL AGENT")
    lines.append("-" * 70)

    if sortable:
        best_agent = sortable[0]

        lines.append(
            f"{best_agent[0].upper()} currently has "
            f"the strongest historical reliability score."
        )

    return "\n".join(lines)


if __name__ == "__main__":
    update_agent_performance(
        "risk",
        successful=True,
    )

    update_agent_performance(
        "scenario",
        successful=True,
    )

    update_agent_performance(
        "decision",
        successful=False,
    )

    update_agent_performance(
        "confidence",
        successful=True,
    )

    update_agent_performance(
        "committee",
        successful=False,
    )

    print(build_agent_performance_report())