from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from src.config.storage_paths import artifact_path, ensure_storage_dirs
from src.orchestration.live_market_refresh_orchestrator import (
    LiveMarketRefreshOrchestrator,
    LiveMarketRefreshResult,
)


@dataclass
class ScheduledRefreshSummary:
    event_type: str
    timestamp: str
    provider: str
    tickers: List[str]
    interval_seconds: int
    cycles_requested: int
    cycles_completed: int
    latest_refresh_status: str
    latest_portfolio_action: str
    latest_stress_score: float
    latest_digital_twin_state: str
    history_path: str
    status: str


class ScheduledRefreshRunner:
    """
    Sprint 3C scheduled refresh runner.

    Wraps LiveMarketRefreshOrchestrator with:
    - repeated refresh cycles
    - JSONL history
    - safe max_cycles
    - summary artifact
    """

    def __init__(
        self,
        provider_name: str = "yfinance",
        tickers: List[str] | None = None,
        period: str = "6mo",
        interval: str = "1d",
        interval_seconds: int = 300,
    ) -> None:
        self.provider_name = provider_name
        self.tickers = tickers or ["SPY", "QQQ", "DIA", "TLT", "GLD"]
        self.period = period
        self.interval = interval
        self.interval_seconds = interval_seconds

        self.orchestrator = LiveMarketRefreshOrchestrator(
            provider_name=provider_name,
            tickers=self.tickers,
            period=period,
            interval=interval,
        )

    def run(
        self,
        max_cycles: int = 1,
        publish_to_redis: bool = True,
        sleep_between_cycles: bool = True,
    ) -> ScheduledRefreshSummary:
        if max_cycles <= 0:
            raise ValueError("max_cycles must be positive.")

        ensure_storage_dirs()

        history_path = artifact_path("sprint3", "scheduled_refresh_history.jsonl")
        history_path.parent.mkdir(parents=True, exist_ok=True)

        latest_result: LiveMarketRefreshResult | None = None
        cycles_completed = 0

        for cycle in range(1, max_cycles + 1):
            result = self.orchestrator.run_once(publish_to_redis=publish_to_redis)
            latest_result = result
            cycles_completed += 1

            history_event = {
                "cycle": cycle,
                **asdict(result),
            }

            with history_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(history_event) + "\n")

            print("=" * 80)
            print("AURUM SCHEDULED REFRESH RUNNER")
            print("=" * 80)
            print(f"Cycle:              {cycle}/{max_cycles}")
            print(f"Provider:           {result.provider}")
            print(f"Regime:             state_{result.current_regime}")
            print(f"Anomaly Severity:   {result.anomaly_severity}")
            print(f"Stress Score:       {result.adjusted_stress_score:.4f}")
            print(f"Digital Twin State: {result.digital_twin_state}")
            print(f"Portfolio Action:   {result.portfolio_os_action}")
            print("=" * 80)

            if cycle < max_cycles and sleep_between_cycles:
                time.sleep(self.interval_seconds)

        if latest_result is None:
            raise RuntimeError("Scheduled refresh completed zero cycles.")

        summary = ScheduledRefreshSummary(
            event_type="scheduled_live_market_refresh",
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider=self.provider_name,
            tickers=self.tickers,
            interval_seconds=int(self.interval_seconds),
            cycles_requested=int(max_cycles),
            cycles_completed=int(cycles_completed),
            latest_refresh_status=latest_result.refresh_status,
            latest_portfolio_action=latest_result.portfolio_os_action,
            latest_stress_score=float(latest_result.adjusted_stress_score),
            latest_digital_twin_state=latest_result.digital_twin_state,
            history_path=str(history_path),
            status="completed",
        )

        self._save_summary(summary)
        return summary

    @staticmethod
    def _save_summary(summary: ScheduledRefreshSummary) -> None:
        output = artifact_path("sprint3", "scheduled_refresh_summary.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(asdict(summary), indent=4), encoding="utf-8")


def main() -> None:
    runner = ScheduledRefreshRunner(
        provider_name="yfinance",
        tickers=["SPY", "QQQ", "DIA", "TLT", "GLD"],
        period="6mo",
        interval="1d",
        interval_seconds=300,
    )

    summary = runner.run(
        max_cycles=1,
        publish_to_redis=True,
        sleep_between_cycles=False,
    )

    print("=" * 80)
    print("AURUM SCHEDULED REFRESH SUMMARY")
    print("=" * 80)
    print(f"Provider:              {summary.provider}")
    print(f"Cycles Completed:      {summary.cycles_completed}")
    print(f"Latest Portfolio Act:  {summary.latest_portfolio_action}")
    print(f"Latest Stress Score:   {summary.latest_stress_score:.4f}")
    print(f"Digital Twin State:    {summary.latest_digital_twin_state}")
    print(f"History Path:          {summary.history_path}")
    print(f"Status:                {summary.status}")
    print("=" * 80)


if __name__ == "__main__":
    main()