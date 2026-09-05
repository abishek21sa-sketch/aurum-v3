from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


RESULTS_DIR = Path("results/research")
OUTPUT_PATH = RESULTS_DIR / "committee_context.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_get(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def compact_text(value: Any, max_len: int = 700) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:max_len]


class CommitteeContextBuilder:
    """
    Builds a compressed, low-token committee context.

    This prevents Phase 5B from sending huge raw artifacts to the LLM.
    """

    def build(self) -> Dict[str, Any]:
        daily_packet = load_json(RESULTS_DIR / "ai_daily_research_packet.json")
        research_committee = load_json(RESULTS_DIR / "ai_research_committee.json")
        research_desk = load_json(RESULTS_DIR / "ai_research_desk_orchestrator.json")

        live_snapshot = load_json("results/realtime/live_market_snapshot.json")
        approval_gate = load_json("results/governance/portfolio_approval_gate.json")
        readiness = load_json("results/institutional/institutional_readiness_report.json")
        portfolio_state = load_json("results/portfolio_state/institutional_portfolio_state.json")
        operating_report = load_json("results/portfolio/portfolio_operating_report.json")

        committee_decision = load_json(RESULTS_DIR / "committee_decision.json")

        context = {
            "generated_at": utc_now(),
            "context_type": "compressed_committee_context",
            "purpose": "low_token_phase5b_committee_input",

            "market_state": {
                "current_regime": (
                    safe_get(research_desk, ["regime_agent", "current_regime"])
                    or safe_get(research_committee, ["regime_agent", "current_regime"])
                    or "unknown"
                ),
                "expected_regime": (
                    safe_get(research_desk, ["regime_agent", "expected_next_regime"])
                    or safe_get(research_committee, ["regime_agent", "expected_next_regime"])
                    or "unknown"
                ),
                "regime_confidence": (
                    safe_get(research_desk, ["regime_agent", "confidence"])
                    or safe_get(research_committee, ["regime_agent", "confidence"])
                ),
                "overall_research_view": compact_text(
                    research_desk.get("overall_view")
                    or research_desk.get("executive_summary")
                    or daily_packet.get("executive_summary")
                ),
                "recommended_posture": (
                    research_desk.get("recommended_posture")
                    or committee_decision.get("investment_view")
                    or "unknown"
                ),
            },

            "risk_state": {
                "desk_risk_score": research_desk.get("desk_risk_score"),
                "highest_risk": compact_text(research_desk.get("highest_risk"), 300),
                "risk_summary": compact_text(
                    safe_get(research_desk, ["risk_agent", "summary"])
                    or safe_get(research_committee, ["risk_agent", "summary"])
                    or research_desk.get("risk_view")
                ),
                "digital_twin_summary": compact_text(
                    safe_get(research_desk, ["digital_twin_agent", "summary"])
                    or safe_get(research_committee, ["digital_twin_agent", "summary"])
                ),
            },

            "governance_state": {
                "approval_decision": (
                    approval_gate.get("approval_decision")
                    or approval_gate.get("decision")
                    or committee_decision.get("approval_status")
                    or "unknown"
                ),
                "allow_execution": (
                    approval_gate.get("allow_execution")
                    if "allow_execution" in approval_gate
                    else None
                ),
                "compliance_status": (
                    approval_gate.get("compliance_status")
                    or safe_get(readiness, ["governance", "compliance_status"])
                    or "unknown"
                ),
                "execution_permission": committee_decision.get("execution_permission", "unknown"),
                "execution_blockers": committee_decision.get("execution_blockers", [])[:8],
                "conditions_for_execution": committee_decision.get("conditions_for_execution", [])[:8],
            },

            "portfolio_state": {
                "portfolio_status": (
                    portfolio_state.get("portfolio_status")
                    or operating_report.get("portfolio_status")
                    or "unknown"
                ),
                "current_weights": (
                    portfolio_state.get("weights")
                    or portfolio_state.get("current_weights")
                    or operating_report.get("current_weights")
                    or {}
                ),
                "portfolio_health_score": (
                    operating_report.get("portfolio_health_score")
                    or portfolio_state.get("portfolio_health_score")
                ),
                "known_issues": (
                    operating_report.get("key_issues", [])[:8]
                    if isinstance(operating_report.get("key_issues", []), list)
                    else []
                ),
            },

            "live_market_snapshot": self._compress_live_snapshot(live_snapshot),

            "prior_committee_state": {
                "investment_view": committee_decision.get("investment_view"),
                "execution_permission": committee_decision.get("execution_permission"),
                "approval_status": committee_decision.get("approval_status"),
                "committee_confidence": committee_decision.get("committee_confidence"),
                "vote_summary": committee_decision.get("vote_summary", {}),
                "target_allocation": committee_decision.get("target_allocation", {}),
                "final_recommendation": compact_text(
                    committee_decision.get("final_recommendation"),
                    700,
                ),
            },

            "committee_instruction": {
                "must_separate_investment_view_from_execution_permission": True,
                "must_not_execute_trades": True,
                "must_return_target_allocation_even_if_prepared_only": True,
                "must_keep_response_concise": True,
            },
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w", encoding="utf-8") as f:
            json.dump(context, f, indent=2)

        return context

    def _compress_live_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        records = snapshot.get("records", snapshot)

        compressed = {}

        if isinstance(records, list):
            for row in records:
                if not isinstance(row, dict):
                    continue
                ticker = row.get("ticker") or row.get("symbol")
                if ticker:
                    compressed[ticker] = {
                        "price": row.get("price"),
                        "timestamp": row.get("timestamp"),
                        "source": row.get("source"),
                    }

        elif isinstance(records, dict):
            for ticker, row in records.items():
                if isinstance(row, dict):
                    compressed[ticker] = {
                        "price": row.get("price"),
                        "timestamp": row.get("timestamp"),
                        "source": row.get("source"),
                    }

        return compressed


def main() -> None:
    print("=" * 80)
    print("AURUM COMMITTEE CONTEXT BUILDER")
    print("=" * 80)

    builder = CommitteeContextBuilder()
    context = builder.build()

    print(f"Context Type: {context.get('context_type')}")
    print(f"Current Regime: {context['market_state'].get('current_regime')}")
    print(f"Recommended Posture: {context['market_state'].get('recommended_posture')}")
    print(f"Execution Permission: {context['governance_state'].get('execution_permission')}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()