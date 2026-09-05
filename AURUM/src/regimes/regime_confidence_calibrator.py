from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class RegimeConfidenceCalibrator:
    """
    Regime Confidence Calibrator v2 for AURUM.

    Fixes overconfident Bayesian/HMM outputs using:
    - probability floor
    - temperature softening
    - confidence cap
    - rolling posterior smoothing
    - calibrated entropy diagnostics
    """

    def __init__(
        self,
        temperature: float = 6.0,
        probability_floor: float = 0.03,
        confidence_cap: float = 0.92,
        smoothing_window: int = 3,
    ):
        self.temperature = temperature
        self.probability_floor = probability_floor
        self.confidence_cap = confidence_cap
        self.smoothing_window = smoothing_window

        self.input_path = Path("data/regimes/bayesian_regime_probabilities.csv")
        self.diagnostics_path = Path("data/regimes/bayesian_regime_diagnostics.csv")

        self.output_dir = Path("data/regimes")
        self.output_path = self.output_dir / "calibrated_regime_probabilities.csv"
        self.summary_path = self.output_dir / "calibrated_regime_summary.csv"

    def load_inputs(self):
        logger.info("Loading Bayesian regime probabilities from: %s", self.input_path)

        self.data = pd.read_csv(self.input_path)
        self.data["Date"] = pd.to_datetime(self.data["Date"])

        if self.diagnostics_path.exists():
            self.diagnostics = pd.read_csv(self.diagnostics_path)
        else:
            self.diagnostics = pd.DataFrame()

        logger.info("Loaded Bayesian probabilities shape: %s", self.data.shape)

    def identify_probability_columns(self):
        logger.info("Identifying posterior probability columns.")

        self.posterior_cols = [
            col for col in self.data.columns
            if col.startswith("posterior_state_") and col.endswith("_probability")
        ]

        logger.info("Posterior probability columns: %s", self.posterior_cols)

    def apply_probability_floor(self):
        logger.info("Applying probability floor: %.4f", self.probability_floor)

        probs = self.data[self.posterior_cols].copy()
        probs = probs.clip(lower=self.probability_floor)
        probs = probs.div(probs.sum(axis=1), axis=0)

        self.floored_probs = probs

    def apply_temperature_softening(self):
        logger.info("Applying temperature softening: %.2f", self.temperature)

        softened = self.floored_probs ** (1 / self.temperature)
        softened = softened.div(softened.sum(axis=1), axis=0)

        self.softmax_probs = softened

    def apply_rolling_smoothing(self):
        logger.info("Applying rolling probability smoothing window: %s", self.smoothing_window)

        smoothed = (
            self.softmax_probs
            .rolling(window=self.smoothing_window, min_periods=1)
            .mean()
        )

        smoothed = smoothed.div(smoothed.sum(axis=1), axis=0)

        self.smoothed_probs = smoothed

    def enforce_confidence_cap(self):
        logger.info("Enforcing confidence cap: %.4f", self.confidence_cap)

        calibrated = self.smoothed_probs.copy()

        for idx in calibrated.index:
            row = calibrated.loc[idx]
            max_col = row.idxmax()
            max_prob = row[max_col]

            if max_prob > self.confidence_cap:
                excess = max_prob - self.confidence_cap
                calibrated.loc[idx, max_col] = self.confidence_cap

                other_cols = [col for col in calibrated.columns if col != max_col]
                other_sum = calibrated.loc[idx, other_cols].sum()

                if other_sum > 0:
                    calibrated.loc[idx, other_cols] = (
                        calibrated.loc[idx, other_cols]
                        + excess * calibrated.loc[idx, other_cols] / other_sum
                    )
                else:
                    calibrated.loc[idx, other_cols] = excess / len(other_cols)

        calibrated = calibrated.div(calibrated.sum(axis=1), axis=0)

        self.calibrated_probs = calibrated

    def build_calibrated_dataset(self):
        logger.info("Building calibrated regime probability dataset.")

        df = self.data.copy()

        self.calibrated_cols = []

        for posterior_col in self.posterior_cols:
            state_id = posterior_col.replace("posterior_state_", "").replace("_probability", "")
            calibrated_col = f"calibrated_state_{state_id}_probability"

            df[calibrated_col] = self.calibrated_probs[posterior_col]
            self.calibrated_cols.append(calibrated_col)

        df["calibrated_most_likely_state"] = (
            df[self.calibrated_cols]
            .idxmax(axis=1)
            .str.extract(r"calibrated_state_(\d+)_probability")
            .astype(int)
        )

        clipped = df[self.calibrated_cols].clip(lower=1e-12)
        entropy = -(clipped * np.log(clipped)).sum(axis=1)
        max_entropy = np.log(len(self.calibrated_cols))

        df["calibrated_regime_entropy"] = entropy
        df["calibrated_normalized_entropy"] = entropy / max_entropy
        df["calibrated_regime_confidence"] = 1 - df["calibrated_normalized_entropy"]
        df["calibrated_max_probability"] = df[self.calibrated_cols].max(axis=1)

        self.calibrated_data = df

        logger.info(
            "Calibrated probability preview:\n%s",
            self.calibrated_data[
                ["Date"]
                + self.calibrated_cols
                + [
                    "calibrated_most_likely_state",
                    "calibrated_regime_confidence",
                    "calibrated_max_probability",
                ]
            ].tail(),
        )

    def build_summary(self):
        logger.info("Building calibrated regime summary.")

        rows = []

        for col in self.calibrated_cols:
            state_id = int(
                col.replace("calibrated_state_", "").replace("_probability", "")
            )

            rows.append(
                {
                    "state": state_id,
                    "avg_calibrated_probability": self.calibrated_data[col].mean(),
                    "max_calibrated_probability": self.calibrated_data[col].max(),
                    "min_calibrated_probability": self.calibrated_data[col].min(),
                }
            )

        self.summary = pd.DataFrame(rows)

        self.summary["avg_calibrated_entropy"] = (
            self.calibrated_data["calibrated_regime_entropy"].mean()
        )
        self.summary["avg_calibrated_confidence"] = (
            self.calibrated_data["calibrated_regime_confidence"].mean()
        )
        self.summary["avg_calibrated_max_probability"] = (
            self.calibrated_data["calibrated_max_probability"].mean()
        )

        logger.info("Calibrated regime summary:\n%s", self.summary.round(4))

    def save_outputs(self):
        logger.info("Saving calibrated regime outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.calibrated_data.to_csv(self.output_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved calibrated probabilities to: %s", self.output_path)
        logger.info("Saved calibrated summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Regime Confidence Calibrator v2.")

        self.load_inputs()
        self.identify_probability_columns()
        self.apply_probability_floor()
        self.apply_temperature_softening()
        self.apply_rolling_smoothing()
        self.enforce_confidence_cap()
        self.build_calibrated_dataset()
        self.build_summary()
        self.save_outputs()

        logger.info("Regime Confidence Calibrator v2 completed successfully.")


if __name__ == "__main__":
    calibrator = RegimeConfidenceCalibrator(
        temperature=3.0,
        probability_floor=0.01,
        confidence_cap=0.85,
        smoothing_window=3,
    )
    calibrator.run()