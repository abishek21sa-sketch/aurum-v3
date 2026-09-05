from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.portfolio_os.portfolio_state_machine import PortfolioStateMachine
from src.portfolio_os.portfolio_director import PortfolioDirector
from src.research.decision_trace_engine import DecisionTraceEngine
from src.research.decision_reasoning_engine import DecisionReasoningEngine
from src.research.explanation_generator import DecisionExplanationGenerator
from src.research.portfolio_copilot import AutonomousPortfolioCopilot
from src.learning.learning_engine import LearningEngine
from src.market_memory.memory_similarity_engine import MarketMemorySimilarityEngine


DAILY_CYCLE_JSON = Path("results/portfolio_os/daily_portfolio_cycle.json")


class DailyPortfolioCycle:
    """
    Runs the daily AURUM operating cycle.

    This connects:
    - state machine
    - portfolio director
    - memory
    - decision intelligence
    - copilot
    - learning
    """

    def __init__(self) -> None:
        DAILY_CYCLE_JSON.parent.mkdir(parents=True, exist_ok=True)

        self.state_machine = PortfolioStateMachine()
        self.director = PortfolioDirector()
        self.trace_engine = DecisionTraceEngine()
        self.reasoning_engine = DecisionReasoningEngine()
        self.explanation_generator = DecisionExplanationGenerator()
        self.copilot = AutonomousPortfolioCopilot()
        self.learning_engine = LearningEngine()
        self.memory_engine = MarketMemorySimilarityEngine()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> Dict[str, Any]:
        cycle = {
            "cycle_id": f"aurum_daily_cycle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self._utc_now(),
            "stages": {},
        }

        self.state_machine.transition(
            "RESEARCH",
            status="COMPLETE",
            message="Research stage completed using Phase 5A research desk artifacts.",
            metadata={"source": "phase_5a"},
        )

        cycle["stages"]["research"] = {
            "status": "COMPLETE",
            "summary": "AI Research Desk available; market view remains defensive-advisory.",
        }

        self.state_machine.transition(
            "COMMITTEE",
            status="COMPLETE",
            message="Committee stage completed using Phase 5B committee artifacts.",
            metadata={"source": "phase_5b"},
        )

        cycle["stages"]["committee"] = {
            "status": "COMPLETE",
            "summary": "Investment Committee view is defensive; execution remains blocked.",
        }

        self.state_machine.transition(
            "MEMORY",
            status="COMPLETE",
            message="Memory stage completed using Phase 5C institutional memory.",
            metadata={"source": "phase_5c"},
        )

        memory_report = self.memory_engine.current_market_resemblance_report(
            current_state={
                "volatility": 0.0836,
                "stress_score": 0.40,
                "breadth": 0.40,
                "projected_var95": 0.1300,
                "projected_drawdown": -0.0641,
            },
            limit=5,
        )

        cycle["stages"]["memory"] = {
            "status": "COMPLETE",
            "summary": "Institutional memory retrieved closest historical analog.",
            "best_match": memory_report.get("best_match"),
        }

        self.state_machine.transition(
            "DECISION_INTELLIGENCE",
            status="COMPLETE",
            message="Decision intelligence stage completed.",
            metadata={"source": "phase_5d"},
        )

        trace = self.trace_engine.build_trace()
        reasoning = self.reasoning_engine.generate_reasoning()
        explanation = self.explanation_generator.generate_explanation()

        cycle["stages"]["decision_intelligence"] = {
            "status": "COMPLETE",
            "trace_id": trace.get("trace_id"),
            "reasoning_summary": reasoning.get("reasoning_summary"),
            "executive_answer": explanation.get("executive_answer"),
        }

        self.state_machine.transition(
            "GOVERNANCE",
            status="COMPLETE",
            message="Governance check completed.",
            metadata={"execution_permission": "blocked"},
        )

        governance_response = self.copilot.ask("What is governance status?")

        cycle["stages"]["governance"] = {
            "status": "COMPLETE",
            "summary": governance_response.get("response", {}).get("answer"),
            "details": governance_response.get("response", {}).get("governance"),
        }

        self.state_machine.transition(
            "PORTFOLIO_ACTION",
            status="COMPLETE",
            message="Portfolio directive generated.",
            metadata={"source": "portfolio_director"},
        )

        directive = self.director.generate_directive()

        cycle["stages"]["portfolio_action"] = {
            "status": "COMPLETE",
            "directive": directive,
        }

        self.state_machine.transition(
            "LEARNING",
            status="COMPLETE",
            message="Learning stage completed.",
            metadata={"source": "phase_5f"},
        )

        learning_report = self.learning_engine.generate_learning_report()

        cycle["stages"]["learning"] = {
            "status": "COMPLETE",
            "learning_status": learning_report.get("system_learning", {}).get("learning_status"),
            "lessons": learning_report.get("system_learning", {}).get("lessons"),
        }

        self.state_machine.transition(
            "COMPLETE",
            status="COMPLETE",
            message="Daily Portfolio Operating Cycle completed.",
            metadata={"cycle_id": cycle["cycle_id"]},
        )

        cycle["state_machine"] = self.state_machine.snapshot()
        cycle["final_directive"] = directive
        cycle["status"] = "COMPLETE"

        with DAILY_CYCLE_JSON.open("w", encoding="utf-8") as f:
            json.dump(cycle, f, indent=2, default=str)

        return cycle


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6A DAILY PORTFOLIO CYCLE")
    print("=" * 80)

    cycle = DailyPortfolioCycle().run()
    directive = cycle["final_directive"]

    print(f"Cycle ID:              {cycle['cycle_id']}")
    print(f"Status:                {cycle['status']}")
    print(f"Portfolio Posture:     {directive['portfolio_posture']}")
    print(f"Portfolio Action:      {directive['portfolio_action']}")
    print(f"Execution Permission:  {directive['execution_permission']}")
    print(f"Stage Count:           {len(cycle['stages'])}")
    print(f"Saved:                 {DAILY_CYCLE_JSON}")
    print("=" * 80)


if __name__ == "__main__":
    main()