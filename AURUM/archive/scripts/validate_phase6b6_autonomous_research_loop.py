from pathlib import Path
import importlib
import json

from src.autonomous_research.autonomous_research_loop import AutonomousResearchLoop


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
    print("AURUM PHASE 6B.6 AUTONOMOUS RESEARCH LOOP VALIDATION")
    print("=" * 80)

    importlib.import_module("src.autonomous_research.research_loop_state")
    importlib.import_module("src.autonomous_research.autonomous_research_loop")
    importlib.import_module("src.autonomous_research.research_loop_report_generator")
    check(True, "autonomous research modules import")

    result = AutonomousResearchLoop().run()

    required_paths = [
        Path("results/autonomous_research/autonomous_research_loop.json"),
        Path("results/autonomous_research/research_loop_state.json"),
        Path("results/autonomous_research/research_learning_summary.json"),
        Path("results/autonomous_research/next_research_queue.json"),
    ]

    for path in required_paths:
        check(path.exists(), f"{path} exists")

    loop = json.loads(
        Path("results/autonomous_research/autonomous_research_loop.json").read_text(
            encoding="utf-8"
        )
    )

    state = loop["loop_state"]
    learning = loop["learning_summary"]
    queue = loop["next_research_queue"]

    check(loop["status"] == "complete", "loop completed")
    check(state["experiment_count"] >= 3, "at least 3 experiments evaluated", str(state["experiment_count"]))
    check(learning["experiment_count"] == state["experiment_count"], "learning summary matches experiment count")
    check(queue["queue_count"] == state["experiment_count"], "next queue generated for each experiment")

    valid_decisions = {
        "promote_to_alpha_factory",
        "continue_research",
        "revise_or_archive",
    }

    for exp in state["experiments"]:
        check(exp["status"] == "evaluated", f"{exp['experiment_id']} evaluated")
        check(exp["decision"] in valid_decisions, f"{exp['experiment_id']} valid decision")
        check(exp["score"] >= 0, f"{exp['experiment_id']} has score")
        check(exp["lesson"], f"{exp['experiment_id']} has lesson")

    check(learning["average_score"] > 0, "average score calculated", str(learning["average_score"]))

    print("=" * 80)
    print("[PASS] PHASE 6B.6 AUTONOMOUS RESEARCH LOOP COMPLETE")
    print("AURUM now converts hypotheses into experiments, learning, and next research actions.")
    print("=" * 80)


if __name__ == "__main__":
    main()