from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.research.decision_reasoning_engine import (
    DecisionReasoningEngine,
    REASONING_JSON,
)


EXPLANATION_TXT = Path("results/decision_intelligence/decision_explanation.txt")
EXPLANATION_JSON = Path("results/decision_intelligence/decision_explanation.json")


class DecisionExplanationGenerator:
    """
    Converts structured reasoning into a human-readable institutional explanation.
    """

    def __init__(self) -> None:
        self.reasoning_engine = DecisionReasoningEngine()
        EXPLANATION_TXT.parent.mkdir(parents=True, exist_ok=True)

    def _load_or_generate_reasoning(self) -> Dict[str, Any]:
        if REASONING_JSON.exists():
            with REASONING_JSON.open("r", encoding="utf-8") as f:
                return json.load(f)

        return self.reasoning_engine.generate_reasoning()

    def generate_explanation(self) -> Dict[str, Any]:
        reasoning = self._load_or_generate_reasoning()

        explanation = {
            "explanation_name": "AURUM Decision Explanation",
            "trace_id": reasoning.get("trace_id"),
            "decision_question": reasoning.get("decision_question"),
            "final_decision": reasoning.get("final_decision"),
            "executive_answer": self._executive_answer(reasoning),
            "detailed_answers": reasoning.get("answers", {}),
            "evidence": reasoning.get("evidence", {}),
            "plain_english_explanation": self._to_text(reasoning),
        }

        with EXPLANATION_JSON.open("w", encoding="utf-8") as f:
            json.dump(explanation, f, indent=2, default=str)

        with EXPLANATION_TXT.open("w", encoding="utf-8") as f:
            f.write(explanation["plain_english_explanation"])

        return explanation

    def _executive_answer(self, reasoning: Dict[str, Any]) -> str:
        final_decision = reasoning.get("final_decision", {})
        seen_before = reasoning.get("answers", {}).get("have_we_seen_this_before", {})

        return (
            f"AURUM's final decision is {final_decision.get('decision')}. "
            f"The system is defensive because market breadth is weak, risk projections "
            f"show meaningful downside, the optimizer recommends reducing equity, "
            f"and institutional memory confirms a similar prior defensive state. "
            f"Execution is blocked because governance approval is not cleared. "
            f"{seen_before.get('message')}"
        )

    def _section(self, title: str, items: List[str]) -> List[str]:
        lines = []
        lines.append("")
        lines.append(title)
        lines.append("-" * 80)

        if not items:
            lines.append("No explanation available.")
            return lines

        for item in items:
            lines.append(f"- {item}")

        return lines

    def _to_text(self, reasoning: Dict[str, Any]) -> str:
        answers = reasoning.get("answers", {})
        final_decision = reasoning.get("final_decision", {})

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM DECISION EXPLANATION")
        lines.append("=" * 80)

        lines.append("")
        lines.append(f"Trace ID:          {reasoning.get('trace_id')}")
        lines.append(f"Decision Question: {reasoning.get('decision_question')}")
        lines.append(f"Final Decision:    {final_decision.get('decision')}")
        lines.append(f"Portfolio Action:  {final_decision.get('portfolio_action')}")
        lines.append(f"Decision Reason:   {final_decision.get('reason')}")

        lines.append("")
        lines.append("EXECUTIVE ANSWER")
        lines.append("-" * 80)
        lines.append(self._executive_answer(reasoning))

        lines.extend(
            self._section(
                "WHY ARE WE DEFENSIVE?",
                answers.get("why_are_we_defensive", []),
            )
        )

        lines.extend(
            self._section(
                "WHY DID ALLOCATION CHANGE?",
                answers.get("why_did_allocation_change", []),
            )
        )

        lines.extend(
            self._section(
                "WHY IS RISK INCREASING?",
                answers.get("why_is_risk_increasing", []),
            )
        )

        lines.extend(
            self._section(
                "WHY IS EXECUTION BLOCKED?",
                answers.get("why_execution_blocked", []),
            )
        )

        seen = answers.get("have_we_seen_this_before", {})
        lines.append("")
        lines.append("HAVE WE SEEN THIS BEFORE?")
        lines.append("-" * 80)
        lines.append(seen.get("message", "No comparable memory found."))

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5D EXPLANATION GENERATOR")
    print("=" * 80)

    generator = DecisionExplanationGenerator()
    explanation = generator.generate_explanation()

    print(f"Trace ID:        {explanation.get('trace_id')}")
    print(f"Final Decision:  {explanation.get('final_decision', {}).get('decision')}")
    print(f"TXT Saved:       {EXPLANATION_TXT}")
    print(f"JSON Saved:      {EXPLANATION_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()