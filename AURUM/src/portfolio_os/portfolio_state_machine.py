from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


STATE_MACHINE_JSON = Path("results/portfolio_os/portfolio_state_machine.json")


VALID_STATES = [
    "INITIALIZED",
    "RESEARCH",
    "COMMITTEE",
    "MEMORY",
    "DECISION_INTELLIGENCE",
    "GOVERNANCE",
    "PORTFOLIO_ACTION",
    "LEARNING",
    "COMPLETE",
]


VALID_TRANSITIONS = {
    "INITIALIZED": ["RESEARCH"],
    "RESEARCH": ["COMMITTEE"],
    "COMMITTEE": ["MEMORY"],
    "MEMORY": ["DECISION_INTELLIGENCE"],
    "DECISION_INTELLIGENCE": ["GOVERNANCE"],
    "GOVERNANCE": ["PORTFOLIO_ACTION"],
    "PORTFOLIO_ACTION": ["LEARNING"],
    "LEARNING": ["COMPLETE"],
    "COMPLETE": [],
}


@dataclass
class PortfolioOSState:
    current_state: str
    previous_state: Optional[str]
    timestamp: str
    status: str
    message: str
    metadata: Dict[str, Any]


class PortfolioStateMachine:
    """
    AURUM Portfolio Operating System state machine.

    Controls the institutional workflow:

    INITIALIZED
        ↓
    RESEARCH
        ↓
    COMMITTEE
        ↓
    MEMORY
        ↓
    DECISION_INTELLIGENCE
        ↓
    GOVERNANCE
        ↓
    PORTFOLIO_ACTION
        ↓
    LEARNING
        ↓
    COMPLETE
    """

    def __init__(self) -> None:
        STATE_MACHINE_JSON.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = []
        self.current_state = "INITIALIZED"
        self._record_state(
            current_state="INITIALIZED",
            previous_state=None,
            status="READY",
            message="Portfolio Operating System initialized.",
            metadata={"phase": "6A"},
        )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_state(
        self,
        current_state: str,
        previous_state: Optional[str],
        status: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        state = PortfolioOSState(
            current_state=current_state,
            previous_state=previous_state,
            timestamp=self._utc_now(),
            status=status,
            message=message,
            metadata=metadata or {},
        )

        payload = asdict(state)
        self.history.append(payload)
        self.current_state = current_state
        self._save()

        return payload

    def can_transition(self, next_state: str) -> bool:
        next_state = next_state.upper().strip()

        if next_state not in VALID_STATES:
            return False

        return next_state in VALID_TRANSITIONS.get(self.current_state, [])

    def transition(
        self,
        next_state: str,
        status: str = "RUNNING",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        next_state = next_state.upper().strip()

        if next_state not in VALID_STATES:
            raise ValueError(f"Invalid state: {next_state}")

        if not self.can_transition(next_state):
            raise ValueError(
                f"Invalid transition: {self.current_state} -> {next_state}"
            )

        previous_state = self.current_state

        return self._record_state(
            current_state=next_state,
            previous_state=previous_state,
            status=status,
            message=message or f"Transitioned from {previous_state} to {next_state}.",
            metadata=metadata or {},
        )

    def run_full_cycle(self) -> Dict[str, Any]:
        sequence = [
            "RESEARCH",
            "COMMITTEE",
            "MEMORY",
            "DECISION_INTELLIGENCE",
            "GOVERNANCE",
            "PORTFOLIO_ACTION",
            "LEARNING",
            "COMPLETE",
        ]

        for state in sequence:
            self.transition(
                state,
                status="COMPLETE" if state == "COMPLETE" else "RUNNING",
                message=f"Portfolio OS entered {state} stage.",
                metadata={"auto_cycle": True},
            )

        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state,
            "state_count": len(self.history),
            "valid_states": VALID_STATES,
            "history": self.history,
        }

    def _save(self) -> None:
        with STATE_MACHINE_JSON.open("w", encoding="utf-8") as f:
            json.dump(self.snapshot(), f, indent=2, default=str)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6A PORTFOLIO STATE MACHINE")
    print("=" * 80)

    machine = PortfolioStateMachine()
    snapshot = machine.run_full_cycle()

    print(f"Current State: {snapshot['current_state']}")
    print(f"State Count:   {snapshot['state_count']}")
    print(f"Saved:         {STATE_MACHINE_JSON}")
    print("-" * 80)

    for event in snapshot["history"]:
        print(
            f"{event['previous_state']} -> {event['current_state']} | "
            f"{event['status']} | {event['message']}"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()