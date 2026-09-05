from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class WalkForwardFramework:
    """
    Institutional Walk-Forward Validation Framework.

    Implements:
    - expanding-window validation
    - rolling retraining
    - out-of-sample evaluation
    - temporal robustness testing
    - walk-forward portfolio simulation
    """

    def __init__(self):
        self.signal_path = Path(
            "data/forecasting/ensemble_forecast_signals.csv"
        )

        self.return_path = Path(
            "data/market_matrix/market_return_matrix.csv"
        )

        self.output_dir = Path("data/validation")

        self.walk_forward_report_path = (
            self.output_dir / "walk_forward_report.csv"
        )

        self.oos_predictions_path = (
            self.output_dir / "walk_forward_predictions.csv"
        )

        self.window_summary_path = (
            self.output_dir / "walk_forward_window_summary.csv"
        )

        self.equity_curve_path = (
            self.output_dir / "walk_forward_equity_curve.csv"
        )

    def load_inputs(self):
        logger.info(
            "Loading forecast signals from: %s",
            self.signal_path,
        )

        logger.info(
            "Loading return matrix from: %s",
            self.return_path,
        )

        self.signals = pd.read_csv(self.signal_path)
        self.returns = pd.read_csv(self.return_path)

        self.signals["Date"] = pd.to_datetime(
            self.signals["Date"]
        )

        self.returns["Date"] = pd.to_datetime(
            self.returns["Date"]
        )

        logger.info(
            "Loaded signals shape: %s",
            self.signals.shape,
        )

        logger.info(
            "Loaded returns shape: %s",
            self.returns.shape,
        )

    def reshape_returns(self):
        logger.info(
            "Reshaping return matrix."
        )

        long_returns = self.returns.melt(
            id_vars="Date",
            var_name="asset",
            value_name="daily_return",
        )

        frames = []

        for asset, group in long_returns.groupby("asset"):

            group = group.sort_values("Date").copy()

            group["forward_return_1d"] = (
                group["daily_return"].shift(-1)
            )

            frames.append(group)

        self.forward_returns = pd.concat(
            frames,
            ignore_index=True,
        )

        logger.info(
            "Forward return dataset shape: %s",
            self.forward_returns.shape,
        )

    def build_dataset(self):
        logger.info(
            "Building walk-forward dataset."
        )

        merge_cols = [
            "Date",
            "asset",
            "uncertainty_adjusted_signal",
            "forecast_conviction",
            "calibrated_most_likely_state",
        ]

        self.dataset = self.signals[
            merge_cols
        ].merge(
            self.forward_returns[
                [
                    "Date",
                    "asset",
                    "forward_return_1d",
                ]
            ],
            on=["Date", "asset"],
            how="inner",
        )

        self.dataset = self.dataset.dropna()

        logger.info(
            "Walk-forward dataset shape: %s",
            self.dataset.shape,
        )

    def run_walk_forward_validation(self):
        logger.info(
            "Running expanding-window walk-forward validation."
        )

        unique_dates = (
            self.dataset["Date"]
            .sort_values()
            .unique()
        )

        train_window = 120
        step_size = 20

        prediction_rows = []
        summary_rows = []

        for start_idx in range(
            train_window,
            len(unique_dates) - step_size,
            step_size,
        ):

            train_dates = unique_dates[:start_idx]
            test_dates = unique_dates[
                start_idx:start_idx + step_size
            ]

            train_df = self.dataset[
                self.dataset["Date"].isin(train_dates)
            ]

            test_df = self.dataset[
                self.dataset["Date"].isin(test_dates)
            ]

            if len(test_df) == 0:
                continue

            train_ic = train_df[
                "uncertainty_adjusted_signal"
            ].corr(
                train_df["forward_return_1d"]
            )

            for test_date, group in test_df.groupby("Date"):

                group = group.copy()

                signal_rank = (
                    group[
                        "uncertainty_adjusted_signal"
                    ]
                    .rank(pct=True)
                )

                top_assets = group[
                    signal_rank >= 0.8
                ]

                bottom_assets = group[
                    signal_rank <= 0.2
                ]

                if (
                    len(top_assets) == 0
                    or len(bottom_assets) == 0
                ):
                    continue

                long_return = top_assets[
                    "forward_return_1d"
                ].mean()

                short_return = bottom_assets[
                    "forward_return_1d"
                ].mean()

                long_short_return = (
                    long_return - short_return
                )

                realized_ic = group[
                    "uncertainty_adjusted_signal"
                ].corr(
                    group["forward_return_1d"]
                )

                prediction_rows.append(
                    {
                        "Date": test_date,
                        "train_ic": train_ic,
                        "realized_ic": realized_ic,
                        "long_return": long_return,
                        "short_return": short_return,
                        "long_short_return": long_short_return,
                        "top_assets": ",".join(
                            top_assets["asset"]
                        ),
                        "bottom_assets": ",".join(
                            bottom_assets["asset"]
                        ),
                    }
                )

            summary_rows.append(
                {
                    "train_start": train_dates.min(),
                    "train_end": train_dates.max(),
                    "test_start": test_dates.min(),
                    "test_end": test_dates.max(),
                    "train_observations": len(train_df),
                    "test_observations": len(test_df),
                    "train_ic": train_ic,
                }
            )

        self.predictions = pd.DataFrame(
            prediction_rows
        )

        self.window_summary = pd.DataFrame(
            summary_rows
        )

        logger.info(
            "Walk-forward prediction preview:\n%s",
            self.predictions.tail(),
        )

        logger.info(
            "Window summary preview:\n%s",
            self.window_summary.tail(),
        )

    def build_equity_curve(self):
        logger.info(
            "Building out-of-sample equity curve."
        )

        df = self.predictions.copy()

        df = df.sort_values("Date")

        df["equity_curve"] = (
            1 + df["long_short_return"]
        ).cumprod()

        df["rolling_peak"] = (
            df["equity_curve"].cummax()
        )

        df["drawdown"] = (
            df["equity_curve"]
            / df["rolling_peak"]
            - 1
        )

        self.equity_curve = df

        logger.info(
            "Equity curve preview:\n%s",
            self.equity_curve.tail(),
        )

    def build_summary_report(self):
        logger.info(
            "Building walk-forward summary report."
        )

        returns = self.predictions[
            "long_short_return"
        ].dropna()

        avg_return = returns.mean()
        volatility = returns.std()

        sharpe_like = (
            avg_return
            / volatility
            * np.sqrt(252)
            if volatility != 0
            else np.nan
        )

        max_drawdown = (
            self.equity_curve["drawdown"].min()
            if not self.equity_curve.empty
            else np.nan
        )

        avg_realized_ic = (
            self.predictions[
                "realized_ic"
            ].mean()
        )

        avg_train_ic = (
            self.predictions[
                "train_ic"
            ].mean()
        )

        self.summary_report = pd.DataFrame(
            [
                {
                    "walk_forward_periods": len(
                        self.window_summary
                    ),
                    "prediction_days": len(
                        self.predictions
                    ),
                    "avg_long_short_return": avg_return,
                    "long_short_volatility": volatility,
                    "walk_forward_sharpe_like": sharpe_like,
                    "max_drawdown": max_drawdown,
                    "avg_train_ic": avg_train_ic,
                    "avg_realized_ic": avg_realized_ic,
                }
            ]
        )

        logger.info(
            "Walk-forward summary:\n%s",
            self.summary_report.round(6),
        )

    def save_outputs(self):
        logger.info(
            "Saving walk-forward outputs."
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.summary_report.to_csv(
            self.walk_forward_report_path,
            index=False,
        )

        self.predictions.to_csv(
            self.oos_predictions_path,
            index=False,
        )

        self.window_summary.to_csv(
            self.window_summary_path,
            index=False,
        )

        self.equity_curve.to_csv(
            self.equity_curve_path,
            index=False,
        )

        logger.info(
            "Saved summary report to: %s",
            self.walk_forward_report_path,
        )

        logger.info(
            "Saved predictions to: %s",
            self.oos_predictions_path,
        )

        logger.info(
            "Saved window summary to: %s",
            self.window_summary_path,
        )

        logger.info(
            "Saved equity curve to: %s",
            self.equity_curve_path,
        )

    def run(self):
        logger.info(
            "Starting Walk-Forward Framework."
        )

        self.load_inputs()
        self.reshape_returns()
        self.build_dataset()
        self.run_walk_forward_validation()
        self.build_equity_curve()
        self.build_summary_report()
        self.save_outputs()

        logger.info(
            "Walk-Forward Framework completed successfully."
        )


if __name__ == "__main__":
    framework = WalkForwardFramework()
    framework.run()