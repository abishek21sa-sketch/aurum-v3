from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class TransactionCostEngine:
    """
    Institutional Transaction Cost Engine for AURUM.

    Models:
    - daily portfolio turnover
    - gross vs net long-short returns
    - fixed transaction cost in basis points
    - cost drag
    - net Sharpe-like performance
    - execution realism diagnostics
    """

    def __init__(self, cost_bps: float = 10.0):
        self.cost_bps = cost_bps
        self.cost_rate = cost_bps / 10000

        self.quantile_path = Path("data/validation/alpha_quantile_returns.csv")
        self.turnover_path = Path("data/validation/alpha_turnover_report.csv")

        self.output_dir = Path("data/validation")
        self.net_return_path = self.output_dir / "transaction_cost_adjusted_returns.csv"
        self.summary_path = self.output_dir / "transaction_cost_summary.csv"

    def load_inputs(self):
        logger.info("Loading quantile returns from: %s", self.quantile_path)
        logger.info("Loading turnover report from: %s", self.turnover_path)

        self.quantile_returns = pd.read_csv(self.quantile_path)
        self.turnover = pd.read_csv(self.turnover_path)

        self.quantile_returns["Date"] = pd.to_datetime(self.quantile_returns["Date"])
        self.turnover["Date"] = pd.to_datetime(self.turnover["Date"])

        logger.info("Loaded quantile returns shape: %s", self.quantile_returns.shape)
        logger.info("Loaded turnover shape: %s", self.turnover.shape)

    def build_cost_adjusted_returns(self):
        logger.info("Building transaction-cost-adjusted return series.")

        df = self.quantile_returns.merge(
            self.turnover[["Date", "top_book_turnover"]],
            on="Date",
            how="left",
        )

        df["top_book_turnover"] = df["top_book_turnover"].fillna(0)

        # Long-short book approximation:
        # top book turnover + bottom/rebalance friction proxy
        df["estimated_total_turnover"] = 2.0 * df["top_book_turnover"]

        df["transaction_cost"] = (
            df["estimated_total_turnover"] * self.cost_rate
        )

        df["gross_long_short_return_1d"] = df["long_short_return_1d"]

        df["net_long_short_return_1d"] = (
            df["gross_long_short_return_1d"] - df["transaction_cost"]
        )

        df["gross_equity_curve"] = (
            1 + df["gross_long_short_return_1d"].fillna(0)
        ).cumprod()

        df["net_equity_curve"] = (
            1 + df["net_long_short_return_1d"].fillna(0)
        ).cumprod()

        df["gross_running_peak"] = df["gross_equity_curve"].cummax()
        df["net_running_peak"] = df["net_equity_curve"].cummax()

        df["gross_drawdown"] = (
            df["gross_equity_curve"] / df["gross_running_peak"] - 1
        )

        df["net_drawdown"] = (
            df["net_equity_curve"] / df["net_running_peak"] - 1
        )

        self.cost_adjusted_returns = df

        logger.info(
            "Transaction cost adjusted preview:\n%s",
            self.cost_adjusted_returns.tail(),
        )

    def build_summary(self):
        logger.info("Building transaction cost summary.")

        gross = self.cost_adjusted_returns["gross_long_short_return_1d"].dropna()
        net = self.cost_adjusted_returns["net_long_short_return_1d"].dropna()

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
                    "transaction_cost_bps": self.cost_bps,
                    "observations": len(net),
                    "avg_daily_turnover": self.cost_adjusted_returns[
                        "estimated_total_turnover"
                    ].mean(),
                    "avg_daily_transaction_cost": self.cost_adjusted_returns[
                        "transaction_cost"
                    ].mean(),
                    "gross_avg_daily_return": gross.mean(),
                    "net_avg_daily_return": net.mean(),
                    "gross_sharpe_like": gross_sharpe,
                    "net_sharpe_like": net_sharpe,
                    "gross_max_drawdown": self.cost_adjusted_returns[
                        "gross_drawdown"
                    ].min(),
                    "net_max_drawdown": self.cost_adjusted_returns[
                        "net_drawdown"
                    ].min(),
                    "total_cost_drag": (
                        self.cost_adjusted_returns["gross_equity_curve"].iloc[-1]
                        - self.cost_adjusted_returns["net_equity_curve"].iloc[-1]
                    ),
                    "gross_terminal_equity": self.cost_adjusted_returns[
                        "gross_equity_curve"
                    ].iloc[-1],
                    "net_terminal_equity": self.cost_adjusted_returns[
                        "net_equity_curve"
                    ].iloc[-1],
                }
            ]
        )

        logger.info(
            "Transaction cost summary:\n%s",
            self.summary.round(6),
        )

    def save_outputs(self):
        logger.info("Saving transaction cost outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.cost_adjusted_returns.to_csv(self.net_return_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved adjusted returns to: %s", self.net_return_path)
        logger.info("Saved transaction cost summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Transaction Cost Engine.")

        self.load_inputs()
        self.build_cost_adjusted_returns()
        self.build_summary()
        self.save_outputs()

        logger.info("Transaction Cost Engine completed successfully.")


if __name__ == "__main__":
    engine = TransactionCostEngine(cost_bps=10.0)
    engine.run()