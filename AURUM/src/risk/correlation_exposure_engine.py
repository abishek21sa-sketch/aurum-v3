from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class CorrelationExposureEngine:
    """
    AURUM Correlation Exposure Engine.

    Computes:
    - asset correlation matrix
    - average correlation
    - average absolute correlation
    - max/min correlation pairs
    - high-correlation pair count
    - diversification score
    """

    def __init__(self):
        self.return_matrix_path = Path("data/market_matrix/market_return_matrix.csv")

        self.output_dir = Path("results/risk")
        self.report_path = self.output_dir / "correlation_report.csv"
        self.matrix_path = self.output_dir / "correlation_matrix.csv"

    def load_inputs(self):
        logger.info("Loading market return matrix from: %s", self.return_matrix_path)

        if not self.return_matrix_path.exists():
            raise FileNotFoundError(f"Missing input file: {self.return_matrix_path}")

        self.returns = pd.read_csv(self.return_matrix_path)
        self.returns["Date"] = pd.to_datetime(self.returns["Date"])

        self.asset_cols = [col for col in self.returns.columns if col != "Date"]

        if len(self.asset_cols) < 2:
            raise ValueError("Need at least two asset return columns to compute correlations.")

        logger.info("Loaded return matrix shape: %s", self.returns.shape)
        logger.info("Assets: %s", self.asset_cols)

    def build_correlation_matrix(self):
        logger.info("Computing asset correlation matrix.")

        self.correlation_matrix = self.returns[self.asset_cols].corr()

    def extract_pairwise_correlations(self):
        rows = []

        for i, asset_a in enumerate(self.asset_cols):
            for asset_b in self.asset_cols[i + 1:]:
                corr = self.correlation_matrix.loc[asset_a, asset_b]

                rows.append(
                    {
                        "asset_a": asset_a,
                        "asset_b": asset_b,
                        "correlation": corr,
                        "abs_correlation": abs(corr),
                    }
                )

        self.pairwise = pd.DataFrame(rows).dropna()

        if self.pairwise.empty:
            raise ValueError("No valid pairwise correlations could be computed.")

    def build_report(self):
        logger.info("Building correlation exposure report.")

        average_correlation = self.pairwise["correlation"].mean()
        average_abs_correlation = self.pairwise["abs_correlation"].mean()

        max_row = self.pairwise.loc[self.pairwise["correlation"].idxmax()]
        min_row = self.pairwise.loc[self.pairwise["correlation"].idxmin()]
        max_abs_row = self.pairwise.loc[self.pairwise["abs_correlation"].idxmax()]

        high_corr_pairs = int((self.pairwise["correlation"] > 0.80).sum())
        negative_corr_pairs = int((self.pairwise["correlation"] < 0.00).sum())

        diversification_score = 1 - average_abs_correlation

        rows = [
            {
                "metric": "average_correlation",
                "value": average_correlation,
                "detail": "Mean pairwise correlation across assets.",
            },
            {
                "metric": "average_absolute_correlation",
                "value": average_abs_correlation,
                "detail": "Mean absolute pairwise correlation across assets.",
            },
            {
                "metric": "diversification_score",
                "value": diversification_score,
                "detail": "Simple diversification score: 1 - average absolute correlation.",
            },
            {
                "metric": "maximum_correlation",
                "value": max_row["correlation"],
                "detail": f"{max_row['asset_a']} vs {max_row['asset_b']}",
            },
            {
                "metric": "minimum_correlation",
                "value": min_row["correlation"],
                "detail": f"{min_row['asset_a']} vs {min_row['asset_b']}",
            },
            {
                "metric": "maximum_absolute_correlation",
                "value": max_abs_row["abs_correlation"],
                "detail": f"{max_abs_row['asset_a']} vs {max_abs_row['asset_b']}",
            },
            {
                "metric": "high_correlation_pairs_above_0_80",
                "value": high_corr_pairs,
                "detail": "Number of asset pairs with correlation above 0.80.",
            },
            {
                "metric": "negative_correlation_pairs",
                "value": negative_corr_pairs,
                "detail": "Number of asset pairs with negative correlation.",
            },
            {
                "metric": "asset_count",
                "value": len(self.asset_cols),
                "detail": "Number of assets in correlation universe.",
            },
            {
                "metric": "pair_count",
                "value": len(self.pairwise),
                "detail": "Number of unique asset pairs.",
            },
        ]

        self.report = pd.DataFrame(rows)

    def save_outputs(self):
        logger.info("Saving correlation exposure outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.report.to_csv(self.report_path, index=False)
        self.correlation_matrix.to_csv(self.matrix_path)

        logger.info("Saved correlation report to: %s", self.report_path)
        logger.info("Saved correlation matrix to: %s", self.matrix_path)

    def run(self):
        logger.info("Starting AURUM Correlation Exposure Engine.")

        self.load_inputs()
        self.build_correlation_matrix()
        self.extract_pairwise_correlations()
        self.build_report()
        self.save_outputs()

        logger.info("Correlation Exposure Engine completed successfully.")


if __name__ == "__main__":
    engine = CorrelationExposureEngine()
    engine.run()