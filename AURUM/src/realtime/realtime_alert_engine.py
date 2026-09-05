# src/realtime/realtime_alert_engine.py

from __future__ import annotations

import argparse
import hashlib
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS


class RealtimeAlertEngine:
    """
    Consumes:
        Redis Stream: market_features

    Produces:
        Redis Stream: alerts

    Detects:
        - VIX spike
        - volatility expansion
        - volume anomaly
        - liquidity weakness
        - momentum shock
        - large 1m move
        - stale/invalid feature values
    """

    def __init__(
        self,
        event_bus: RedisEventBus,
        input_stream: str = EVENT_STREAMS["market_features"],
        output_stream: str = EVENT_STREAMS["alerts"],
        block_ms: int = 5000,
    ) -> None:
        self.event_bus = event_bus
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.block_ms = block_ms
        self.last_id = "$"

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        try:
            number = float(value)
            if math.isnan(number) or math.isinf(number):
                return default
            return number
        except Exception:
            return default

    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(float(value))
        except Exception:
            return default

    @staticmethod
    def clean_number(value: float) -> float:
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return round(float(value), 8)

    @staticmethod
    def make_alert_id(alert_type: str, ticker: str, timestamp: str) -> str:
        raw = f"{alert_type}|{ticker}|{timestamp}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def severity_rank(severity: str) -> int:
        ranks = {
            "info": 1,
            "low": 2,
            "medium": 3,
            "high": 4,
            "critical": 5,
        }
        return ranks.get(severity, 1)

    def build_alert(
        self,
        alert_type: str,
        ticker: str,
        severity: str,
        message: str,
        feature: Dict[str, Any],
        metric_name: str,
        metric_value: float,
        threshold: float,
    ) -> Dict[str, Any]:
        timestamp = feature.get("timestamp", self.utc_now())

        return {
            "event_type": "alert",
            "alert_id": self.make_alert_id(alert_type, ticker, timestamp),
            "alert_type": alert_type,
            "ticker": ticker,
            "severity": severity,
            "severity_rank": self.severity_rank(severity),
            "message": message,
            "metric_name": metric_name,
            "metric_value": self.clean_number(metric_value),
            "threshold": self.clean_number(threshold),
            "price": self.safe_float(feature.get("price")),
            "source_event_timestamp": timestamp,
            "computed_at": feature.get("computed_at", ""),
            "alerted_at": self.utc_now(),
        }

    def evaluate_feature(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        ticker = str(feature.get("ticker", "")).upper().strip()

        if not ticker:
            return []

        price = self.safe_float(feature.get("price"))
        return_1m = self.safe_float(feature.get("return_1m"))
        return_5m = self.safe_float(feature.get("return_5m"))
        rolling_volatility = self.safe_float(feature.get("rolling_volatility"))
        momentum = self.safe_float(feature.get("momentum"))
        volume_zscore = self.safe_float(feature.get("volume_zscore"))
        history_size = self.safe_int(feature.get("history_size"))
        liquidity_state = str(feature.get("liquidity_state", "normal")).lower()
        volatility_state = str(feature.get("volatility_state", "normal")).lower()

        alerts: List[Dict[str, Any]] = []

        if price <= 0:
            alerts.append(
                self.build_alert(
                    alert_type="invalid_price",
                    ticker=ticker,
                    severity="high",
                    message=f"{ticker} has invalid non-positive price.",
                    feature=feature,
                    metric_name="price",
                    metric_value=price,
                    threshold=0.0,
                )
            )

        if history_size < 10:
            alerts.append(
                self.build_alert(
                    alert_type="insufficient_history",
                    ticker=ticker,
                    severity="info",
                    message=f"{ticker} has limited streaming history; feature confidence is low.",
                    feature=feature,
                    metric_name="history_size",
                    metric_value=float(history_size),
                    threshold=10.0,
                )
            )

        # VIX-specific spike logic
        if ticker in {"VIX", "^VIX"}:
            if return_1m >= 0.01:
                alerts.append(
                    self.build_alert(
                        alert_type="vix_spike",
                        ticker=ticker,
                        severity="critical",
                        message=f"VIX spike detected: 1m return {return_1m:.4%}.",
                        feature=feature,
                        metric_name="return_1m",
                        metric_value=return_1m,
                        threshold=0.01,
                    )
                )

            elif return_1m >= 0.005:
                alerts.append(
                    self.build_alert(
                        alert_type="vix_rising",
                        ticker=ticker,
                        severity="high",
                        message=f"VIX rising quickly: 1m return {return_1m:.4%}.",
                        feature=feature,
                        metric_name="return_1m",
                        metric_value=return_1m,
                        threshold=0.005,
                    )
                )

        # Large short-horizon move
        if abs(return_1m) >= 0.01:
            alerts.append(
                self.build_alert(
                    alert_type="large_1m_move",
                    ticker=ticker,
                    severity="high",
                    message=f"{ticker} large 1m move detected: {return_1m:.4%}.",
                    feature=feature,
                    metric_name="return_1m",
                    metric_value=return_1m,
                    threshold=0.01,
                )
            )

        elif abs(return_1m) >= 0.005:
            alerts.append(
                self.build_alert(
                    alert_type="notable_1m_move",
                    ticker=ticker,
                    severity="medium",
                    message=f"{ticker} notable 1m move detected: {return_1m:.4%}.",
                    feature=feature,
                    metric_name="return_1m",
                    metric_value=return_1m,
                    threshold=0.005,
                )
            )

        # 5m move, useful once enough history exists
        if abs(return_5m) >= 0.025:
            alerts.append(
                self.build_alert(
                    alert_type="large_5m_move",
                    ticker=ticker,
                    severity="high",
                    message=f"{ticker} large 5m move detected: {return_5m:.4%}.",
                    feature=feature,
                    metric_name="return_5m",
                    metric_value=return_5m,
                    threshold=0.025,
                )
            )

        # Volatility expansion
        if rolling_volatility >= 0.003:
            alerts.append(
                self.build_alert(
                    alert_type="volatility_expansion",
                    ticker=ticker,
                    severity="high",
                    message=f"{ticker} volatility expansion detected.",
                    feature=feature,
                    metric_name="rolling_volatility",
                    metric_value=rolling_volatility,
                    threshold=0.003,
                )
            )

        elif volatility_state == "elevated":
            alerts.append(
                self.build_alert(
                    alert_type="elevated_volatility",
                    ticker=ticker,
                    severity="medium",
                    message=f"{ticker} volatility state is elevated.",
                    feature=feature,
                    metric_name="rolling_volatility",
                    metric_value=rolling_volatility,
                    threshold=0.001,
                )
            )

        # Volume anomaly
        if abs(volume_zscore) >= 3.0:
            alerts.append(
                self.build_alert(
                    alert_type="extreme_volume_anomaly",
                    ticker=ticker,
                    severity="high",
                    message=f"{ticker} extreme volume anomaly detected: z={volume_zscore:.2f}.",
                    feature=feature,
                    metric_name="volume_zscore",
                    metric_value=volume_zscore,
                    threshold=3.0,
                )
            )

        elif abs(volume_zscore) >= 2.0:
            alerts.append(
                self.build_alert(
                    alert_type="volume_anomaly",
                    ticker=ticker,
                    severity="medium",
                    message=f"{ticker} volume anomaly detected: z={volume_zscore:.2f}.",
                    feature=feature,
                    metric_name="volume_zscore",
                    metric_value=volume_zscore,
                    threshold=2.0,
                )
            )

        # Liquidity weakness
        if liquidity_state == "weak":
            alerts.append(
                self.build_alert(
                    alert_type="liquidity_weakness",
                    ticker=ticker,
                    severity="medium",
                    message=f"{ticker} liquidity weakness detected.",
                    feature=feature,
                    metric_name="volume_zscore",
                    metric_value=volume_zscore,
                    threshold=-1.5,
                )
            )

        # Momentum shock
        if abs(momentum) >= 0.01:
            alerts.append(
                self.build_alert(
                    alert_type="momentum_shock",
                    ticker=ticker,
                    severity="medium",
                    message=f"{ticker} momentum shock detected: {momentum:.4%}.",
                    feature=feature,
                    metric_name="momentum",
                    metric_value=momentum,
                    threshold=0.01,
                )
            )

        return alerts

    def process_feature(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts = self.evaluate_feature(feature)

        for alert in alerts:
            self.event_bus.publish(self.output_stream, alert)

        return alerts

    def run_forever(self) -> None:
        print("=" * 80)
        print("AURUM REAL-TIME ALERT ENGINE")
        print("=" * 80)
        print(f"Input stream:  {self.input_stream}")
        print(f"Output stream: {self.output_stream}")
        print("=" * 80)

        while True:
            events = self.event_bus.read_from(
                stream_name=self.input_stream,
                last_id=self.last_id,
                block_ms=self.block_ms,
                count=100,
            )

            if not events:
                continue

            for event in events:
                self.last_id = event["redis_id"]

                alerts = self.process_feature(event)

                for alert in alerts:
                    print(
                        f"[ALERT] {alert['severity'].upper()} | "
                        f"{alert['ticker']} | "
                        f"{alert['alert_type']} | "
                        f"{alert['message']}"
                    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run AURUM real-time alert engine."
    )
    parser.add_argument("--block-ms", type=int, default=5000)

    args = parser.parse_args()

    bus = RedisEventBus()
    engine = RealtimeAlertEngine(
        event_bus=bus,
        block_ms=args.block_ms,
    )
    engine.run_forever()


if __name__ == "__main__":
    main()