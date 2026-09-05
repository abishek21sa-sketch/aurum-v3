from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class SignalDecayAnalyzer:
    """
    Institutional Signal Decay Analyzer v2.

    Measures:
    - signal persistence
    - alpha decay
    - IC decay
    - regime-conditioned predictability
    - top-bottom spread persistence
    """

    def __init__(self):
        self.forecast_path = Path(
            "data/forecasting/ensemble_forecast_signals.csv"
        )

        self.return_matrix_path = Path(
            "data/market_matrix/market_return_matrix.csv"
        )

        self.output_dir = Path("data/forecasting")

        self.report_path = (
            self.output_dir / "signal_decay_report.csv"
        )

        self.summary_path = (
            self.output_dir / "signal_decay_summary.csv"
        )

        self.regime_summary_path = (
            self.output_dir / "signal_decay_regime_summary.csv"
        )

    def load_inputs(self):
        logger.info(
            "Loading ensemble forecast signals from: %s",
            self.forecast_path,
        )

        logger.info(
            "Loading return matrix from: %s",
            self.return_matrix_path,
        )

        self.forecasts = pd.read_csv(self.forecast_path)
        self.returns = pd.read_csv(self.return_matrix_path)

        self.forecasts["Date"] = pd.to_datetime(
            self.forecasts["Date"]
        )

        self.returns["Date"] = pd.to_datetime(
            self.returns["Date"]
        )

        logger.info(
            "Loaded forecasts shape: %s",
            self.forecasts.shape,
        )

        logger.info(
            "Loaded returns shape: %s",
            self.returns.shape,
        )

    def reshape_returns(self):
        logger.info("Reshaping return matrix.")

        long_returns = self.returns.melt(
            id_vars="Date",
            var_name="asset",
            value_name="daily_return",
        )

        self.long_returns = long_returns

        logger.info(
            "Long returns shape: %s",
            self.long_returns.shape,
        )

    def build_forward_returns(self):
        logger.info("Building forward returns.")

        horizons = [1, 5, 10, 20]

        frames = []

        for asset, group in self.long_returns.groupby("asset"):

            group = group.sort_values("Date").copy()

            for horizon in horizons:

                group[f"forward_return_{horizon}d"] = (
                    group["daily_return"]
                    .rolling(horizon)
                    .sum()
                    .shift(-horizon)
                )

            frames.append(group)

        self.forward_returns = pd.concat(
            frames,
            ignore_index=True,
        )

        logger.info(
            "Forward return preview:\n%s",
            self.forward_returns.tail(),
        )

    def merge_forecasts(self):
        logger.info(
            "Merging forecasts with forward returns."
        )

        merge_cols = [
            "Date",
            "asset",
            "uncertainty_adjusted_signal",
            "forecast_conviction",
            "allocation_preference_rank",
            "calibrated_most_likely_state",
        ]

        self.dataset = self.forecasts[merge_cols].merge(
            self.forward_returns,
            on=["Date", "asset"],
            how="inner",
        )

        logger.info(
            "Merged dataset shape: %s",
            self.dataset.shape,
        )

    def compute_signal_decay_metrics(self):
        logger.info(
            "Computing institutional decay metrics."
        )

        horizons = [1, 5, 10, 20]

        rows = []

        for horizon in horizons:

            target = f"forward_return_{horizon}d"

            valid = self.dataset.dropna(
                subset=[
                    "uncertainty_adjusted_signal",
                    target,
                ]
            ).copy()

            for asset, asset_df in valid.groupby("asset"):

                if len(asset_df) < 25:
                    continue

                signal = asset_df[
                    "uncertainty_adjusted_signal"
                ]

                future = asset_df[target]

                pearson_ic = signal.corr(future)

                rank_ic = (
                    signal.rank().corr(
                        future.rank()
                    )
                )

                top_threshold = signal.quantile(0.8)
                bottom_threshold = signal.quantile(0.2)

                top_future = future[
                    signal >= top_threshold
                ].mean()

                bottom_future = future[
                    signal <= bottom_threshold
                ].mean()

                spread = (
                    top_future - bottom_future
                )

                persistence = (
                    asset_df[
                        "forecast_conviction"
                    ].corr(signal)
                )

                rows.append(
                    {
                        "asset": asset,
                        "horizon_days": horizon,
                        "pearson_ic": pearson_ic,
                        "rank_ic": rank_ic,
                        "top_bottom_spread": spread,
                        "signal_persistence": persistence,
                        "observations": len(asset_df),
                    }
                )

        self.decay_report = pd.DataFrame(rows)

        logger.info(
            "Signal decay preview:\n%s",
            self.decay_report.head(20),
        )

    def compute_regime_conditioned_decay(self):
        logger.info(
            "Computing regime-conditioned decay."
        )

        horizons = [1, 5, 10, 20]

        rows = []

        for horizon in horizons:

            target = f"forward_return_{horizon}d"

            valid = self.dataset.dropna(
                subset=[
                    "uncertainty_adjusted_signal",
                    target,
                ]
            )

            grouped = valid.groupby(
                "calibrated_most_likely_state"
            )

            for regime, regime_df in grouped:

                if len(regime_df) < 25:
                    continue

                ic = regime_df[
                    "uncertainty_adjusted_signal"
                ].corr(regime_df[target])

                rows.append(
                    {
                        "regime_state": regime,
                        "horizon_days": horizon,
                        "signal_ic": ic,
                        "observations": len(regime_df),
                    }
                )

        self.regime_summary = pd.DataFrame(rows)

        logger.info(
            "Regime-conditioned summary:\n%s",
            self.regime_summary,
        )

    def build_summary(self):
        logger.info(
            "Building decay summary."
        )

        self.summary = (
            self.decay_report
            .groupby("horizon_days")
            .agg(
                avg_pearson_ic=(
                    "pearson_ic",
                    "mean",
                ),
                avg_rank_ic=(
                    "rank_ic",
                    "mean",
                ),
                avg_top_bottom_spread=(
                    "top_bottom_spread",
                    "mean",
                ),
                avg_signal_persistence=(
                    "signal_persistence",
                    "mean",
                ),
                observations=(
                    "observations",
                    "sum",
                ),
            )
            .reset_index()
        )

        logger.info(
            "Signal decay summary:\n%s",
            self.summary.round(4),
        )

    def save_outputs(self):
        logger.info(
            "Saving signal decay outputs."
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.decay_report.to_csv(
            self.report_path,
            index=False,
        )

        self.summary.to_csv(
            self.summary_path,
            index=False,
        )

        self.regime_summary.to_csv(
            self.regime_summary_path,
            index=False,
        )

        logger.info(
            "Saved decay report to: %s",
            self.report_path,
        )

        logger.info(
            "Saved decay summary to: %s",
            self.summary_path,
        )

        logger.info(
            "Saved regime summary to: %s",
            self.regime_summary_path,
        )

    def run(self):
        logger.info(
            "Starting Signal Decay Analyzer v2."
        )

        self.load_inputs()
        self.reshape_returns()
        self.build_forward_returns()
        self.merge_forecasts()
        self.compute_signal_decay_metrics()
        self.compute_regime_conditioned_decay()
        self.build_summary()
        self.save_outputs()

        logger.info(
            "Signal Decay Analyzer v2 completed successfully."
        )


if __name__ == "__main__":
    analyzer = SignalDecayAnalyzer()
    analyzer.run()