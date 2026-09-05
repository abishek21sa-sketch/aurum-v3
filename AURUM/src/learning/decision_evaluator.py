from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DECISION_SCORECARD_CSV = Path("results/learning/decision_scorecard.csv")
DECISION_EVALUATION_JSON = Path("results/learning/decision_evaluation_latest.json")


class DecisionEvaluator:
    """
    Evaluates AURUM decisions against realized or simulated outcomes.

    Metrics:
    - accuracy
    - risk reduction
    - drawdown avoidance
    - allocation quality
    - total decision score
    """

    def __init__(self) -> None:
        DECISION_SCORECARD_CSV.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))

    def evaluate_decision(
        self,
        decision_id: str,
        decision_type: str,
        recommendation: str,
        predicted_regime: str,
        realized_regime: str,
        pre_decision_risk: float,
        post_decision_risk: float,
        avoided_drawdown: float,
        allocation_sharpe: float,
        committee_agreement: float,
    ) -> Dict[str, Any]:
        prediction_correct = predicted_regime.lower() == realized_regime.lower()
        accuracy_score = 1.0 if prediction_correct else 0.0

        risk_reduction = pre_decision_risk - post_decision_risk
        risk_reduction_score = self._clamp(risk_reduction / max(pre_decision_risk, 1e-9))

        drawdown_avoidance_score = self._clamp(avoided_drawdown / 0.10)

        allocation_quality_score = self._clamp(allocation_sharpe / 1.5)

        committee_agreement_score = self._clamp(committee_agreement)

        total_score = (
            0.25 * accuracy_score
            + 0.25 * risk_reduction_score
            + 0.20 * drawdown_avoidance_score
            + 0.20 * allocation_quality_score
            + 0.10 * committee_agreement_score
        )

        result = {
            "timestamp": self._utc_now(),
            "decision_id": decision_id,
            "decision_type": decision_type,
            "recommendation": recommendation,
            "predicted_regime": predicted_regime,
            "realized_regime": realized_regime,
            "prediction_correct": prediction_correct,
            "pre_decision_risk": pre_decision_risk,
            "post_decision_risk": post_decision_risk,
            "risk_reduction": risk_reduction,
            "avoided_drawdown": avoided_drawdown,
            "allocation_sharpe": allocation_sharpe,
            "committee_agreement": committee_agreement,
            "accuracy_score": round(accuracy_score, 4),
            "risk_reduction_score": round(risk_reduction_score, 4),
            "drawdown_avoidance_score": round(drawdown_avoidance_score, 4),
            "allocation_quality_score": round(allocation_quality_score, 4),
            "committee_agreement_score": round(committee_agreement_score, 4),
            "total_decision_score": round(total_score, 4),
            "grade": self._grade(total_score),
        }

        self._append_scorecard(result)

        with DECISION_EVALUATION_JSON.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.85:
            return "EXCELLENT"
        if score >= 0.70:
            return "GOOD"
        if score >= 0.50:
            return "WATCH"
        return "POOR"

    def _append_scorecard(self, result: Dict[str, Any]) -> None:
        file_exists = DECISION_SCORECARD_CSV.exists()

        with DECISION_SCORECARD_CSV.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(result.keys()))

            if not file_exists:
                writer.writeheader()

            writer.writerow(result)

    def load_scorecard(self) -> List[Dict[str, Any]]:
        if not DECISION_SCORECARD_CSV.exists():
            return []

        with DECISION_SCORECARD_CSV.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5F DECISION EVALUATOR")
    print("=" * 80)

    evaluator = DecisionEvaluator()

    result = evaluator.evaluate_decision(
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

    print(f"Decision ID:        {result['decision_id']}")
    print(f"Recommendation:     {result['recommendation']}")
    print(f"Prediction Correct: {result['prediction_correct']}")
    print(f"Total Score:        {result['total_decision_score']}")
    print(f"Grade:              {result['grade']}")
    print(f"Saved CSV:          {DECISION_SCORECARD_CSV}")
    print(f"Saved JSON:         {DECISION_EVALUATION_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()