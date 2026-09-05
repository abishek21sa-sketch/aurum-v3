"""
AURUM HMM Regime Engine Cleanup

Correct terminology:

Filtered probability:
    P(state_t | observations_1:t)
    Valid for live use.

Smoothed probability:
    P(state_t | observations_1:T)
    Uses future data.
    Valid only for retrospective analysis.

Posterior probability:
    Generic term. Avoid using it loosely in dashboard/live claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
try:
    from hmmlearn.hmm import GaussianHMM
except (ImportError, ModuleNotFoundError):  # Python 3.14 fallback
    from src.regimes.gaussian_hmm_compat import GaussianHMMCompat as GaussianHMM
from sklearn.preprocessing import StandardScaler


from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()

@dataclass
class HMMRegimeResult:
    current_regime: int
    current_filtered_probabilities: Dict[str, float]
    current_smoothed_probabilities: Dict[str, float]
    transition_matrix: List[List[float]]
    expected_durations: Dict[str, float]
    regime_counts: Dict[str, int]
    live_probability_type: str
    warning: str


class CleanHMMRegimeEngine:
    def __init__(self, n_states: int = 3, random_state: int = 42):
        self.n_states = n_states
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = GaussianHMM(
            n_components=n_states,
            covariance_type="full",
            n_iter=500,
            random_state=random_state,
        )

    def fit(self, features: pd.DataFrame) -> HMMRegimeResult:
        if features.empty:
            raise ValueError("Feature DataFrame is empty.")

        clean_features = features.dropna()
        x = self.scaler.fit_transform(clean_features.values)

        self.model.fit(x)

        smoothed_probs = self.model.predict_proba(x)
        hidden_states = self.model.predict(x)

        filtered_probs = self._compute_filtered_probabilities(x)

        current_filtered = filtered_probs[-1]
        current_smoothed = smoothed_probs[-1]
        current_regime = int(np.argmax(current_filtered))

        transition = self.model.transmat_

        expected_durations = {}
        for i in range(self.n_states):
            stay_prob = transition[i, i]
            duration = 1.0 / (1.0 - stay_prob) if stay_prob < 1 else np.inf
            expected_durations[f"state_{i}"] = float(duration)

        regime_counts = {
            f"state_{i}": int(np.sum(hidden_states == i)) for i in range(self.n_states)
        }

        result = HMMRegimeResult(
            current_regime=current_regime,
            current_filtered_probabilities={
                f"state_{i}": float(current_filtered[i]) for i in range(self.n_states)
            },
            current_smoothed_probabilities={
                f"state_{i}": float(current_smoothed[i]) for i in range(self.n_states)
            },
            transition_matrix=transition.tolist(),
            expected_durations=expected_durations,
            regime_counts=regime_counts,
            live_probability_type="filtered",
            warning=(
                "Use filtered probabilities for live decisions. "
                "Smoothed probabilities use full-sample hindsight and should only be used retrospectively."
            ),
        )

        self.save_result(result)
        return result

    def _compute_filtered_probabilities(self, x: np.ndarray) -> np.ndarray:
        """
        Forward-filtering approximation.

        hmmlearn exposes predict_proba as smoothed probabilities.
        For live-safe probabilities, this function performs the forward pass:
            P(z_t | x_1:t)
        """

        log_startprob = np.log(self.model.startprob_ + 1e-12)
        log_transmat = np.log(self.model.transmat_ + 1e-12)

        framelogprob = self.model._compute_log_likelihood(x)

        n_obs = x.shape[0]
        n_states = self.n_states

        log_alpha = np.zeros((n_obs, n_states))
        log_alpha[0] = log_startprob + framelogprob[0]
        log_alpha[0] -= self._logsumexp(log_alpha[0])

        for t in range(1, n_obs):
            for j in range(n_states):
                log_alpha[t, j] = (
                    framelogprob[t, j]
                    + self._logsumexp(log_alpha[t - 1] + log_transmat[:, j])
                )
            log_alpha[t] -= self._logsumexp(log_alpha[t])

        return np.exp(log_alpha)

    @staticmethod
    def _logsumexp(values: np.ndarray) -> float:
        max_val = np.max(values)
        return float(max_val + np.log(np.sum(np.exp(values - max_val))))

    @staticmethod
    def save_result(result: HMMRegimeResult) -> None:
        output_path = artifact_path("regime", "hmm_regime_engine_clean_result.json")
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=4)


def load_sample_features() -> pd.DataFrame:
    np.random.seed(42)

    n = 750

    regime_1 = np.random.normal([0.0004, 0.01, 15], [0.005, 0.002, 2], size=(350, 3))
    regime_2 = np.random.normal([-0.0002, 0.018, 24], [0.010, 0.004, 4], size=(250, 3))
    regime_3 = np.random.normal([-0.0010, 0.035, 38], [0.020, 0.008, 7], size=(150, 3))

    x = np.vstack([regime_1, regime_2, regime_3])

    return pd.DataFrame(
        x,
        columns=["market_return", "rolling_volatility", "vix_level"],
    )


def main() -> None:
    features = load_sample_features()

    engine = CleanHMMRegimeEngine(n_states=3)
    result = engine.fit(features)

    print("=" * 80)
    print("AURUM CLEAN HMM REGIME ENGINE")
    print("=" * 80)
    print(f"Current Regime:          state_{result.current_regime}")
    print(f"Live Probability Type:   {result.live_probability_type}")
    print("-" * 80)
    print("Filtered Probabilities")
    for state, prob in result.current_filtered_probabilities.items():
        print(f"{state:<10} {prob:.4f}")
    print("-" * 80)
    print("Smoothed Probabilities")
    for state, prob in result.current_smoothed_probabilities.items():
        print(f"{state:<10} {prob:.4f}")
    print("-" * 80)
    print(result.warning)
    print("=" * 80)


if __name__ == "__main__":
    main()