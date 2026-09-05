from __future__ import annotations

from typing import Any, Dict

from src.market_memory.memory_store import InstitutionalMemoryStore


class CommitteeMemoryEngine:
    """
    Stores AI investment committee votes, disagreements, final decisions,
    and approval outcomes.
    """

    def __init__(self) -> None:
        self.store = InstitutionalMemoryStore()

    def remember_committee_vote(
        self,
        regime: str,
        committee_name: str,
        agent_votes: Dict[str, str],
        final_view: str,
        approval_status: str,
        execution_permission: str,
        confidence: float,
        rationale: str,
        source: str = "committee_memory_engine",
    ) -> Dict[str, Any]:
        regime = regime.lower().strip()

        disagreement_count = len(set(agent_votes.values()))

        title = f"Committee Memory: {committee_name}"

        description = (
            f"AURUM committee '{committee_name}' voted under {regime} regime. "
            f"Final view={final_view}, approval_status={approval_status}, "
            f"execution_permission={execution_permission}, confidence={confidence}."
        )

        return self.store.remember(
            memory_type="COMMITTEE",
            title=title,
            description=description,
            regime=regime,
            committee_vote={
                "committee_name": committee_name,
                "agent_votes": agent_votes,
                "final_view": final_view,
                "approval_status": approval_status,
                "execution_permission": execution_permission,
                "confidence": confidence,
                "rationale": rationale,
                "disagreement_count": disagreement_count,
            },
            decision={
                "final_view": final_view,
                "approval_status": approval_status,
                "execution_permission": execution_permission,
                "confidence": confidence,
            },
            metadata={
                "source": source,
                "phase": "5C",
            },
        )


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C COMMITTEE MEMORY ENGINE")
    print("=" * 80)

    engine = CommitteeMemoryEngine()

    record = engine.remember_committee_vote(
        regime="defensive",
        committee_name="AI Investment Committee",
        agent_votes={
            "macro_agent": "neutral",
            "risk_agent": "defensive",
            "portfolio_agent": "defensive",
            "regime_agent": "normal",
            "digital_twin_agent": "watch",
        },
        final_view="defensive",
        approval_status="blocked",
        execution_permission="blocked",
        confidence=0.85,
        rationale=(
            "Committee recommended no live execution because governance and "
            "runtime coherence checks remain unresolved."
        ),
    )

    print(f"Saved Memory ID:       {record['memory_id']}")
    print(f"Type:                  {record['memory_type']}")
    print(f"Title:                 {record['title']}")
    print(f"Regime:                {record['regime']}")
    print(f"Final View:            {record['decision'].get('final_view')}")
    print(f"Execution Permission:  {record['decision'].get('execution_permission')}")
    print("=" * 80)


if __name__ == "__main__":
    main()