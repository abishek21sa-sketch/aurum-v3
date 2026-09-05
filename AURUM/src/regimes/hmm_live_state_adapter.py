from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

import pandas as pd

from src.regimes.hmm_regime_engine_clean import CleanHMMRegimeEngine


from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()


@dataclass
class HMMLiveState:
    current_regime: int
    probability_type: str
    probabilities: Dict[str, float]
    live_safe: bool
    warning: str


class HMMLiveStateAdapter:
    """
    Live adapter.

    Important:
    Uses filtered probabilities only.
    Does not expose smoothed probabilities to live decision systems.
    """

    def run(self, features: pd.DataFrame) -> HMMLiveState:
        engine = CleanHMMRegimeEngine(n_states=3)
        result = engine.fit(features)

        live_state = HMMLiveState(
            current_regime=result.current_regime,
            probability_type="filtered",
            probabilities=result.current_filtered_probabilities,
            live_safe=True,
            warning="Live state uses filtered probabilities only. No smoothed hindsight probabilities used.",
        )

        path = artifact_path("sprint1b", "hmm_live_state_adapter_result.json")
        path.write_text(json.dumps(asdict(live_state), indent=4), encoding="utf-8")

        return live_state