# src/digital_twin/live_digital_twin_state_engine.py

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

STREAM_TICKS = "market_ticks"
STREAM_FEATURES = "market_features"
STREAM_ALERTS = "market_alerts"
STREAM_SIGNALS = "market_signals"

REGIME_SUMMARY_CANDIDATES = [
    Path("data/regimes/next_regime_forecast.csv"),
    Path("data/regimes/market_regime_summary.csv"),
    Path("data/regimes/regime_summary.csv"),
]

OUTPUT_DIR = Path("results/digital_twin/live_state")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LIVE_STATE_PATH = OUTPUT_DIR / "live_market_state.json"
LIVE_STATE_TXT_PATH = OUTPUT_DIR / "live_market_state_report.txt"


@dataclass
class LiveDigitalTwinState:
    event_type: str
    timestamp_utc: str
    latest_ticker: str
    latest_price: Optional[float]
    tick_age_seconds: Optional[float]
    feature_age_seconds: Optional[float]
    alert_age_seconds: Optional[float]
    tick_stream_length: int
    feature_stream_length: int
    alert_stream_length: int
    current_regime: str
    volatility_state: str
    liquidity_state: str
    alert_state: str
    market_stress_score: float
    state_label: str
    redis_event_id: Optional[str] = None


class LiveDigitalTwinStateEngine:
    def __init__(self) -> None:
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

    def latest_entry(self, stream: str) -> tuple[Optional[str], Dict[str, Any]]:
        rows = self.redis_client.xrevrange(stream, count=1)
        if not rows:
            return None, {}
        row_id, payload = rows[0]
        return row_id, payload

    def stream_length(self, stream: str) -> int:
        try:
            return int(self.redis_client.xlen(stream))
        except Exception:
            return 0

    def redis_id_age_seconds(self, redis_id: Optional[str]) -> Optional[float]:
        if redis_id is None:
            return None
        try:
            millis = int(redis_id.split("-")[0])
            return round(time.time() - millis / 1000.0, 2)
        except Exception:
            return None

    def unwrap_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "event" in payload:
            try:
                event = json.loads(payload["event"])
                if isinstance(event, dict):
                    return event
            except Exception:
                return payload
        return payload

    def extract_ticker(self, payload: Dict[str, Any]) -> str:
        for key in ["ticker", "symbol", "asset"]:
            if key in payload:
                return str(payload[key])
        return "UNKNOWN"

    def extract_price(self, payload: Dict[str, Any]) -> Optional[float]:
        for key in ["price", "close", "last_price", "value"]:
            if key in payload:
                try:
                    return float(payload[key])
                except Exception:
                    return None
        return None

    def load_current_regime(self) -> str:
        for path in REGIME_SUMMARY_CANDIDATES:
            if not path.exists():
                continue

            try:
                import pandas as pd

                df = pd.read_csv(path)

                for col in [
                    "regime",
                    "current_regime",
                    "predicted_regime",
                    "forecast_regime",
                    "latest_regime",
                ]:
                    if col in df.columns and not df.empty:
                        return str(df[col].iloc[-1])

            except Exception:
                continue

        return "unknown"

    def classify_volatility_state(self, latest_feature: Dict[str, Any]) -> str:
        numeric_values = []

        for _, value in latest_feature.items():
            try:
                numeric_values.append(abs(float(value)))
            except Exception:
                continue

        if not numeric_values:
            return "unknown"

        max_abs = max(numeric_values)

        if max_abs >= 0.05:
            return "high"
        if max_abs >= 0.02:
            return "moderate"
        return "low"

    def classify_liquidity_state(self, tick_age: Optional[float]) -> str:
        if tick_age is None:
            return "unknown"
        if tick_age > 30:
            return "stale"
        if tick_age > 10:
            return "watch"
        return "healthy"

    def classify_alert_state(
        self,
        alert_age: Optional[float],
        alert_stream_length: int,
    ) -> str:
        if alert_stream_length == 0:
            return "quiet"
        if alert_age is None:
            return "unknown"
        if alert_age <= 60:
            return "active_alerting"
        if alert_age <= 300:
            return "recent_alerting"
        return "quiet"

    def compute_stress_score(
        self,
        tick_age: Optional[float],
        feature_age: Optional[float],
        alert_age: Optional[float],
        volatility_state: str,
        liquidity_state: str,
        alert_state: str,
    ) -> float:
        score = 0.0

        if volatility_state == "moderate":
            score += 0.20
        elif volatility_state == "high":
            score += 0.40
        elif volatility_state == "unknown":
            score += 0.10

        if liquidity_state == "watch":
            score += 0.20
        elif liquidity_state == "stale":
            score += 0.40
        elif liquidity_state == "unknown":
            score += 0.10

        if alert_state == "recent_alerting":
            score += 0.15
        elif alert_state == "active_alerting":
            score += 0.30
        elif alert_state == "unknown":
            score += 0.10

        if feature_age is not None and feature_age > 30:
            score += 0.20

        if tick_age is not None and tick_age > 30:
            score += 0.20

        return round(min(score, 1.0), 4)

    def classify_state_label(self, stress_score: float) -> str:
        if stress_score >= 0.75:
            return "critical"
        if stress_score >= 0.50:
            return "stressed"
        if stress_score >= 0.25:
            return "watch"
        return "normal"

    def publish_state(self, state: LiveDigitalTwinState) -> str:
        data = asdict(state)
        data.pop("redis_event_id", None)

        payload = {
            key: json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value)
            for key, value in data.items()
            if value is not None
        }

        return self.redis_client.xadd(STREAM_SIGNALS, payload)

    def run_once(self) -> LiveDigitalTwinState:
        tick_id, tick_payload_raw = self.latest_entry(STREAM_TICKS)
        feature_id, feature_payload_raw = self.latest_entry(STREAM_FEATURES)
        alert_id, _ = self.latest_entry(STREAM_ALERTS)

        tick_payload = self.unwrap_payload(tick_payload_raw)
        feature_payload = self.unwrap_payload(feature_payload_raw)

        tick_age = self.redis_id_age_seconds(tick_id)
        feature_age = self.redis_id_age_seconds(feature_id)
        alert_age = self.redis_id_age_seconds(alert_id)

        tick_len = self.stream_length(STREAM_TICKS)
        feature_len = self.stream_length(STREAM_FEATURES)
        alert_len = self.stream_length(STREAM_ALERTS)

        ticker = self.extract_ticker(tick_payload)
        price = self.extract_price(tick_payload)

        current_regime = self.load_current_regime()

        volatility_state = self.classify_volatility_state(feature_payload)
        liquidity_state = self.classify_liquidity_state(tick_age)
        alert_state = self.classify_alert_state(alert_age, alert_len)

        stress_score = self.compute_stress_score(
            tick_age=tick_age,
            feature_age=feature_age,
            alert_age=alert_age,
            volatility_state=volatility_state,
            liquidity_state=liquidity_state,
            alert_state=alert_state,
        )

        state_label = self.classify_state_label(stress_score)

        state = LiveDigitalTwinState(
            event_type="live_digital_twin_state",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            latest_ticker=ticker,
            latest_price=price,
            tick_age_seconds=tick_age,
            feature_age_seconds=feature_age,
            alert_age_seconds=alert_age,
            tick_stream_length=tick_len,
            feature_stream_length=feature_len,
            alert_stream_length=alert_len,
            current_regime=current_regime,
            volatility_state=volatility_state,
            liquidity_state=liquidity_state,
            alert_state=alert_state,
            market_stress_score=stress_score,
            state_label=state_label,
        )

        redis_event_id = self.publish_state(state)
        state.redis_event_id = redis_event_id

        self.write_outputs(state)
        return state

    def write_outputs(self, state: LiveDigitalTwinState) -> None:
        data = asdict(state)

        LIVE_STATE_PATH.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        lines = [
            "=" * 80,
            "AURUM LIVE DIGITAL TWIN STATE",
            "=" * 80,
            f"Timestamp UTC: {state.timestamp_utc}",
            f"Redis Event ID: {state.redis_event_id}",
            f"Latest Ticker: {state.latest_ticker}",
            f"Latest Price: {state.latest_price}",
            f"Current Regime: {state.current_regime}",
            "-" * 80,
            f"Tick Age Seconds: {state.tick_age_seconds}",
            f"Feature Age Seconds: {state.feature_age_seconds}",
            f"Alert Age Seconds: {state.alert_age_seconds}",
            f"Tick Stream Length: {state.tick_stream_length}",
            f"Feature Stream Length: {state.feature_stream_length}",
            f"Alert Stream Length: {state.alert_stream_length}",
            "-" * 80,
            f"Volatility State: {state.volatility_state}",
            f"Liquidity State: {state.liquidity_state}",
            f"Alert State: {state.alert_state}",
            f"Market Stress Score: {state.market_stress_score}",
            f"State Label: {state.state_label}",
        ]

        LIVE_STATE_TXT_PATH.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    def print_state(self, state: LiveDigitalTwinState) -> None:
        print("=" * 80)
        print("AURUM LIVE DIGITAL TWIN STATE")
        print("=" * 80)
        print(f"Latest Ticker: {state.latest_ticker}")
        print(f"Latest Price: {state.latest_price}")
        print(f"Current Regime: {state.current_regime}")
        print(f"Volatility State: {state.volatility_state}")
        print(f"Liquidity State: {state.liquidity_state}")
        print(f"Alert State: {state.alert_state}")
        print(f"Market Stress Score: {state.market_stress_score}")
        print(f"State Label: {state.state_label}")
        print(f"Redis Event ID: {state.redis_event_id}")

    def run_forever(self, interval_seconds: int = 10) -> None:
        while True:
            state = self.run_once()
            self.print_state(state)
            time.sleep(interval_seconds)


def main() -> None:
    engine = LiveDigitalTwinStateEngine()
    state = engine.run_once()
    engine.print_state(state)


if __name__ == "__main__":
    main()