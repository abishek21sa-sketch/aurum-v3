from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class AlphaValidationEngine:
    """
    Alpha Validation Engine for AURUM.

    Validates whether forecast signals are economically useful using:
    - quantile portfolios
    - long-short spreads
    - hit ratio
    - rolling IC
    - turnover
    - regime-conditioned alpha performance
    - equity curve construction
    """

    def __init__(self):
        self.forecast_path = Path("data/forecasting/ensemble_forecast_signals.csv")
        self.return_path = Path("data/market_matrix/market_return_matrix.csv")

        self.output_dir = Path("data/validation")
        self.validation_report_path = self.output_dir / "alpha_validation_report.csv"
        self.quantile_returns_path = self.output_dir / "alpha_quantile_returns.csv"
        self.rolling_ic_path = self.output_dir / "rolling_ic_report.csv"
        self.regime_report_path = self.output_dir / "regime_alpha_report.csv"
        self.equity_curve_path = self.output_dir / "long_short_equity_curve.csv"
        self.turnover_path = self.output_dir / "alpha_turnover_report.csv"

    def load_inputs(self):
        logger.info("Loading forecasts from: %s", self.forecast_path)
        logger.info("Loading returns from: %s", self.return_path)

        self.forecasts = pd.read_csv(self.forecast_path)
        self.returns = pd.read_csv(self.return_path)

        self.forecasts["Date"] = pd.to_datetime(self.forecasts["Date"])
        self.returns["Date"] = pd.to_datetime(self.returns["Date"])

        logger.info("Loaded forecasts shape: %s", self.forecasts.shape)
        logger.info("Loaded returns shape: %s", self.returns.shape)

    def reshape_returns(self):
        logger.info("Reshaping return matrix.")

        self.long_returns = self.returns.melt(
            id_vars="Date",
            var_name="asset",
            value_name="daily_return",
        )

        logger.info("Long returns shape: %s", self.long_returns.shape)

    def build_forward_returns(self):
        logger.info("Building forward return targets.")

        frames = []

        for asset, group in self.long_returns.groupby("asset"):
            group = group.sort_values("Date").copy()

            group["forward_return_1d"] = group["daily_return"].shift(-1)
            group["forward_return_5d"] = (
                group["daily_return"].rolling(5).sum().shift(-5)
            )
            group["forward_return_10d"] = (
                group["daily_return"].rolling(10).sum().shift(-10)
            )
            group["forward_return_20d"] = (
                group["daily_return"].rolling(20).sum().shift(-20)
            )

            frames.append(group)

        self.forward_returns = pd.concat(frames, ignore_index=True)

        logger.info(
            "Forward returns preview:\n%s",
            self.forward_returns.tail(),
        )

    def build_validation_dataset(self):
        logger.info("Building validation dataset.")

        signal_cols = [
            "Date",
            "asset",
            "uncertainty_adjusted_signal",
            "final_expected_return_signal",
            "forecast_conviction",
            "allocation_preference_rank",
            "calibrated_most_likely_state",
        ]

        forward_cols = [
            "Date",
            "asset",
            "forward_return_1d",
            "forward_return_5d",
            "forward_return_10d",
            "forward_return_20d",
        ]

        self.validation_data = self.forecasts[signal_cols].merge(
            self.forward_returns[forward_cols],
            on=["Date", "asset"],
            how="inner",
        )

        logger.info("Validation dataset shape: %s", self.validation_data.shape)

    def build_quantile_portfolios(self):
        logger.info("Building quantile long-short portfolios.")

        rows = []

        for date, group in self.validation_data.groupby("Date"):
            group = group.dropna(subset=["uncertainty_adjusted_signal", "forward_return_1d"])

            if len(group) < 4:
                continue

            top_threshold = group["uncertainty_adjusted_signal"].quantile(0.80)
            bottom_threshold = group["uncertainty_adjusted_signal"].quantile(0.20)

            top = group[group["uncertainty_adjusted_signal"] >= top_threshold]
            bottom = group[group["uncertainty_adjusted_signal"] <= bottom_threshold]

            if len(top) == 0 or len(bottom) == 0:
                continue

            row = {
                "Date": date,
                "top_portfolio_return_1d": top["forward_return_1d"].mean(),
                "bottom_portfolio_return_1d": bottom["forward_return_1d"].mean(),
                "long_short_return_1d": (
                    top["forward_return_1d"].mean()
                    - bottom["forward_return_1d"].mean()
                ),
                "top_assets": ",".join(top["asset"].tolist()),
                "bottom_assets": ",".join(bottom["asset"].tolist()),
            }

            for horizon in [5, 10, 20]:
                col = f"forward_return_{horizon}d"
                row[f"top_portfolio_return_{horizon}d"] = top[col].mean()
                row[f"bottom_portfolio_return_{horizon}d"] = bottom[col].mean()
                row[f"long_short_return_{horizon}d"] = (
                    top[col].mean() - bottom[col].mean()
                )

            rows.append(row)

        self.quantile_returns = pd.DataFrame(rows)

        logger.info(
            "Quantile portfolio preview:\n%s",
            self.quantile_returns.tail(),
        )

    def build_equity_curve(self):
        logger.info("Building long-short equity curve.")

        df = self.quantile_returns[["Date", "long_short_return_1d"]].dropna().copy()
        df = df.sort_values("Date")

        df["long_short_equity_curve"] = (1 + df["long_short_return_1d"]).cumprod()
        df["rolling_peak"] = df["long_short_equity_curve"].cummax()
        df["drawdown"] = df["long_short_equity_curve"] / df["rolling_peak"] - 1

        self.equity_curve = df

        logger.info(
            "Equity curve preview:\n%s",
            self.equity_curve.tail(),
        )

    def compute_rolling_ic(self):
        logger.info("Computing rolling IC metrics.")

        rows = []

        for date, group in self.validation_data.groupby("Date"):
            group = group.dropna(
                subset=["uncertainty_adjusted_signal", "forward_return_1d"]
            )

            if len(group) < 4:
                continue

            rows.append(
                {
                    "Date": date,
                    "pearson_ic_1d": group["uncertainty_adjusted_signal"].corr(
                        group["forward_return_1d"]
                    ),
                    "rank_ic_1d": group["uncertainty_adjusted_signal"].rank().corr(
                        group["forward_return_1d"].rank()
                    ),
                }
            )

        ic = pd.DataFrame(rows).sort_values("Date")

        ic["rolling_pearson_ic_20d"] = ic["pearson_ic_1d"].rolling(20).mean()
        ic["rolling_rank_ic_20d"] = ic["rank_ic_1d"].rolling(20).mean()

        self.rolling_ic = ic

        logger.info(
            "Rolling IC preview:\n%s",
            self.rolling_ic.tail(),
        )

    def compute_hit_ratio(self):
        logger.info("Computing hit ratio.")

        df = self.validation_data.dropna(
            subset=["uncertainty_adjusted_signal", "forward_return_1d"]
        ).copy()

        df["signal_direction"] = np.sign(df["uncertainty_adjusted_signal"])
        df["realized_direction"] = np.sign(df["forward_return_1d"])
        df["correct_direction"] = (
            df["signal_direction"] == df["realized_direction"]
        ).astype(int)

        self.hit_ratio = df["correct_direction"].mean()

        logger.info("Hit ratio: %.4f", self.hit_ratio)

    def compute_turnover(self):
        logger.info("Computing alpha portfolio turnover.")

        rows = []

        previous_top_assets = None

        for date, group in self.validation_data.groupby("Date"):
            group = group.dropna(subset=["uncertainty_adjusted_signal"])

            if len(group) < 4:
                continue

            top_threshold = group["uncertainty_adjusted_signal"].quantile(0.80)
            current_top_assets = set(
                group[group["uncertainty_adjusted_signal"] >= top_threshold]["asset"]
            )

            if previous_top_assets is None:
                turnover = 0.0
            else:
                union = previous_top_assets.union(current_top_assets)
                intersection = previous_top_assets.intersection(current_top_assets)

                turnover = 1 - len(intersection) / len(union) if len(union) > 0 else 0.0

            rows.append(
                {
                    "Date": date,
                    "top_book_turnover": turnover,
                    "top_book_size": len(current_top_assets),
                }
            )

            previous_top_assets = current_top_assets

        self.turnover_report = pd.DataFrame(rows)

        logger.info(
            "Turnover preview:\n%s",
            self.turnover_report.tail(),
        )

    def build_regime_report(self):
        logger.info("Building regime-conditioned alpha report.")

        df = self.validation_data.dropna(subset=["forward_return_1d"]).copy()

        self.regime_report = (
            df.groupby("calibrated_most_likely_state")
            .agg(
                observations=("asset", "count"),
                avg_signal=("uncertainty_adjusted_signal", "mean"),
                avg_forward_return_1d=("forward_return_1d", "mean"),
                avg_forward_return_5d=("forward_return_5d", "mean"),
                avg_forward_return_10d=("forward_return_10d", "mean"),
                avg_forward_return_20d=("forward_return_20d", "mean"),
            )
            .reset_index()
        )

        logger.info(
            "Regime alpha report:\n%s",
            self.regime_report.round(6),
        )

    def build_validation_report(self):
        logger.info("Building alpha validation summary report.")

        ls_returns = self.quantile_returns["long_short_return_1d"].dropna()

        if len(ls_returns) > 1:
            avg_ls_return = ls_returns.mean()
            ls_vol = ls_returns.std()
            sharpe_like = avg_ls_return / ls_vol * np.sqrt(252) if ls_vol != 0 else np.nan
        else:
            avg_ls_return = np.nan
            ls_vol = np.nan
            sharpe_like = np.nan

        max_drawdown = (
            self.equity_curve["drawdown"].min()
            if not self.equity_curve.empty
            else np.nan
        )

        avg_turnover = (
            self.turnover_report["top_book_turnover"].mean()
            if not self.turnover_report.empty
            else np.nan
        )

        self.validation_report = pd.DataFrame(
            [
                {
                    "observations": len(ls_returns),
                    "avg_long_short_return_1d": avg_ls_return,
                    "long_short_volatility": ls_vol,
                    "long_short_sharpe_like": sharpe_like,
                    "max_drawdown": max_drawdown,
                    "hit_ratio": self.hit_ratio,
                    "avg_top_book_turnover": avg_turnover,
                    "avg_rolling_rank_ic_20d": self.rolling_ic[
                        "rolling_rank_ic_20d"
                    ].mean(),
                    "avg_rolling_pearson_ic_20d": self.rolling_ic[
                        "rolling_pearson_ic_20d"
                    ].mean(),
                }
            ]
        )

        logger.info(
            "Validation report:\n%s",
            self.validation_report.round(6),
        )

    def save_outputs(self):
        logger.info("Saving alpha validation outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.validation_report.to_csv(self.validation_report_path, index=False)
        self.quantile_returns.to_csv(self.quantile_returns_path, index=False)
        self.rolling_ic.to_csv(self.rolling_ic_path, index=False)
        self.regime_report.to_csv(self.regime_report_path, index=False)
        self.equity_curve.to_csv(self.equity_curve_path, index=False)
        self.turnover_report.to_csv(self.turnover_path, index=False)

        logger.info("Saved validation report to: %s", self.validation_report_path)
        logger.info("Saved quantile returns to: %s", self.quantile_returns_path)
        logger.info("Saved rolling IC report to: %s", self.rolling_ic_path)
        logger.info("Saved regime alpha report to: %s", self.regime_report_path)
        logger.info("Saved equity curve to: %s", self.equity_curve_path)
        logger.info("Saved turnover report to: %s", self.turnover_path)

    def run(self):
        logger.info("Starting Alpha Validation Engine.")

        self.load_inputs()
        self.reshape_returns()
        self.build_forward_returns()
        self.build_validation_dataset()
        self.build_quantile_portfolios()
        self.build_equity_curve()
        self.compute_rolling_ic()
        self.compute_hit_ratio()
        self.compute_turnover()
        self.build_regime_report()
        self.build_validation_report()
        self.save_outputs()

        logger.info("Alpha Validation Engine completed successfully.")


if __name__ == "__main__":
    engine = AlphaValidationEngine()
    engine.run()