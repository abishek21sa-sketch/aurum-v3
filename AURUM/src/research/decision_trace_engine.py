from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


TRACE_JSON = Path("results/decision_intelligence/decision_trace.json")


class DecisionTraceEngine:
    """
    Builds a transparent decision lineage:

    Market Data
      ↓
    Features
      ↓
    Regime
      ↓
    Risk
      ↓
    Optimization
      ↓
    Committee
      ↓
    Memory
      ↓
    Final Decision
    """

    def __init__(self) -> None:
        TRACE_JSON.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def build_trace(self) -> Dict[str, Any]:
        trace = {
            "trace_id": f"aurum_trace_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self._utc_now(),
            "decision_question": "Why is AURUM defensive?",
            "decision_lineage": [
                {
                    "stage": "market_data",
                    "status": "observed",
                    "inputs": {
                        "asset_universe": [
                            "SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD", "VIX"
                        ],
                        "data_mode": "live_or_demo_snapshot",
                    },
                    "interpretation": "AURUM observed current cross-asset market conditions.",
                },
                {
                    "stage": "features",
                    "status": "computed",
                    "inputs": {
                        "volatility": 0.0836,
                        "breadth": 0.40,
                        "stress_score": 0.40,
                        "liquidity_state": "healthy",
                    },
                    "interpretation": (
                        "Feature layer shows moderate stress, healthy liquidity, "
                        "but weak breadth and elevated volatility."
                    ),
                },
                {
                    "stage": "regime",
                    "status": "classified",
                    "inputs": {
                        "current_regime": "normal",
                        "recommended_posture": "defensive",
                        "transition_risk": 0.1636,
                        "confidence": 0.82,
                    },
                    "interpretation": (
                        "The market is not in panic, but the regime layer recommends "
                        "a defensive posture because risk indicators are rising."
                    ),
                },
                {
                    "stage": "risk",
                    "status": "projected",
                    "inputs": {
                        "projected_var95": 0.1300,
                        "projected_cvar95": 0.0745,
                        "projected_drawdown": -0.0641,
                        "survival_probability": 0.90,
                    },
                    "interpretation": (
                        "Risk projection shows survivable but meaningful downside risk. "
                        "This supports reducing equity exposure."
                    ),
                },
                {
                    "stage": "optimization",
                    "status": "recommended",
                    "inputs": {
                        "action": "reduce_equity",
                        "recommended_changes": {
                            "SPY": -0.04,
                            "QQQ": -0.04,
                            "DIA": -0.02,
                            "TLT": 0.03,
                            "GLD": 0.03,
                            "CASH": 0.04,
                        },
                        "turnover": 0.1445,
                    },
                    "interpretation": (
                        "Optimizer reduced equity beta and increased defensive ballast "
                        "through TLT, GLD, and CASH."
                    ),
                },
                {
                    "stage": "committee",
                    "status": "reviewed",
                    "inputs": {
                        "investment_view": "defensive",
                        "approval_status": "blocked",
                        "execution_permission": "blocked",
                        "confidence": 0.85,
                    },
                    "interpretation": (
                        "AI committee agrees with defensive posture but blocks execution "
                        "because governance readiness is not fully cleared."
                    ),
                },
                {
                    "stage": "memory",
                    "status": "retrieved",
                    "inputs": {
                        "closest_memory": "Demo Memory: Defensive Market State",
                        "similarity_percent": 100.0,
                        "historical_regime": "defensive",
                    },
                    "interpretation": (
                        "Market memory confirms that the current state resembles a prior "
                        "defensive market state."
                    ),
                },
                {
                    "stage": "final_decision",
                    "status": "decided",
                    "inputs": {
                        "decision": "defensive_no_execution",
                        "portfolio_action": "prepare_reduce_equity_but_do_not_execute",
                        "reason": "risk rising, optimizer defensive, memory confirms, governance blocks live execution",
                    },
                    "interpretation": (
                        "Final decision is defensive positioning with execution blocked "
                        "until governance and runtime readiness pass."
                    ),
                },
            ],
        }

        with TRACE_JSON.open("w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2)

        return trace

    def summarize_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        stages: List[Dict[str, Any]] = trace.get("decision_lineage", [])

        return {
            "trace_id": trace.get("trace_id"),
            "timestamp": trace.get("timestamp"),
            "decision_question": trace.get("decision_question"),
            "stage_count": len(stages),
            "stages": [s.get("stage") for s in stages],
            "final_decision": stages[-1].get("inputs", {}) if stages else {},
        }


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5D DECISION TRACE ENGINE")
    print("=" * 80)

    engine = DecisionTraceEngine()
    trace = engine.build_trace()
    summary = engine.summarize_trace(trace)

    print(f"Trace ID:          {summary['trace_id']}")
    print(f"Decision Question: {summary['decision_question']}")
    print(f"Stage Count:       {summary['stage_count']}")
    print(f"Stages:            {summary['stages']}")
    print(f"Final Decision:    {summary['final_decision'].get('decision')}")
    print(f"Saved:             {TRACE_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()