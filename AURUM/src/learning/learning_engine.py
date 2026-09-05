from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from src.learning.decision_evaluator import (
    DECISION_SCORECARD_CSV,
    DecisionEvaluator,
)
from src.learning.committee_scorecard import (
    COMMITTEE_PERFORMANCE_JSON,
    CommitteeScorecard,
)


LEARNING_REPORT_TXT = Path("results/learning/learning_report.txt")
LEARNING_REPORT_JSON = Path("results/learning/learning_report.json")


class LearningEngine:
    """
    Turns decision evaluations and committee scorecards into institutional learning.
    """

    def __init__(self) -> None:
        LEARNING_REPORT_TXT.parent.mkdir(parents=True, exist_ok=True)
        self.decision_evaluator = DecisionEvaluator()
        self.committee_scorecard = CommitteeScorecard()

    def _load_decision_scorecard(self) -> List[Dict[str, Any]]:
        if not DECISION_SCORECARD_CSV.exists():
            return []

        with DECISION_SCORECARD_CSV.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _load_committee_performance(self) -> Dict[str, Any]:
        if not COMMITTEE_PERFORMANCE_JSON.exists():
            return {}

        with COMMITTEE_PERFORMANCE_JSON.open("r", encoding="utf-8") as f:
            return json.load(f)

    def generate_learning_report(self) -> Dict[str, Any]:
        decisions = self._load_decision_scorecard()
        committee = self._load_committee_performance()

        if not decisions:
            self.decision_evaluator.evaluate_decision(
                decision_id="decision_5d_defensive_no_execution",
                decision_type="portfolio_posture",
                recommendation="defensive_no_execution",
                predicted_regime="defensive",
                realized_regime="defensive",
                pre_decision_risk=0.1300,
                post_decision_risk=0.1000,
                avoided_drawdown=0.0210,
                allocation_sharpe=0.8696,
                committee_agreement=0.80,
            )
            decisions = self._load_decision_scorecard()

        if not committee:
            self.committee_scorecard.score_committee(
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
            committee = self._load_committee_performance()

        decision_summary = self._summarize_decisions(decisions)
        committee_summary = self._summarize_committee(committee)

        report = {
            "report_name": "AURUM Learning Report",
            "decision_learning": decision_summary,
            "committee_learning": committee_summary,
            "system_learning": self._system_learning(decision_summary, committee_summary),
        }

        with LEARNING_REPORT_JSON.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        with LEARNING_REPORT_TXT.open("w", encoding="utf-8") as f:
            f.write(self._to_text(report))

        return report

    def _summarize_decisions(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = [float(d.get("total_decision_score", 0.0)) for d in decisions]
        correct = [
            str(d.get("prediction_correct", "")).lower() == "true"
            for d in decisions
        ]

        avg_score = sum(scores) / max(len(scores), 1)
        accuracy = sum(correct) / max(len(correct), 1)

        latest = decisions[-1] if decisions else {}

        return {
            "decision_count": len(decisions),
            "average_decision_score": round(avg_score, 4),
            "prediction_accuracy": round(accuracy, 4),
            "latest_decision": latest.get("decision_id"),
            "latest_grade": latest.get("grade"),
            "latest_recommendation": latest.get("recommendation"),
        }

    def _summarize_committee(self, committee: Dict[str, Any]) -> Dict[str, Any]:
        agents = committee.get("agents", {}) or {}

        leaders = [
            agent for agent, data in agents.items()
            if data.get("grade") == "LEADER"
        ]

        weak = [
            agent for agent, data in agents.items()
            if data.get("grade") == "WEAK"
        ]

        return {
            "committee_accuracy": committee.get("committee_accuracy"),
            "average_contribution_score": committee.get("average_contribution_score"),
            "best_agent": committee.get("best_agent"),
            "weakest_agent": committee.get("weakest_agent"),
            "leader_agents": leaders,
            "weak_agents": weak,
            "recommendation": committee.get("recommendation"),
        }

    def _system_learning(
        self,
        decision_summary: Dict[str, Any],
        committee_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        avg_score = float(decision_summary.get("average_decision_score", 0.0))
        committee_accuracy = float(committee_summary.get("committee_accuracy") or 0.0)

        lessons = []

        if avg_score >= 0.70:
            lessons.append("Recent AURUM decisions are performing well.")
        elif avg_score >= 0.50:
            lessons.append("Recent AURUM decisions are acceptable but require monitoring.")
        else:
            lessons.append("Recent AURUM decisions need improvement.")

        if committee_accuracy >= 0.70:
            lessons.append("Committee agreement is strong.")
        elif committee_accuracy >= 0.50:
            lessons.append("Committee has mixed accuracy; agent weighting should be reviewed.")
        else:
            lessons.append("Committee accuracy is weak; voting process needs recalibration.")

        best_agent = committee_summary.get("best_agent")
        weakest_agent = committee_summary.get("weakest_agent")

        if best_agent:
            lessons.append(f"{best_agent} should receive higher future voting influence.")

        if weakest_agent:
            lessons.append(f"{weakest_agent} should be monitored or down-weighted.")

        return {
            "learning_status": "ACTIVE",
            "lessons": lessons,
            "next_action": "Feed learning scores into future committee weighting and memory records.",
        }

    def _to_text(self, report: Dict[str, Any]) -> str:
        decision = report["decision_learning"]
        committee = report["committee_learning"]
        system = report["system_learning"]

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM PHASE 5F LEARNING REPORT")
        lines.append("=" * 80)

        lines.append("")
        lines.append("DECISION LEARNING")
        lines.append("-" * 80)
        lines.append(f"Decision Count:           {decision.get('decision_count')}")
        lines.append(f"Average Decision Score:   {decision.get('average_decision_score')}")
        lines.append(f"Prediction Accuracy:      {decision.get('prediction_accuracy')}")
        lines.append(f"Latest Decision:          {decision.get('latest_decision')}")
        lines.append(f"Latest Grade:             {decision.get('latest_grade')}")

        lines.append("")
        lines.append("COMMITTEE LEARNING")
        lines.append("-" * 80)
        lines.append(f"Committee Accuracy:       {committee.get('committee_accuracy')}")
        lines.append(f"Average Contribution:     {committee.get('average_contribution_score')}")
        lines.append(f"Best Agent:               {committee.get('best_agent')}")
        lines.append(f"Weakest Agent:            {committee.get('weakest_agent')}")
        lines.append(f"Leader Agents:            {committee.get('leader_agents')}")
        lines.append(f"Weak Agents:              {committee.get('weak_agents')}")

        lines.append("")
        lines.append("SYSTEM LEARNING")
        lines.append("-" * 80)

        for lesson in system.get("lessons", []):
            lines.append(f"- {lesson}")

        lines.append("")
        lines.append(f"Next Action: {system.get('next_action')}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5F LEARNING ENGINE")
    print("=" * 80)

    engine = LearningEngine()
    report = engine.generate_learning_report()

    print(f"Learning Status:         {report['system_learning']['learning_status']}")
    print(f"Decision Count:          {report['decision_learning']['decision_count']}")
    print(f"Average Decision Score:  {report['decision_learning']['average_decision_score']}")
    print(f"Committee Accuracy:      {report['committee_learning']['committee_accuracy']}")
    print(f"Best Agent:              {report['committee_learning']['best_agent']}")
    print(f"Saved TXT:               {LEARNING_REPORT_TXT}")
    print(f"Saved JSON:              {LEARNING_REPORT_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()