from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.storage_paths import artifact_path, ensure_storage_dirs


@dataclass
class LiveRefreshDashboardState:
    live_refresh_available: bool
    scheduled_refresh_available: bool
    provider: str
    timestamp: str
    regime: str
    probability_type: str
    anomaly_severity: str
    anomaly_score: float
    stress_score: float
    digital_twin_state: str
    portfolio_action: str
    cycles_completed: int
    status: str


class LiveRefreshDashboardAdapter:
    """
    Reads Sprint 3 live refresh artifacts and converts them into dashboard-ready state.
    """

    def __init__(self) -> None:
        self.live_refresh_path = artifact_path("sprint3", "live_market_refresh_result.json")
        self.scheduled_summary_path = artifact_path("sprint3", "scheduled_refresh_summary.json")

    def load_state(self) -> LiveRefreshDashboardState:
        live = self._read_json(self.live_refresh_path)
        scheduled = self._read_json(self.scheduled_summary_path)

        live_available = live is not None
        scheduled_available = scheduled is not None

        state = LiveRefreshDashboardState(
            live_refresh_available=live_available,
            scheduled_refresh_available=scheduled_available,
            provider=str(live.get("provider", "unavailable")) if live else "unavailable",
            timestamp=str(live.get("timestamp", "unavailable")) if live else "unavailable",
            regime=f"state_{live.get('current_regime', 'unavailable')}" if live else "unavailable",
            probability_type=str(live.get("regime_probability_type", "unavailable")) if live else "unavailable",
            anomaly_severity=str(live.get("anomaly_severity", "unavailable")) if live else "unavailable",
            anomaly_score=float(live.get("anomaly_score", 0.0)) if live else 0.0,
            stress_score=float(live.get("adjusted_stress_score", 0.0)) if live else 0.0,
            digital_twin_state=str(live.get("digital_twin_state", "unavailable")) if live else "unavailable",
            portfolio_action=str(live.get("portfolio_os_action", "unavailable")) if live else "unavailable",
            cycles_completed=int(scheduled.get("cycles_completed", 0)) if scheduled else 0,
            status=str(live.get("refresh_status", "unavailable")) if live else "unavailable",
        )

        self._save_state(state)
        return state

    @staticmethod
    def _read_json(path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def _save_state(state: LiveRefreshDashboardState) -> None:
        ensure_storage_dirs()
        output = artifact_path("sprint3", "live_refresh_dashboard_state.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(asdict(state), indent=4), encoding="utf-8")


def main() -> None:
    state = LiveRefreshDashboardAdapter().load_state()

    print("=" * 80)
    print("AURUM LIVE REFRESH DASHBOARD ADAPTER")
    print("=" * 80)
    print(f"Live Available:      {state.live_refresh_available}")
    print(f"Scheduled Available: {state.scheduled_refresh_available}")
    print(f"Provider:            {state.provider}")
    print(f"Regime:              {state.regime}")
    print(f"Probability Type:    {state.probability_type}")
    print(f"Anomaly Severity:    {state.anomaly_severity}")
    print(f"Stress Score:        {state.stress_score:.4f}")
    print(f"Digital Twin State:  {state.digital_twin_state}")
    print(f"Portfolio Action:    {state.portfolio_action}")
    print(f"Cycles Completed:    {state.cycles_completed}")
    print(f"Status:              {state.status}")
    print("=" * 80)


if __name__ == "__main__":
    main()