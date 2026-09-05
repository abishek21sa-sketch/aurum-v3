from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.research.ai_research_committee import AIResearchCommittee


class AIResearchDeskOrchestrator:
    """
    AURUM AI Research Desk Orchestrator V2.

    Uses the true AI Research Committee as the final reasoning layer.
    """

    def __init__(self) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.output_dir = Path("results/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.output_dir / "ai_research_desk.json"

    def run(self) -> Dict[str, Any]:
        committee = AIResearchCommittee()
        committee_result = committee.run()

        committee_analysis = committee_result.get("committee_analysis", {})
        analyst_outputs = committee_result.get("analyst_outputs", {})

        result = {
            "platform": "AURUM",
            "artifact": "ai_research_desk",
            "generated_at": self.generated_at,
            "ai_research_status": "complete",
            "analyst_outputs": analyst_outputs,
            "committee_analysis": committee_analysis,
            "executive_summary": self._build_executive_summary(committee_analysis),
            "recommended_posture": committee_analysis.get(
                "execution_permission", "review_required"
            ),
            "highest_priority_risk": committee_analysis.get(
                "binding_constraint", "unknown"
            ),
            "research_confidence": committee_analysis.get(
                "committee_confidence", 0.0
            ),
        }

        with self.output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

        return result

    @staticmethod
    def _build_executive_summary(committee_analysis: Dict[str, Any]) -> str:
        decision = committee_analysis.get("committee_decision", "Unavailable")
        permission = committee_analysis.get("execution_permission", "unknown")
        constraint = committee_analysis.get("binding_constraint", "unknown")
        confidence = committee_analysis.get("committee_confidence", 0.0)

        return (
            f"{decision} Execution permission is {permission}. "
            f"Binding constraint: {constraint}. "
            f"Committee confidence: {confidence}."
        )


if __name__ == "__main__":
    orchestrator = AIResearchDeskOrchestrator()
    result = orchestrator.run()

    print(json.dumps({
        "executive_summary": result["executive_summary"],
        "recommended_posture": result["recommended_posture"],
        "highest_priority_risk": result["highest_priority_risk"],
        "research_confidence": result["research_confidence"],
    }, indent=2, default=str))

    print()
    print("Saved: results/research/ai_research_desk.json")