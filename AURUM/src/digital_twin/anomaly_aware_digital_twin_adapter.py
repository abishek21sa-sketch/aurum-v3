from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from src.intelligence.institutional_anomaly_signal_generator import InstitutionalAnomalySignal


from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()


@dataclass
class AnomalyAwareDigitalTwinState:
    base_stress_score: float
    anomaly_score: float
    anomaly_severity: str
    anomaly_stress_addon: float
    adjusted_stress_score: float
    state_label: str
    integration_status: str


class AnomalyAwareDigitalTwinAdapter:
    """
    Adds institutional anomaly pressure into digital twin stress.
    """

    def __init__(self, anomaly_weight: float = 0.20):
        self.anomaly_weight = anomaly_weight

    def update_state(
        self,
        base_stress_score: float,
        anomaly_signal: InstitutionalAnomalySignal,
    ) -> AnomalyAwareDigitalTwinState:
        addon = float(anomaly_signal.score) * self.anomaly_weight
        adjusted = min(1.0, max(0.0, base_stress_score + addon))

        state = AnomalyAwareDigitalTwinState(
            base_stress_score=float(base_stress_score),
            anomaly_score=float(anomaly_signal.score),
            anomaly_severity=anomaly_signal.severity,
            anomaly_stress_addon=float(addon),
            adjusted_stress_score=float(adjusted),
            state_label=self._label(adjusted),
            integration_status="digital_twin_receives_anomaly_signal",
        )

        path = artifact_path("sprint1b", "anomaly_aware_digital_twin_state.json")
        path.write_text(json.dumps(asdict(state), indent=4), encoding="utf-8")

        return state

    @staticmethod
    def _label(score: float) -> str:
        if score >= 0.80:
            return "critical"
        if score >= 0.60:
            return "stressed"
        if score >= 0.35:
            return "watch"
        return "normal"