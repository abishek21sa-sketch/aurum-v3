from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from src.intelligence.institutional_anomaly_detector import InstitutionalAnomalyDetector


from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()

@dataclass
class InstitutionalAnomalySignal:
    event_type: str
    timestamp: str
    severity: str
    score: float
    is_anomaly: bool
    rolling_z_score: float
    isolation_score: float
    source: str
    redis_stream: str
    publish_status: str


class InstitutionalAnomalySignalGenerator:
    """
    Converts anomaly detector output into a market_signals-compatible event.

    Redis publishing is optional.
    If Redis is unavailable, it still saves the signal artifact.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url

    def generate(self, returns: pd.Series, publish_to_redis: bool = True) -> InstitutionalAnomalySignal:
        detector = InstitutionalAnomalyDetector(
            rolling_window=60,
            z_threshold=2.5,
            contamination=0.03,
        )

        detected = detector.detect(returns)
        summary = detector.summarize(detected)

        signal = InstitutionalAnomalySignal(
            event_type="institutional_anomaly",
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=summary.latest_severity,
            score=float(summary.latest_combined_score),
            is_anomaly=bool(summary.latest_is_anomaly),
            rolling_z_score=float(summary.latest_rolling_z_score),
            isolation_score=float(summary.latest_isolation_score),
            source="rolling_z_score + isolation_forest",
            redis_stream="market_signals",
            publish_status="not_attempted",
        )

        if publish_to_redis:
            signal.publish_status = self._publish(signal)

        self._save(signal)
        return signal

    def _publish(self, signal: InstitutionalAnomalySignal) -> str:
        try:
            import redis

            client = redis.Redis.from_url(self.redis_url, decode_responses=True)

            payload = {
                "event_type": signal.event_type,
                "timestamp": signal.timestamp,
                "severity": signal.severity,
                "score": str(signal.score),
                "is_anomaly": str(signal.is_anomaly),
                "rolling_z_score": str(signal.rolling_z_score),
                "isolation_score": str(signal.isolation_score),
                "source": signal.source,
            }

            client.xadd("market_signals", payload, maxlen=10000, approximate=True)
            return "published"

        except Exception as exc:
            return f"redis_unavailable_saved_locally: {exc}"

    @staticmethod
    def _save(signal: InstitutionalAnomalySignal) -> None:
        path = artifact_path("sprint1b", "institutional_anomaly_signal.json")
        path.write_text(json.dumps(asdict(signal), indent=4), encoding="utf-8")