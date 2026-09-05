from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


ASSET_CLASS_MAP = {
    "SPY": "Equity",
    "QQQ": "Equity",
    "DIA": "Equity",
    "TLT": "Fixed Income",
    "GLD": "Commodity",
    "BTC-USD": "Crypto",
    "ETH-USD": "Crypto",
    "VIX": "Volatility",
    "CASH": "Cash",
}

SECTOR_MAP = {
    "SPY": "Broad Equity",
    "QQQ": "Technology",
    "DIA": "Industrial Equity",
    "TLT": "Government Bonds",
    "GLD": "Gold",
    "BTC-USD": "Digital Assets",
    "ETH-USD": "Digital Assets",
    "VIX": "Volatility",
    "CASH": "Cash",
}


class ExposureAnalyticsEngine:
    """
    AURUM Exposure Analytics Engine.

    Computes:
    - position concentration
    - top-N exposure
    - HHI concentration
    - effective number of assets
    - asset-class concentration
    - sector concentration
    """

    def __init__(self):
        self.weights_path = Path("data/institutional/portfolio_weights.csv")
        self.output_dir = Path("results/risk")
        self.report_path = self.output_dir / "exposure_report.csv"
        self.latest_snapshot_path = self.output_dir / "latest_exposure_snapshot.csv"

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

        logger.info("Loaded portfolio weights shape: %s", self.weights.shape)

    def get_latest_weights(self):
        latest_date = self.weights["Date"].max()

        latest = self.weights[self.weights["Date"] == latest_date].copy()
        latest["final_weight"] = latest["final_weight"].fillna(0.0)

        latest["asset_class"] = latest["asset"].map(ASSET_CLASS_MAP).fillna("Other")
        latest["sector"] = latest["asset"].map(SECTOR_MAP).fillna("Other")

        self.latest_date = latest_date
        self.latest_weights = latest

        logger.info("Latest exposure date: %s", latest_date.date())
        logger.info("Latest exposure snapshot:\n%s", latest)

    def compute_position_concentration(self):
        weights = (
            self.latest_weights[["asset", "final_weight"]]
            .sort_values("final_weight", ascending=False)
            .reset_index(drop=True)
        )

        positive_weights = weights[weights["final_weight"] > 0]["final_weight"]

        hhi = float(np.sum(np.square(positive_weights)))
        effective_assets = float(1 / hhi) if hhi > 0 else np.nan

        rows = [
            {
                "metric": "latest_exposure_date",
                "category": "position_concentration",
                "value": self.latest_date.strftime("%Y-%m-%d"),
            },
            {
                "metric": "largest_position_weight",
                "category": "position_concentration",
                "value": float(positive_weights.max()) if len(positive_weights) else 0.0,
            },
            {
                "metric": "top_3_weight",
                "category": "position_concentration",
                "value": float(positive_weights.head(3).sum()),
            },
            {
                "metric": "top_5_weight",
                "category": "position_concentration",
                "value": float(positive_weights.head(5).sum()),
            },
            {
                "metric": "hhi_concentration",
                "category": "position_concentration",
                "value": hhi,
            },
            {
                "metric": "effective_number_of_assets",
                "category": "position_concentration",
                "value": effective_assets,
            },
        ]

        self.position_report = pd.DataFrame(rows)

    def compute_group_exposure(self, group_col: str, category: str):
        grouped = (
            self.latest_weights
            .groupby(group_col)["final_weight"]
            .sum()
            .reset_index()
            .sort_values("final_weight", ascending=False)
        )

        grouped["metric"] = grouped[group_col].str.lower().str.replace(" ", "_") + "_exposure"
        grouped["category"] = category
        grouped["value"] = grouped["final_weight"]

        return grouped[["metric", "category", "value"]]

    def build_report(self):
        self.compute_position_concentration()

        asset_class_report = self.compute_group_exposure(
            group_col="asset_class",
            category="asset_class_exposure",
        )

        sector_report = self.compute_group_exposure(
            group_col="sector",
            category="sector_exposure",
        )

        self.report = pd.concat(
            [
                self.position_report,
                asset_class_report,
                sector_report,
            ],
            ignore_index=True,
        )

    def save_outputs(self):
        logger.info("Saving exposure analytics outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.report.to_csv(self.report_path, index=False)
        self.latest_weights.to_csv(self.latest_snapshot_path, index=False)

        logger.info("Saved exposure report to: %s", self.report_path)
        logger.info("Saved latest exposure snapshot to: %s", self.latest_snapshot_path)

    def run(self):
        logger.info("Starting AURUM Exposure Analytics Engine.")

        self.load_inputs()
        self.get_latest_weights()
        self.build_report()
        self.save_outputs()

        logger.info("Exposure Analytics Engine completed successfully.")


if __name__ == "__main__":
    engine = ExposureAnalyticsEngine()
    engine.run()