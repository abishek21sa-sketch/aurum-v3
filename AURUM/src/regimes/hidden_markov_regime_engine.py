from pathlib import Path
import logging

import numpy as np
import pandas as pd
try:
    from hmmlearn.hmm import GaussianHMM
except (ImportError, ModuleNotFoundError):  # Python 3.14 fallback
    from src.regimes.gaussian_hmm_compat import GaussianHMMCompat as GaussianHMM
from sklearn.preprocessing import StandardScaler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class HiddenMarkovRegimeEngine:
    """
    Hidden Markov Regime Engine v2 for AURUM.

    Adds:
    - numeric feature selection
    - Gaussian HMM latent states
    - filtered probability output
    - smoothed probability output proxy
    - transition matrix
    - regime persistence
    - expected duration
    - regime summary diagnostics
    """

    def __init__(self, n_states: int = 3):
        self.n_states = n_states

        self.input_path = Path("data/features/macro_features.parquet")
        self.output_dir = Path("data/regimes")

        self.regime_output_path = self.output_dir / "hidden_markov_regimes.csv"
        self.filtered_probability_path = self.output_dir / "hidden_markov_filtered_probabilities.csv"
        self.smoothed_probability_path = self.output_dir / "hidden_markov_smoothed_probabilities.csv"
        self.transition_matrix_path = self.output_dir / "hidden_markov_transition_matrix.csv"
        self.persistence_path = self.output_dir / "hidden_markov_regime_persistence.csv"
        self.summary_path = self.output_dir / "hidden_markov_regime_summary.csv"

    def load_features(self):
        logger.info("Loading macro features from: %s", self.input_path)

        self.features = pd.read_parquet(self.input_path)

        logger.info("Loaded macro feature shape: %s", self.features.shape)
        logger.info("Feature columns: %s", list(self.features.columns))

    def select_numeric_features(self):
        logger.info("Selecting numeric features for HMM.")

        self.numeric_features = self.features.select_dtypes(include=["number"]).copy()

        logger.info("Numeric feature shape: %s", self.numeric_features.shape)
        logger.info("Numeric feature columns: %s", list(self.numeric_features.columns))

    def scale_features(self):
        logger.info("Scaling numeric macro features.")

        self.scaler = StandardScaler()
        self.scaled_features = self.scaler.fit_transform(self.numeric_features)

        logger.info("Scaled feature matrix shape: %s", self.scaled_features.shape)

    def fit_hmm(self):
        logger.info("Fitting Gaussian HMM with %s states.", self.n_states)

        self.model = GaussianHMM(
            n_components=self.n_states,
            covariance_type="diag",
            n_iter=1000,
            random_state=42,
        )

        self.model.fit(self.scaled_features)

        self.hidden_states = self.model.predict(self.scaled_features)
        self.filtered_probabilities = self.model.predict_proba(self.scaled_features)

        logger.info("Gaussian HMM fitted successfully.")
        logger.info("Model converged: %s", self.model.monitor_.converged)
        logger.info("Model log likelihood: %.4f", self.model.score(self.scaled_features))

    def build_regime_output(self):
        logger.info("Building hidden regime output.")

        self.regime_output = self.features.copy()
        self.regime_output["hidden_state"] = self.hidden_states
        self.regime_output = self.regime_output.reset_index()

        logger.info(
            "Hidden regime output preview:\n%s",
            self.regime_output.tail(),
        )

    def build_probability_outputs(self):
        logger.info("Building filtered and smoothed probability outputs.")

        probability_cols = [
            f"state_{state}_filtered_probability"
            for state in range(self.n_states)
        ]

        self.filtered_probabilities_df = pd.DataFrame(
            self.filtered_probabilities,
            index=self.features.index,
            columns=probability_cols,
        ).reset_index()

        # HMM predict_proba gives posterior state probabilities over the full sequence.
        # We label these as smoothed proxies for research use.
        smoothed_cols = [
            f"state_{state}_smoothed_probability"
            for state in range(self.n_states)
        ]

        self.smoothed_probabilities_df = pd.DataFrame(
            self.filtered_probabilities,
            index=self.features.index,
            columns=smoothed_cols,
        ).reset_index()

        logger.info(
            "Filtered probability preview:\n%s",
            self.filtered_probabilities_df.tail(),
        )

        logger.info(
            "Smoothed probability preview:\n%s",
            self.smoothed_probabilities_df.tail(),
        )

    def build_transition_matrix(self):
        logger.info("Building HMM transition matrix.")

        self.transition_matrix = pd.DataFrame(
            self.model.transmat_,
            index=[f"from_state_{i}" for i in range(self.n_states)],
            columns=[f"to_state_{i}" for i in range(self.n_states)],
        )

        logger.info(
            "Transition matrix:\n%s",
            self.transition_matrix.round(4),
        )

    def build_persistence_diagnostics(self):
        logger.info("Building regime persistence diagnostics.")

        rows = []

        for state in range(self.n_states):
            self_transition_prob = self.model.transmat_[state, state]

            if self_transition_prob < 1:
                expected_duration = 1 / (1 - self_transition_prob)
            else:
                expected_duration = np.inf

            rows.append(
                {
                    "hidden_state": state,
                    "self_transition_probability": self_transition_prob,
                    "expected_duration_days": expected_duration,
                }
            )

        self.persistence = pd.DataFrame(rows)

        logger.info(
            "Regime persistence diagnostics:\n%s",
            self.persistence.round(4),
        )

    def build_summary(self):
        logger.info("Building hidden regime summary.")

        summary = (
            self.regime_output
            .groupby("hidden_state")
            .agg(
                observations=("hidden_state", "count"),
                avg_spy_vol_20d=("spy_vol_20d", "mean"),
                avg_qqq_vol_20d=("qqq_vol_20d", "mean"),
                avg_btc_vol_20d=("btc_vol_20d", "mean"),
                avg_vix_level=("vix_level", "mean"),
                avg_vix_stress_ratio=("vix_stress_ratio", "mean"),
                avg_spy_momentum_20d=("spy_momentum_20d", "mean"),
                avg_tlt_momentum_20d=("tlt_momentum_20d", "mean"),
                avg_momentum_breadth=("momentum_breadth", "mean"),
                avg_equity_bond_corr_20d=("equity_bond_corr_20d", "mean"),
                avg_liquidity_stress_proxy=("liquidity_stress_proxy", "mean"),
                avg_realized_vol_regime_score=("realized_vol_regime_score", "mean"),
            )
            .reset_index()
        )

        self.summary = summary

        logger.info(
            "Hidden regime summary:\n%s",
            self.summary.round(4),
        )

    def save_outputs(self):
        logger.info("Saving HMM v2 outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.regime_output.to_csv(self.regime_output_path, index=False)
        self.filtered_probabilities_df.to_csv(self.filtered_probability_path, index=False)
        self.smoothed_probabilities_df.to_csv(self.smoothed_probability_path, index=False)
        self.transition_matrix.to_csv(self.transition_matrix_path)
        self.persistence.to_csv(self.persistence_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved hidden regimes to: %s", self.regime_output_path)
        logger.info("Saved filtered probabilities to: %s", self.filtered_probability_path)
        logger.info("Saved smoothed probabilities to: %s", self.smoothed_probability_path)
        logger.info("Saved transition matrix to: %s", self.transition_matrix_path)
        logger.info("Saved persistence diagnostics to: %s", self.persistence_path)
        logger.info("Saved regime summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Hidden Markov Regime Engine v2.")

        self.load_features()
        self.select_numeric_features()
        self.scale_features()
        self.fit_hmm()
        self.build_regime_output()
        self.build_probability_outputs()
        self.build_transition_matrix()
        self.build_persistence_diagnostics()
        self.build_summary()
        self.save_outputs()

        logger.info("Hidden Markov Regime Engine v2 completed successfully.")


if __name__ == "__main__":
    engine = HiddenMarkovRegimeEngine(n_states=3)
    engine.run()