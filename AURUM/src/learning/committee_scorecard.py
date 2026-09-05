from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


COMMITTEE_PERFORMANCE_JSON = Path("results/learning/committee_performance.json")


class CommitteeScorecard:
    """
    Scores AI committee members based on historical recommendation quality.

    Tracks:
    - vote accuracy
    - agreement with final outcome
    - risk discipline
    - contribution score
    """

    def __init__(self) -> None:
        COMMITTEE_PERFORMANCE_JSON.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.85:
            return "LEADER"
        if score >= 0.70:
            return "STRONG"
        if score >= 0.55:
            return "WATCH"
        return "WEAK"

    def score_committee(
        self,
        realized_outcome: str,
        agent_votes: Dict[str, str],
        agent_confidences: Dict[str, float],
        risk_alignment: Dict[str, float],
    ) -> Dict[str, Any]:
        realized = realized_outcome.lower().strip()

        agents: Dict[str, Any] = {}

        for agent, vote in agent_votes.items():
            vote_clean = vote.lower().strip()
            confidence = float(agent_confidences.get(agent, 0.50))
            risk_score = float(risk_alignment.get(agent, 0.50))

            correct = vote_clean == realized

            accuracy_score = 1.0 if correct else 0.0
            confidence_quality = confidence if correct else 1.0 - confidence

            contribution_score = (
                0.50 * accuracy_score
                + 0.25 * confidence_quality
                + 0.25 * risk_score
            )

            agents[agent] = {
                "vote": vote,
                "realized_outcome": realized_outcome,
                "correct": correct,
                "confidence": round(confidence, 4),
                "risk_alignment": round(risk_score, 4),
                "accuracy_score": round(accuracy_score, 4),
                "confidence_quality": round(confidence_quality, 4),
                "contribution_score": round(contribution_score, 4),
                "grade": self._grade(contribution_score),
            }

        committee_accuracy = (
            sum(1 for a in agents.values() if a["correct"]) / max(len(agents), 1)
        )

        average_contribution = (
            sum(a["contribution_score"] for a in agents.values()) / max(len(agents), 1)
        )

        best_agent = max(agents.items(), key=lambda x: x[1]["contribution_score"])[0]
        weakest_agent = min(agents.items(), key=lambda x: x[1]["contribution_score"])[0]

        scorecard = {
            "realized_outcome": realized_outcome,
            "committee_accuracy": round(committee_accuracy, 4),
            "average_contribution_score": round(average_contribution, 4),
            "best_agent": best_agent,
            "weakest_agent": weakest_agent,
            "agents": agents,
            "recommendation": self._recommendation(agents),
        }

        with COMMITTEE_PERFORMANCE_JSON.open("w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2)

        return scorecard

    def _recommendation(self, agents: Dict[str, Any]) -> str:
        strong = [
            agent for agent, data in agents.items()
            if data["grade"] in {"LEADER", "STRONG"}
        ]

        weak = [
            agent for agent, data in agents.items()
            if data["grade"] == "WEAK"
        ]

        if strong and weak:
            return (
                f"Increase influence of {', '.join(strong)} and monitor "
                f"{', '.join(weak)} in future committee votes."
            )

        if strong:
            return f"Maintain or increase influence of {', '.join(strong)}."

        return "No agent has strong enough performance yet. Keep equal weighting."

    def load_scorecard(self) -> Dict[str, Any]:
        if not COMMITTEE_PERFORMANCE_JSON.exists():
            return {}

        with COMMITTEE_PERFORMANCE_JSON.open("r", encoding="utf-8") as f:
            return json.load(f)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5F COMMITTEE SCORECARD")
    print("=" * 80)

    scorecard_engine = CommitteeScorecard()

    scorecard = scorecard_engine.score_committee(
        realized_outcome="defensive",
        agent_votes={
            "macro_agent": "neutral",
            "risk_agent": "defensive",
            "portfolio_agent": "defensive",
            "regime_agent": "normal",
            "digital_twin_agent": "defensive",
        },
        agent_confidences={
            "macro_agent": 0.70,
            "risk_agent": 0.88,
            "portfolio_agent": 0.82,
            "regime_agent": 0.76,
            "digital_twin_agent": 0.80,
        },
        risk_alignment={
            "macro_agent": 0.55,
            "risk_agent": 0.92,
            "portfolio_agent": 0.84,
            "regime_agent": 0.65,
            "digital_twin_agent": 0.86,
        },
    )

    print(f"Committee Accuracy:        {scorecard['committee_accuracy']}")
    print(f"Average Contribution:      {scorecard['average_contribution_score']}")
    print(f"Best Agent:                {scorecard['best_agent']}")
    print(f"Weakest Agent:             {scorecard['weakest_agent']}")
    print(f"Recommendation:            {scorecard['recommendation']}")
    print(f"Saved:                     {COMMITTEE_PERFORMANCE_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()