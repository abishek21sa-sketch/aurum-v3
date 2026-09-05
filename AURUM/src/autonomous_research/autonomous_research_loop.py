from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json

from src.autonomous_research.research_loop_state import (
    ResearchExperiment,
    ResearchLoopState,
)


RESULTS_DIR = Path("results/autonomous_research")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

HYPOTHESES_PATH = Path("results/research_scientist/research_hypotheses.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutonomousResearchLoop:
    def load_hypotheses(self) -> List[Dict]:
        if not HYPOTHESES_PATH.exists():
            return []

        payload = json.loads(HYPOTHESES_PATH.read_text(encoding="utf-8"))
        return payload.get("hypotheses", [])

    def build_research_design(self, hypothesis: Dict) -> str:
        return (
            f"Design experiment for {hypothesis['hypothesis_id']}: "
            f"{hypothesis['test_design']}"
        )

    def simulate_backtest_evaluation(self, hypothesis: Dict) -> Dict:
        priority = hypothesis.get("priority", "medium")
        theme = hypothesis.get("theme", "")

        score = 65.0

        if priority == "high":
            score += 8.0
        elif priority == "medium":
            score += 4.0

        if "momentum" in theme:
            score += 5.0
        if "volatility" in theme:
            score += 4.0
        if "rates" in theme:
            score += 3.0
        if "repair" in theme:
            score -= 2.0

        score = round(min(score, 95.0), 2)

        if score >= 78:
            decision = "promote_to_alpha_factory"
        elif score >= 70:
            decision = "continue_research"
        else:
            decision = "revise_or_archive"

        return {
            "score": score,
            "decision": decision,
        }

    def generate_lesson(self, hypothesis: Dict, evaluation: Dict) -> str:
        decision = evaluation["decision"]

        if decision == "promote_to_alpha_factory":
            return (
                f"{hypothesis['hypothesis_id']} shows enough promise to become a new alpha candidate."
            )

        if decision == "continue_research":
            return (
                f"{hypothesis['hypothesis_id']} is promising but requires additional filters or validation."
            )

        return (
            f"{hypothesis['hypothesis_id']} is weak and should be revised, combined, or archived."
        )

    def run(self) -> Dict:
        hypotheses = self.load_hypotheses()

        state = ResearchLoopState()
        state.stage = "running"

        for index, hypothesis in enumerate(hypotheses, start=1):
            evaluation = self.simulate_backtest_evaluation(hypothesis)
            lesson = self.generate_lesson(hypothesis, evaluation)

            experiment = ResearchExperiment(
                experiment_id=f"EXP_{index:03d}",
                hypothesis_id=hypothesis["hypothesis_id"],
                theme=hypothesis["theme"],
                research_design=self.build_research_design(hypothesis),
                status="evaluated",
                score=evaluation["score"],
                decision=evaluation["decision"],
                lesson=lesson,
            )

            state.add_experiment(experiment)

        state.stage = "complete"

        loop_state = state.to_dict()
        learning = self.learning_summary(loop_state)
        next_steps = self.next_hypotheses(loop_state)

        result = {
            "timestamp": utc_now(),
            "loop": "aurum_autonomous_research_loop",
            "status": "complete",
            "loop_state": loop_state,
            "learning_summary": learning,
            "next_research_queue": next_steps,
        }

        (RESULTS_DIR / "autonomous_research_loop.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "research_loop_state.json").write_text(
            json.dumps(loop_state, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "research_learning_summary.json").write_text(
            json.dumps(learning, indent=2),
            encoding="utf-8",
        )

        (RESULTS_DIR / "next_research_queue.json").write_text(
            json.dumps(next_steps, indent=2),
            encoding="utf-8",
        )

        return result

    def learning_summary(self, loop_state: Dict) -> Dict:
        experiments = loop_state["experiments"]

        promoted = [
            exp for exp in experiments
            if exp["decision"] == "promote_to_alpha_factory"
        ]

        continued = [
            exp for exp in experiments
            if exp["decision"] == "continue_research"
        ]

        archived = [
            exp for exp in experiments
            if exp["decision"] == "revise_or_archive"
        ]

        return {
            "timestamp": utc_now(),
            "experiment_count": len(experiments),
            "promoted_count": len(promoted),
            "continue_count": len(continued),
            "archive_count": len(archived),
            "average_score": round(
                sum(exp["score"] for exp in experiments) / len(experiments),
                2,
            ) if experiments else 0,
            "lessons": [exp["lesson"] for exp in experiments],
        }

    def next_hypotheses(self, loop_state: Dict) -> Dict:
        experiments = loop_state["experiments"]

        queue = []

        for exp in experiments:
            if exp["decision"] == "promote_to_alpha_factory":
                queue.append(
                    {
                        "next_step": "register_alpha_candidate",
                        "source_experiment": exp["experiment_id"],
                        "hypothesis_id": exp["hypothesis_id"],
                        "priority": "high",
                    }
                )
            elif exp["decision"] == "continue_research":
                queue.append(
                    {
                        "next_step": "add_filters_and_retest",
                        "source_experiment": exp["experiment_id"],
                        "hypothesis_id": exp["hypothesis_id"],
                        "priority": "medium",
                    }
                )
            else:
                queue.append(
                    {
                        "next_step": "revise_or_archive",
                        "source_experiment": exp["experiment_id"],
                        "hypothesis_id": exp["hypothesis_id"],
                        "priority": "low",
                    }
                )

        return {
            "timestamp": utc_now(),
            "queue_count": len(queue),
            "queue": queue,
        }


def main() -> None:
    result = AutonomousResearchLoop().run()
    learning = result["learning_summary"]

    print("=" * 80)
    print("AURUM PHASE 6B.6 AUTONOMOUS RESEARCH LOOP")
    print("=" * 80)
    print(f"Status:          {result['status']}")
    print(f"Experiments:     {learning['experiment_count']}")
    print(f"Promoted:        {learning['promoted_count']}")
    print(f"Continue:        {learning['continue_count']}")
    print(f"Archive:         {learning['archive_count']}")
    print(f"Average Score:   {learning['average_score']}")
    print("=" * 80)


if __name__ == "__main__":
    main()