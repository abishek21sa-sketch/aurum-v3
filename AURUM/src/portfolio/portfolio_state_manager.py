# src/portfolio/portfolio_state_manager.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


STATE_DIR = Path("results/portfolio_state")
STATE_DIR.mkdir(parents=True, exist_ok=True)

PORTFOLIO_STATE_PATH = STATE_DIR / "institutional_portfolio_state.json"


class PortfolioStateManager:
    def __init__(self, state_path: Path = PORTFOLIO_STATE_PATH):
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def build_state(self) -> Dict[str, Any]:
        current_portfolio = self.load_json(Path("results/execution/current_portfolio_state.json"))
        target_portfolio = self.load_json(Path("results/execution/target_portfolio.json"))
        approval = self.load_json(Path("results/governance/portfolio_approval_decision.json"))
        lifecycle = self.load_json(Path("results/execution/lifecycle_report.json"))

        state = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "state_type": "INSTITUTIONAL_PORTFOLIO_STATE",
            "current_portfolio": current_portfolio,
            "target_portfolio": target_portfolio,
            "governance_approval": approval,
            "execution_lifecycle": lifecycle,
            "state_summary": {
                "has_current_portfolio": bool(current_portfolio),
                "has_target_portfolio": bool(target_portfolio),
                "has_governance_approval": bool(approval),
                "has_execution_lifecycle": bool(lifecycle),
            },
        }

        self.state_path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        return state


def main():
    manager = PortfolioStateManager()
    state = manager.build_state()

    print("=" * 80)
    print("AURUM PORTFOLIO STATE MANAGER")
    print("=" * 80)
    print(json.dumps(state["state_summary"], indent=2))


if __name__ == "__main__":
    main()