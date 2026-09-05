from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.config.storage_paths import artifact_path, ensure_storage_dirs
from src.digital_twin.anomaly_aware_digital_twin_adapter import AnomalyAwareDigitalTwinAdapter
from src.intelligence.institutional_anomaly_signal_generator import InstitutionalAnomalySignalGenerator
from src.market.providers.provider_factory import get_provider
from src.regimes.hmm_live_state_adapter import HMMLiveStateAdapter


@dataclass
class LiveMarketRefreshResult:
    event_type: str
    timestamp: str
    provider: str
    tickers: List[str]
    rows_by_ticker: Dict[str, int]
    feature_rows: int
    regime_probability_type: str
    current_regime: int
    anomaly_severity: str
    anomaly_score: float
    adjusted_stress_score: float
    digital_twin_state: str
    portfolio_os_action: str
    refresh_status: str


class LiveMarketRefreshOrchestrator:
    """
    Sprint 3B live refresh orchestrator.

    Flow:
        Market Data
        -> Features
        -> Regime
        -> Anomaly Signal
        -> Digital Twin Stress
        -> Portfolio OS Action
    """

    def __init__(
        self,
        provider_name: str = "yfinance",
        tickers: List[str] | None = None,
        period: str = "6mo",
        interval: str = "1d",
    ) -> None:
        self.provider = get_provider(provider_name)
        self.tickers = tickers or ["SPY", "QQQ", "DIA", "TLT", "GLD"]
        self.period = period
        self.interval = interval

    def run_once(self, publish_to_redis: bool = True) -> LiveMarketRefreshResult:
        ensure_storage_dirs()

        timestamp = datetime.now(timezone.utc).isoformat()

        price_data = self._load_market_data()
        features = self._build_features(price_data)

        hmm_state = HMMLiveStateAdapter().run(features)

        primary_returns = price_data["SPY"]["Close"].pct_change().dropna()

        anomaly_signal = InstitutionalAnomalySignalGenerator().generate(
            primary_returns,
            publish_to_redis=publish_to_redis,
        )

        base_stress_score = self._base_stress_from_features(features)

        digital_twin_state = AnomalyAwareDigitalTwinAdapter(
            anomaly_weight=0.20
        ).update_state(
            base_stress_score=base_stress_score,
            anomaly_signal=anomaly_signal,
        )

        portfolio_os_action = self._portfolio_os_action(
            digital_twin_state.adjusted_stress_score
        )

        result = LiveMarketRefreshResult(
            event_type="live_market_refresh",
            timestamp=timestamp,
            provider=self.provider.provider_name,
            tickers=self.tickers,
            rows_by_ticker={
                ticker: int(len(frame)) for ticker, frame in price_data.items()
            },
            feature_rows=int(len(features)),
            regime_probability_type=hmm_state.probability_type,
            current_regime=int(hmm_state.current_regime),
            anomaly_severity=anomaly_signal.severity,
            anomaly_score=float(anomaly_signal.score),
            adjusted_stress_score=float(digital_twin_state.adjusted_stress_score),
            digital_twin_state=digital_twin_state.state_label,
            portfolio_os_action=portfolio_os_action,
            refresh_status="completed",
        )

        self._save_result(result)
        return result

    def run_loop(
        self,
        refresh_minutes: int = 5,
        max_cycles: int | None = None,
        publish_to_redis: bool = True,
    ) -> None:
        cycle = 0

        while True:
            cycle += 1
            result = self.run_once(publish_to_redis=publish_to_redis)

            print("=" * 80)
            print("AURUM LIVE MARKET REFRESH")
            print("=" * 80)
            print(f"Cycle:              {cycle}")
            print(f"Timestamp:          {result.timestamp}")
            print(f"Provider:           {result.provider}")
            print(f"Regime:             state_{result.current_regime}")
            print(f"Probability Type:   {result.regime_probability_type}")
            print(f"Anomaly Severity:   {result.anomaly_severity}")
            print(f"Stress Score:       {result.adjusted_stress_score:.4f}")
            print(f"Digital Twin State: {result.digital_twin_state}")
            print(f"Portfolio Action:   {result.portfolio_os_action}")
            print("=" * 80)

            if max_cycles is not None and cycle >= max_cycles:
                break

            time.sleep(refresh_minutes * 60)

    def _load_market_data(self) -> Dict[str, pd.DataFrame]:
        data = {}

        for ticker in self.tickers:
            frame = self.provider.get_prices(
                ticker=ticker,
                period=self.period,
                interval=self.interval,
            )

            if frame.empty:
                raise ValueError(f"No market data returned for {ticker}")

            if "Close" not in frame.columns:
                raise ValueError(f"Close column missing for {ticker}")

            data[ticker] = frame.dropna()

        return data

    def _build_features(self, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        closes = pd.DataFrame(
            {
                ticker: frame["Close"]
                for ticker, frame in price_data.items()
            }
        ).dropna()

        returns = closes.pct_change().dropna()

        spy_returns = returns["SPY"]

        features = pd.DataFrame(index=returns.index)
        features["market_return"] = spy_returns
        features["rolling_volatility"] = spy_returns.rolling(20).std()
        features["cross_asset_dispersion"] = returns.std(axis=1)
        features["equity_momentum_20d"] = closes["SPY"].pct_change(20)
        features["bond_momentum_20d"] = closes["TLT"].pct_change(20)
        features["gold_momentum_20d"] = closes["GLD"].pct_change(20)

        features = features.replace([np.inf, -np.inf], np.nan).dropna()

        if len(features) < 80:
            raise ValueError(
                f"Not enough feature rows for live refresh. Rows={len(features)}"
            )

        return features

    @staticmethod
    def _base_stress_from_features(features: pd.DataFrame) -> float:
        latest = features.iloc[-1]

        vol = float(latest["rolling_volatility"])
        dispersion = float(latest["cross_asset_dispersion"])
        momentum = float(latest["equity_momentum_20d"])

        vol_score = min(1.0, vol / 0.03)
        dispersion_score = min(1.0, dispersion / 0.025)
        momentum_score = min(1.0, max(0.0, -momentum / 0.08))

        return float(
            0.45 * vol_score
            + 0.25 * dispersion_score
            + 0.30 * momentum_score
        )

    @staticmethod
    def _portfolio_os_action(stress_score: float) -> str:
        if stress_score >= 0.80:
            return "block_execution_reduce_risk"
        if stress_score >= 0.60:
            return "reduce_risk"
        if stress_score >= 0.35:
            return "watch"
        return "normal"

    @staticmethod
    def _save_result(result: LiveMarketRefreshResult) -> None:
        output = artifact_path("sprint3", "live_market_refresh_result.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(asdict(result), indent=4), encoding="utf-8")


def main() -> None:
    orchestrator = LiveMarketRefreshOrchestrator(
        provider_name="yfinance",
        tickers=["SPY", "QQQ", "DIA", "TLT", "GLD"],
        period="6mo",
        interval="1d",
    )

    result = orchestrator.run_once(publish_to_redis=True)

    print("=" * 80)
    print("AURUM LIVE MARKET REFRESH ORCHESTRATOR")
    print("=" * 80)
    print(f"Provider:           {result.provider}")
    print(f"Tickers:            {', '.join(result.tickers)}")
    print(f"Feature Rows:       {result.feature_rows}")
    print(f"Regime:             state_{result.current_regime}")
    print(f"Probability Type:   {result.regime_probability_type}")
    print(f"Anomaly Severity:   {result.anomaly_severity}")
    print(f"Anomaly Score:      {result.anomaly_score:.4f}")
    print(f"Stress Score:       {result.adjusted_stress_score:.4f}")
    print(f"Digital Twin State: {result.digital_twin_state}")
    print(f"Portfolio Action:   {result.portfolio_os_action}")
    print(f"Status:             {result.refresh_status}")
    print("=" * 80)


if __name__ == "__main__":
    main()