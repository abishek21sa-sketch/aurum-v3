# src/realtime/streaming_feature_engine.py

from __future__ import annotations

import argparse
import math
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

import numpy as np

from src.realtime.event_bus import RedisEventBus, EVENT_STREAMS


class StreamingFeatureEngine:
    """
    Consumes live market ticks from Redis Stream: market_ticks
    Produces live market features into Redis Stream: market_features
    """

    def __init__(
        self,
        event_bus: RedisEventBus,
        input_stream: str = EVENT_STREAMS["market_ticks"],
        output_stream: str = EVENT_STREAMS["market_features"],
        max_history: int = 300,
        block_ms: int = 5000,
    ) -> None:
        self.event_bus = event_bus
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.max_history = max_history
        self.block_ms = block_ms

        self.last_id = "$"

        self.price_history: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self.volume_history: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self.timestamp_history: Dict[str, Deque[str]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    @staticmethod
    def safe_divide(numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return numerator / denominator

    @staticmethod
    def clean_number(value: float) -> float:
        if value is None:
            return 0.0
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return round(float(value), 8)

    def update_memory(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ticker = tick.get("ticker")
        price = self.safe_float(tick.get("price"))
        volume = self.safe_float(tick.get("volume"))
        timestamp = tick.get("timestamp", self.utc_now())

        if not ticker or price <= 0:
            return None

        self.price_history[ticker].append(price)
        self.volume_history[ticker].append(volume)
        self.timestamp_history[ticker].append(timestamp)

        return {
            "ticker": ticker,
            "price": price,
            "volume": volume,
            "timestamp": timestamp,
            "source": tick.get("source", "unknown"),
        }

    def compute_return(self, prices: List[float], lookback: int) -> float:
        if len(prices) <= lookback:
            return 0.0

        current = prices[-1]
        previous = prices[-lookback]

        return self.safe_divide(current, previous) - 1.0

    def compute_volatility(self, prices: List[float]) -> float:
        if len(prices) < 3:
            return 0.0

        returns = np.diff(prices) / prices[:-1]

        if len(returns) == 0:
            return 0.0

        return float(np.std(returns))

    def compute_momentum(self, prices: List[float], lookback: int = 30) -> float:
        if len(prices) < 2:
            return 0.0

        recent_prices = prices[-lookback:] if len(prices) >= lookback else prices
        recent_mean = float(np.mean(recent_prices))

        if recent_mean == 0:
            return 0.0

        return self.safe_divide(prices[-1], recent_mean) - 1.0

    def compute_volume_zscore(self, volumes: List[float]) -> float:
        if len(volumes) < 10:
            return 0.0

        current_volume = volumes[-1]
        mean_volume = float(np.mean(volumes))
        std_volume = float(np.std(volumes))

        if std_volume == 0:
            return 0.0

        return (current_volume - mean_volume) / std_volume

    @staticmethod
    def classify_liquidity(volume_zscore: float) -> str:
        if volume_zscore <= -1.5:
            return "weak"
        if volume_zscore >= 1.5:
            return "strong"
        return "normal"

    @staticmethod
    def classify_volatility(volatility: float) -> str:
        if volatility >= 0.003:
            return "high"
        if volatility >= 0.001:
            return "elevated"
        return "normal"

    def compute_features(self, normalized_tick: Dict[str, Any]) -> Dict[str, Any]:
        ticker = normalized_tick["ticker"]

        prices = list(self.price_history[ticker])
        volumes = list(self.volume_history[ticker])

        return_1m = self.compute_return(prices, lookback=60)
        return_5m = self.compute_return(prices, lookback=300)
        volatility = self.compute_volatility(prices)
        momentum = self.compute_momentum(prices, lookback=30)
        volume_zscore = self.compute_volume_zscore(volumes)

        liquidity_state = self.classify_liquidity(volume_zscore)
        volatility_state = self.classify_volatility(volatility)

        return {
            "event_type": "feature",
            "ticker": ticker,
            "source": normalized_tick.get("source", "unknown"),
            "price": self.clean_number(normalized_tick["price"]),
            "volume": self.clean_number(normalized_tick["volume"]),
            "return_1m": self.clean_number(return_1m),
            "return_5m": self.clean_number(return_5m),
            "rolling_volatility": self.clean_number(volatility),
            "momentum": self.clean_number(momentum),
            "volume_zscore": self.clean_number(volume_zscore),
            "liquidity_state": liquidity_state,
            "volatility_state": volatility_state,
            "history_size": len(prices),
            "timestamp": normalized_tick["timestamp"],
            "computed_at": self.utc_now(),
        }

    def process_tick(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        normalized_tick = self.update_memory(tick)

        if normalized_tick is None:
            return None

        features = self.compute_features(normalized_tick)
        self.event_bus.publish(self.output_stream, features)

        return features

    def run_forever(self) -> None:
        print("=" * 80)
        print("AURUM STREAMING FEATURE ENGINE")
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

                features = self.process_tick(event)

                if features:
                    print(
                        f"[FEATURE] {features['ticker']} | "
                        f"price={features['price']} | "
                        f"ret_1m={features['return_1m']} | "
                        f"vol={features['rolling_volatility']} | "
                        f"mom={features['momentum']} | "
                        f"vol_z={features['volume_zscore']} | "
                        f"liq={features['liquidity_state']} | "
                        f"vol_state={features['volatility_state']}"
                    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run AURUM streaming feature engine."
    )
    parser.add_argument("--block-ms", type=int, default=5000)
    parser.add_argument("--max-history", type=int, default=300)

    args = parser.parse_args()

    bus = RedisEventBus()

    engine = StreamingFeatureEngine(
        event_bus=bus,
        max_history=args.max_history,
        block_ms=args.block_ms,
    )

    engine.run_forever()


if __name__ == "__main__":
    main()