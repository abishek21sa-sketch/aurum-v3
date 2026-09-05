from pathlib import Path
import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class CorrelationBreakdownDetector:
    """
    Correlation Breakdown Detector v2 for AURUM.

    Detects:
    - crisis correlation spikes
    - diversification collapse
    - instability clustering
    - rolling network stress
    """

    def __init__(self, window: int = 20):
        self.window = window

        self.returns_path = Path("data/market_matrix/market_return_matrix.csv")
        self.regime_path = Path("data/regimes/calibrated_regime_probabilities.csv")

        self.output_dir = Path("data/risk")
        self.report_path = self.output_dir / "correlation_breakdown_report.csv"
        self.summary_path = self.output_dir / "correlation_breakdown_summary.csv"

    def load_inputs(self):
        logger.info("Loading return matrix from: %s", self.returns_path)
        logger.info("Loading calibrated regimes from: %s", self.regime_path)

        self.returns = pd.read_csv(self.returns_path)
        self.regimes = pd.read_csv(self.regime_path)

        self.returns["Date"] = pd.to_datetime(self.returns["Date"])
        self.regimes["Date"] = pd.to_datetime(self.regimes["Date"])

        logger.info("Loaded returns shape: %s", self.returns.shape)
        logger.info("Loaded regimes shape: %s", self.regimes.shape)

    def compute_rolling_correlation_features(self):
        logger.info("Computing rolling correlation features.")

        asset_cols = [col for col in self.returns.columns if col != "Date"]

        records = []

        for idx in range(self.window, len(self.returns)):
            window_df = self.returns.iloc[idx - self.window:idx][asset_cols].dropna()

            if len(window_df) < self.window // 2:
                continue

            corr = window_df.corr()

            corr_values = corr.unstack()
            corr_values = corr_values[
                corr_values.index.get_level_values(0)
                != corr_values.index.get_level_values(1)
            ]

            abs_corr = corr_values.abs()

            high_corr_edges = (abs_corr >= 0.70).sum()
            possible_edges = len(abs_corr)

            network_stress = high_corr_edges / possible_edges if possible_edges > 0 else 0

            records.append(
                {
                    "Date": self.returns.iloc[idx]["Date"],
                    "rolling_avg_abs_corr": abs_corr.mean(),
                    "rolling_max_abs_corr": abs_corr.max(),
                    "rolling_corr_dispersion": abs_corr.std(),
                    "high_corr_edge_ratio": network_stress,
                }
            )

        self.correlation_features = pd.DataFrame(records)

        logger.info(
            "Correlation feature preview:\n%s",
            self.correlation_features.tail(),
        )

    def detect_breakdowns(self):
        logger.info("Detecting diversification breakdowns.")

        df = self.correlation_features.copy()

        avg_corr_threshold = df["rolling_avg_abs_corr"].quantile(0.80)
        max_corr_threshold = df["rolling_max_abs_corr"].quantile(0.90)
        network_threshold = df["high_corr_edge_ratio"].quantile(0.85)

        df["avg_corr_spike_flag"] = (
            df["rolling_avg_abs_corr"] >= avg_corr_threshold
        ).astype(int)

        df["max_corr_spike_flag"] = (
            df["rolling_max_abs_corr"] >= max_corr_threshold
        ).astype(int)

        df["network_stress_flag"] = (
            df["high_corr_edge_ratio"] >= network_threshold
        ).astype(int)

        df["diversification_collapse_score"] = (
            0.40 * df["avg_corr_spike_flag"]
            + 0.30 * df["max_corr_spike_flag"]
            + 0.30 * df["network_stress_flag"]
        )

        df["collapse_label"] = pd.cut(
            df["diversification_collapse_score"],
            bins=[-0.01, 0.01, 0.60, 1.00],
            labels=[
                "normal_diversification",
                "partial_breakdown",
                "severe_collapse",
            ],
        )

        df["instability_cluster_score"] = (
            df["diversification_collapse_score"]
            .rolling(window=5, min_periods=1)
            .mean()
        )

        self.breakdown_report = df

        logger.info(
            "Breakdown report preview:\n%s",
            self.breakdown_report.tail(),
        )

    def merge_regimes(self):
        logger.info("Merging correlation breakdown data with regimes.")

        regime_cols = [
            "Date",
            "calibrated_most_likely_state",
            "calibrated_regime_confidence",
            "calibrated_state_0_probability",
            "calibrated_state_1_probability",
            "calibrated_state_2_probability",
        ]

        self.breakdown_report = self.breakdown_report.merge(
            self.regimes[regime_cols],
            on="Date",
            how="left",
        )

        logger.info(
            "Merged breakdown preview:\n%s",
            self.breakdown_report.tail(),
        )

    def build_summary(self):
        logger.info("Building correlation breakdown summary.")

        self.summary = (
            self.breakdown_report
            .groupby(
                ["calibrated_most_likely_state", "collapse_label"],
                observed=False,
            )
            .agg(
                observations=("collapse_label", "count"),
                avg_abs_corr=("rolling_avg_abs_corr", "mean"),
                max_abs_corr=("rolling_max_abs_corr", "max"),
                avg_high_corr_edge_ratio=("high_corr_edge_ratio", "mean"),
                avg_collapse_score=("diversification_collapse_score", "mean"),
                avg_instability_cluster_score=("instability_cluster_score", "mean"),
                avg_regime_confidence=("calibrated_regime_confidence", "mean"),
            )
            .reset_index()
        )

        logger.info(
            "Correlation breakdown summary:\n%s",
            self.summary.round(4),
        )

    def save_outputs(self):
        logger.info("Saving correlation breakdown outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.breakdown_report.to_csv(self.report_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved breakdown report to: %s", self.report_path)
        logger.info("Saved breakdown summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Correlation Breakdown Detector v2.")

        self.load_inputs()
        self.compute_rolling_correlation_features()
        self.detect_breakdowns()
        self.merge_regimes()
        self.build_summary()
        self.save_outputs()

        logger.info("Correlation Breakdown Detector v2 completed successfully.")


if __name__ == "__main__":
    detector = CorrelationBreakdownDetector(window=20)
    detector.run()