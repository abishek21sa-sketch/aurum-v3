from __future__ import annotations

from typing import Any, Dict

from src.market_memory.memory_store import InstitutionalMemoryStore


class OutcomeMemoryEngine:
    """
    Stores prediction outcomes and decision accuracy feedback.
    """

    def __init__(self) -> None:
        self.store = InstitutionalMemoryStore()

    def remember_outcome(
        self,
        regime: str,
        prediction_name: str,
        predicted_value: str,
        actual_value: str,
        decision_taken: str,
        realized_return: float,
        realized_drawdown: float,
        prediction_confidence: float,
        source: str = "outcome_memory_engine",
    ) -> Dict[str, Any]:
        regime = regime.lower().strip()

        correct = str(predicted_value).lower().strip() == str(actual_value).lower().strip()
        prediction_error = 0.0 if correct else 1.0

        title = f"Outcome Memory: {prediction_name}"

        description = (
            f"AURUM outcome record for '{prediction_name}'. "
            f"Predicted={predicted_value}, actual={actual_value}, "
            f"correct={correct}, realized_return={realized_return}, "
            f"realized_drawdown={realized_drawdown}."
        )

        return self.store.remember(
            memory_type="OUTCOME",
            title=title,
            description=description,
            regime=regime,
            decision={
                "decision_taken": decision_taken,
                "prediction_confidence": prediction_confidence,
            },
            outcome={
                "prediction_name": prediction_name,
                "predicted_value": predicted_value,
                "actual_value": actual_value,
                "correct": correct,
                "prediction_error": prediction_error,
                "realized_return": realized_return,
                "realized_drawdown": realized_drawdown,
            },
            metadata={
                "source": source,
                "phase": "5C",
            },
        )


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C OUTCOME MEMORY ENGINE")
    print("=" * 80)

    engine = OutcomeMemoryEngine()

    record = engine.remember_outcome(
        regime="defensive",
        prediction_name="Regime Forecast Validation",
        predicted_value="defensive",
        actual_value="defensive",
        decision_taken="reduce_equity",
        realized_return=0.0125,
        realized_drawdown=-0.0210,
        prediction_confidence=0.85,
    )

    print(f"Saved Memory ID:   {record['memory_id']}")
    print(f"Type:              {record['memory_type']}")
    print(f"Title:             {record['title']}")
    print(f"Regime:            {record['regime']}")
    print(f"Correct:           {record['outcome'].get('correct')}")
    print(f"Prediction Error:  {record['outcome'].get('prediction_error')}")
    print("=" * 80)


if __name__ == "__main__":
    main()