from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

from src.digital_twin.anomaly_aware_digital_twin_adapter import AnomalyAwareDigitalTwinState
from src.intelligence.institutional_anomaly_signal_generator import InstitutionalAnomalySignal

from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()


@dataclass
class QuantCoreCIOBriefing:
    briefing_type: str
    cvar_engine: str
    cvar_method: str
    hmm_probability_type: str
    anomaly_severity: str
    anomaly_score: float
    adjusted_stress_score: float
    digital_twin_state: str
    execution_posture: str
    notes: Dict[str, str]


class QuantCoreCIOBriefingAdapter:
    def generate(
        self,
        cvar_engine: str,
        cvar_method: str,
        hmm_probability_type: str,
        anomaly_signal: InstitutionalAnomalySignal,
        digital_twin_state: AnomalyAwareDigitalTwinState,
    ) -> QuantCoreCIOBriefing:
        posture = self._posture(digital_twin_state.adjusted_stress_score)

        briefing = QuantCoreCIOBriefing(
            briefing_type="sprint1b_quant_core_integration",
            cvar_engine=cvar_engine,
            cvar_method=cvar_method,
            hmm_probability_type=hmm_probability_type,
            anomaly_severity=anomaly_signal.severity,
            anomaly_score=float(anomaly_signal.score),
            adjusted_stress_score=float(digital_twin_state.adjusted_stress_score),
            digital_twin_state=digital_twin_state.state_label,
            execution_posture=posture,
            notes={
                "cvar": "CIO briefing now references cvxpy Rockafellar-Uryasev LP CVaR engine.",
                "hmm": "Live regime probability type is filtered, not smoothed.",
                "anomaly": "Anomaly signal comes from rolling z-score plus Isolation Forest.",
            },
        )

        path = artifact_path("sprint1b", "quant_core_cio_briefing.json")
        path.write_text(json.dumps(asdict(briefing), indent=4), encoding="utf-8")

        return briefing

    @staticmethod
    def _posture(stress_score: float) -> str:
        if stress_score >= 0.80:
            return "block_or_reduce_risk"
        if stress_score >= 0.60:
            return "reduce_risk"
        if stress_score >= 0.35:
            return "watch"
        return "normal"