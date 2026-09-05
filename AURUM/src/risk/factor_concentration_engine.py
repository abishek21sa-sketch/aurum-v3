from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


FACTOR_MAP = {
    "SPY": "market_factor",
    "QQQ": "market_factor",
    "DIA": "market_factor",
    "TLT": "duration_factor",
    "GLD": "gold_factor",
    "BTC-USD": "crypto_factor",
    "ETH-USD": "crypto_factor",
    "VIX": "volatility_factor",
    "CASH": "cash_factor",
}


class FactorConcentrationEngine:
    """
    AURUM Factor Concentration Engine.

    Computes latest portfolio factor exposure using final portfolio weights.
    """

    def __init__(self):
        self.weights_path = Path("data/institutional/portfolio_weights.csv")

        self.output_dir = Path("results/risk")
        self.report_path = self.output_dir / "factor_concentration_report.csv"
        self.snapshot_path = self.output_dir / "latest_factor_exposure_snapshot.csv"

    def load_inputs(self):
        logger.info("Loading portfolio weights from: %s", self.weights_path)

        if not self.weights_path.exists():
            raise FileNotFoundError(f"Missing input file: {self.weights_path}")

        self.weights = pd.read_csv(self.weights_path)
        self.weights["Date"] = pd.to_datetime(self.weights["Date"])

        required = ["Date", "asset", "final_weight"]
        missing = [col for col in required if col not in self.weights.columns]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def get_latest_weights(self):
        self.latest_date = self.weights["Date"].max()

        self.latest_weights = self.weights[
            self.weights["Date"] == self.latest_date
        ].copy()

        self.latest_weights["final_weight"] = self.latest_weights[
            "final_weight"
        ].fillna(0.0)

        self.latest_weights["factor"] = self.latest_weights["asset"].map(
            FACTOR_MAP
        ).fillna("other_factor")

    def build_factor_report(self):
        factor_exposure = (
            self.latest_weights
            .groupby("factor")["final_weight"]
            .sum()
            .reset_index()
            .sort_values("final_weight", ascending=False)
        )

        factor_exposure["metric"] = factor_exposure["factor"] + "_exposure"
        factor_exposure["category"] = "factor_exposure"
        factor_exposure["value"] = factor_exposure["final_weight"]

        positive = factor_exposure[factor_exposure["value"] > 0]["value"]

        hhi = float(np.sum(np.square(positive)))
        effective_factors = float(1 / hhi) if hhi > 0 else np.nan

        summary_rows = pd.DataFrame(
            [
                {
                    "metric": "latest_factor_exposure_date",
                    "category": "factor_concentration",
                    "value": self.latest_date.strftime("%Y-%m-%d"),
                },
                {
                    "metric": "largest_factor_exposure",
                    "category": "factor_concentration",
                    "value": float(positive.max()) if len(positive) else 0.0,
                },
                {
                    "metric": "factor_hhi_concentration",
                    "category": "factor_concentration",
                    "value": hhi,
                },
                {
                    "metric": "effective_number_of_factors",
                    "category": "factor_concentration",
                    "value": effective_factors,
                },
            ]
        )

        self.report = pd.concat(
            [
                summary_rows,
                factor_exposure[["metric", "category", "value"]],
            ],
            ignore_index=True,
        )

    def save_outputs(self):
        logger.info("Saving factor concentration outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.report.to_csv(self.report_path, index=False)
        self.latest_weights.to_csv(self.snapshot_path, index=False)

        logger.info("Saved factor concentration report to: %s", self.report_path)
        logger.info("Saved latest factor snapshot to: %s", self.snapshot_path)

    def run(self):
        logger.info("Starting AURUM Factor Concentration Engine.")

        self.load_inputs()
        self.get_latest_weights()
        self.build_factor_report()
        self.save_outputs()

        logger.info("Factor Concentration Engine completed successfully.")


if __name__ == "__main__":
    engine = FactorConcentrationEngine()
    engine.run()