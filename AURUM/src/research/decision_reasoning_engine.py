from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.research.decision_trace_engine import DecisionTraceEngine, TRACE_JSON
from src.market_memory.memory_similarity_engine import MarketMemorySimilarityEngine


REASONING_JSON = Path("results/decision_intelligence/decision_reasoning.json")


class DecisionReasoningEngine:
    """
    Converts raw decision trace into structured institutional reasoning.

    This answers:
    - Why did allocation change?
    - Why is risk increasing?
    - Why are we defensive?
    - What evidence supports the decision?
    - What historical memories support the decision?
    """

    def __init__(self) -> None:
        self.trace_engine = DecisionTraceEngine()
        self.memory_engine = MarketMemorySimilarityEngine()
        REASONING_JSON.parent.mkdir(parents=True, exist_ok=True)

    def _load_or_build_trace(self) -> Dict[str, Any]:
        if TRACE_JSON.exists():
            with TRACE_JSON.open("r", encoding="utf-8") as f:
                return json.load(f)

        return self.trace_engine.build_trace()

    @staticmethod
    def _get_stage(trace: Dict[str, Any], stage_name: str) -> Dict[str, Any]:
        for stage in trace.get("decision_lineage", []):
            if stage.get("stage") == stage_name:
                return stage
        return {}

    def generate_reasoning(self) -> Dict[str, Any]:
        trace = self._load_or_build_trace()

        features = self._get_stage(trace, "features").get("inputs", {})
        regime = self._get_stage(trace, "regime").get("inputs", {})
        risk = self._get_stage(trace, "risk").get("inputs", {})
        optimization = self._get_stage(trace, "optimization").get("inputs", {})
        committee = self._get_stage(trace, "committee").get("inputs", {})
        final_decision = self._get_stage(trace, "final_decision").get("inputs", {})

        current_state = {
            "volatility": features.get("volatility", 0.0),
            "stress_score": features.get("stress_score", 0.0),
            "breadth": features.get("breadth", 0.0),
            "projected_var95": risk.get("projected_var95", 0.0),
            "projected_drawdown": risk.get("projected_drawdown", 0.0),
        }

        memory_report = self.memory_engine.current_market_resemblance_report(
            current_state=current_state,
            limit=5,
        )

        reasoning = {
            "trace_id": trace.get("trace_id"),
            "timestamp": trace.get("timestamp"),
            "decision_question": trace.get("decision_question"),
            "final_decision": final_decision,
            "reasoning_summary": self._build_summary(
                features=features,
                regime=regime,
                risk=risk,
                optimization=optimization,
                committee=committee,
                memory_report=memory_report,
            ),
            "answers": {
                "why_are_we_defensive": self._why_defensive(
                    features, regime, risk, optimization, committee, memory_report
                ),
                "why_did_allocation_change": self._why_allocation_changed(
                    optimization, risk
                ),
                "why_is_risk_increasing": self._why_risk_increasing(
                    features, risk
                ),
                "why_execution_blocked": self._why_execution_blocked(
                    committee
                ),
                "have_we_seen_this_before": self._seen_before(
                    memory_report
                ),
            },
            "evidence": {
                "features": features,
                "regime": regime,
                "risk": risk,
                "optimization": optimization,
                "committee": committee,
                "memory": memory_report,
            },
        }

        with REASONING_JSON.open("w", encoding="utf-8") as f:
            json.dump(reasoning, f, indent=2, default=str)

        return reasoning

    def _build_summary(
        self,
        features: Dict[str, Any],
        regime: Dict[str, Any],
        risk: Dict[str, Any],
        optimization: Dict[str, Any],
        committee: Dict[str, Any],
        memory_report: Dict[str, Any],
    ) -> str:
        best = memory_report.get("best_match") or {}

        return (
            f"AURUM is defensive because breadth is {features.get('breadth')}, "
            f"stress_score is {features.get('stress_score')}, projected drawdown is "
            f"{risk.get('projected_drawdown')}, and the optimizer recommends "
            f"{optimization.get('action')}. The committee view is "
            f"{committee.get('investment_view')} with execution permission "
            f"{committee.get('execution_permission')}. Market memory found closest "
            f"match '{best.get('title')}' with similarity "
            f"{best.get('similarity_percent')}%."
        )

    def _why_defensive(
        self,
        features: Dict[str, Any],
        regime: Dict[str, Any],
        risk: Dict[str, Any],
        optimization: Dict[str, Any],
        committee: Dict[str, Any],
        memory_report: Dict[str, Any],
    ) -> List[str]:
        best = memory_report.get("best_match") or {}

        return [
            f"Market breadth is weak at {features.get('breadth')}, indicating limited participation.",
            f"Stress score is {features.get('stress_score')}, so the system is not in panic but risk is elevated.",
            f"Projected drawdown is {risk.get('projected_drawdown')}, which justifies reducing equity exposure.",
            f"The optimizer action is {optimization.get('action')}, shifting exposure toward defensive assets.",
            f"The AI committee final view is {committee.get('investment_view')}.",
            f"Market memory found a similar prior state: {best.get('title')} at {best.get('similarity_percent')}% similarity.",
        ]

    def _why_allocation_changed(
        self,
        optimization: Dict[str, Any],
        risk: Dict[str, Any],
    ) -> List[str]:
        changes = optimization.get("recommended_changes", {}) or {}

        reasons = [
            f"Projected VaR95 is {risk.get('projected_var95')}.",
            f"Projected CVaR95 is {risk.get('projected_cvar95')}.",
            f"Projected drawdown is {risk.get('projected_drawdown')}.",
            "The optimizer reduced equity exposure and increased hedge/cash exposure.",
        ]

        for asset, change in changes.items():
            direction = "increased" if change > 0 else "reduced"
            reasons.append(f"{asset} was {direction} by {abs(change)}.")

        return reasons

    def _why_risk_increasing(
        self,
        features: Dict[str, Any],
        risk: Dict[str, Any],
    ) -> List[str]:
        return [
            f"Volatility is {features.get('volatility')}.",
            f"Market breadth is only {features.get('breadth')}.",
            f"Stress score is {features.get('stress_score')}.",
            f"Projected VaR95 is {risk.get('projected_var95')}.",
            f"Projected drawdown is {risk.get('projected_drawdown')}.",
        ]

    def _why_execution_blocked(
        self,
        committee: Dict[str, Any],
    ) -> List[str]:
        return [
            f"Committee approval status is {committee.get('approval_status')}.",
            f"Execution permission is {committee.get('execution_permission')}.",
            "AURUM can recommend the defensive action, but live execution remains blocked until governance readiness clears.",
        ]

    def _seen_before(
        self,
        memory_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        best = memory_report.get("best_match")

        if not best:
            return {
                "seen_before": False,
                "message": "No comparable memory found.",
            }

        return {
            "seen_before": True,
            "closest_memory": best.get("title"),
            "regime": best.get("regime"),
            "similarity_percent": best.get("similarity_percent"),
            "message": (
                f"Yes. Current market resembles {best.get('title')} "
                f"with {best.get('similarity_percent')}% similarity."
            ),
        }


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5D DECISION REASONING ENGINE")
    print("=" * 80)

    engine = DecisionReasoningEngine()
    reasoning = engine.generate_reasoning()

    print(f"Trace ID:        {reasoning.get('trace_id')}")
    print(f"Question:        {reasoning.get('decision_question')}")
    print(f"Final Decision:  {reasoning.get('final_decision', {}).get('decision')}")
    print("-" * 80)
    print("Reasoning Summary:")
    print(reasoning.get("reasoning_summary"))
    print("-" * 80)
    print("Have We Seen This Before?")
    print(reasoning["answers"]["have_we_seen_this_before"]["message"])
    print(f"Saved:           {REASONING_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()