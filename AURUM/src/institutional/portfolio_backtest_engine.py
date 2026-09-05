from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class PortfolioBacktestEngine:
    """
    Institutional Portfolio Backtest Engine for AURUM.

    Tests:
    - final allocator weights
    - realized next-day portfolio returns
    - turnover
    - transaction-cost-adjusted returns
    - drawdown
    - Sharpe-like performance
    - cash utilization
    """

    def __init__(self, transaction_cost_bps: float = 10.0):
        self.transaction_cost_bps = transaction_cost_bps
        self.transaction_cost_rate = transaction_cost_bps / 10000

        self.weights_path = Path("data/institutional/portfolio_weights.csv")
        self.returns_path = Path("data/market_matrix/market_return_matrix.csv")

        self.output_dir = Path("data/institutional")
        self.backtest_path = self.output_dir / "portfolio_backtest_results.csv"
        self.summary_path = self.output_dir / "portfolio_backtest_summary.csv"
        self.exposure_path = self.output_dir / "portfolio_exposure_summary.csv"

    def load_inputs(self):
        logger.info("Loading portfolio weights from: %s", self.weights_path)
        logger.info("Loading return matrix from: %s", self.returns_path)

        self.weights = pd.read_csv(self.weights_path)
        self.returns = pd.read_csv(self.returns_path)

        self.weights["Date"] = pd.to_datetime(self.weights["Date"])
        self.returns["Date"] = pd.to_datetime(self.returns["Date"])

        logger.info("Loaded weights shape: %s", self.weights.shape)
        logger.info("Loaded returns shape: %s", self.returns.shape)

    def reshape_returns(self):
        logger.info("Reshaping returns.")

        self.long_returns = self.returns.melt(
            id_vars="Date",
            var_name="asset",
            value_name="daily_return",
        )

        self.long_returns = self.long_returns.sort_values(["asset", "Date"])
        self.long_returns["forward_return_1d"] = (
            self.long_returns.groupby("asset")["daily_return"].shift(-1)
        )

        cash_dates = self.returns[["Date"]].copy()
        cash_dates["asset"] = "CASH"
        cash_dates["forward_return_1d"] = 0.0

        self.forward_returns = pd.concat(
            [
                self.long_returns[["Date", "asset", "forward_return_1d"]],
                cash_dates,
            ],
            ignore_index=True,
        )

        logger.info("Forward returns shape: %s", self.forward_returns.shape)

    def compute_weight_turnover(self):
        logger.info("Computing portfolio turnover.")

        weights_wide = (
            self.weights
            .pivot_table(
                index="Date",
                columns="asset",
                values="final_weight",
                aggfunc="sum",
            )
            .fillna(0)
            .sort_index()
        )

        turnover = weights_wide.diff().abs().sum(axis=1) / 2
        turnover.iloc[0] = 0.0

        self.turnover = turnover.reset_index()
        self.turnover.columns = ["Date", "portfolio_turnover"]

        logger.info("Turnover preview:\n%s", self.turnover.tail())

    def run_backtest(self):
        logger.info("Running portfolio backtest.")

        merged = self.weights.merge(
            self.forward_returns,
            on=["Date", "asset"],
            how="left",
        )

        merged["forward_return_1d"] = merged["forward_return_1d"].fillna(0.0)
        merged["weighted_return"] = merged["final_weight"] * merged["forward_return_1d"]

        daily = (
            merged
            .groupby("Date")
            .agg(
                gross_portfolio_return=("weighted_return", "sum"),
                gross_exposure=("final_weight", "sum"),
                cash_weight=("final_weight", lambda x: merged.loc[x.index].loc[merged.loc[x.index, "asset"] == "CASH", "final_weight"].sum()),
            )
            .reset_index()
            .sort_values("Date")
        )

        daily = daily.merge(self.turnover, on="Date", how="left")
        daily["portfolio_turnover"] = daily["portfolio_turnover"].fillna(0.0)

        daily["transaction_cost"] = (
            daily["portfolio_turnover"] * self.transaction_cost_rate
        )

        daily["net_portfolio_return"] = (
            daily["gross_portfolio_return"] - daily["transaction_cost"]
        )

        daily["gross_equity_curve"] = (
            1 + daily["gross_portfolio_return"]
        ).cumprod()

        daily["net_equity_curve"] = (
            1 + daily["net_portfolio_return"]
        ).cumprod()

        daily["gross_running_peak"] = daily["gross_equity_curve"].cummax()
        daily["net_running_peak"] = daily["net_equity_curve"].cummax()

        daily["gross_drawdown"] = (
            daily["gross_equity_curve"] / daily["gross_running_peak"] - 1
        )

        daily["net_drawdown"] = (
            daily["net_equity_curve"] / daily["net_running_peak"] - 1
        )

        self.backtest = daily

        logger.info("Backtest preview:\n%s", self.backtest.tail())

    def build_summary(self):
        logger.info("Building portfolio backtest summary.")

        gross = self.backtest["gross_portfolio_return"].dropna()
        net = self.backtest["net_portfolio_return"].dropna()

        gross_sharpe = (
            gross.mean() / gross.std() * np.sqrt(252)
            if gross.std() != 0
            else np.nan
        )

        net_sharpe = (
            net.mean() / net.std() * np.sqrt(252)
            if net.std() != 0
            else np.nan
        )

        self.summary = pd.DataFrame(
            [
                {
                    "observations": len(net),
                    "transaction_cost_bps": self.transaction_cost_bps,
                    "gross_avg_daily_return": gross.mean(),
                    "net_avg_daily_return": net.mean(),
                    "gross_volatility": gross.std(),
                    "net_volatility": net.std(),
                    "gross_sharpe_like": gross_sharpe,
                    "net_sharpe_like": net_sharpe,
                    "gross_max_drawdown": self.backtest["gross_drawdown"].min(),
                    "net_max_drawdown": self.backtest["net_drawdown"].min(),
                    "avg_turnover": self.backtest["portfolio_turnover"].mean(),
                    "avg_cash_weight": self.backtest["cash_weight"].mean(),
                    "gross_terminal_equity": self.backtest["gross_equity_curve"].iloc[-1],
                    "net_terminal_equity": self.backtest["net_equity_curve"].iloc[-1],
                }
            ]
        )

        logger.info("Backtest summary:\n%s", self.summary.round(6))

    def build_exposure_summary(self):
        logger.info("Building exposure summary.")

        self.exposure_summary = (
            self.weights
            .groupby("asset")
            .agg(
                avg_weight=("final_weight", "mean"),
                max_weight=("final_weight", "max"),
                min_weight=("final_weight", "min"),
            )
            .reset_index()
            .sort_values("avg_weight", ascending=False)
        )

        logger.info("Exposure summary:\n%s", self.exposure_summary.round(4))

    def save_outputs(self):
        logger.info("Saving portfolio backtest outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.backtest.to_csv(self.backtest_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)
        self.exposure_summary.to_csv(self.exposure_path, index=False)

        logger.info("Saved backtest results to: %s", self.backtest_path)
        logger.info("Saved backtest summary to: %s", self.summary_path)
        logger.info("Saved exposure summary to: %s", self.exposure_path)

    def run(self):
        logger.info("Starting Portfolio Backtest Engine.")

        self.load_inputs()
        self.reshape_returns()
        self.compute_weight_turnover()
        self.run_backtest()
        self.build_summary()
        self.build_exposure_summary()
        self.save_outputs()

        logger.info("Portfolio Backtest Engine completed successfully.")


if __name__ == "__main__":
    engine = PortfolioBacktestEngine(transaction_cost_bps=10.0)
    engine.run()