from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class TailRiskEngine:
    """
    AURUM Tail Risk Engine v3.

    Uses actual institutional portfolio returns for main portfolio tail risk:
    - net_portfolio_return
    - gross_portfolio_return

    Also preserves research diagnostics:
    - regime-conditioned tail risk
    - asset-level tail risk
    - tail dependence
    """

    def __init__(self):
        self.portfolio_backtest_path = Path(
            "data/institutional/portfolio_backtest_results.csv"
        )
        self.return_matrix_path = Path("data/market_matrix/market_return_matrix.csv")
        self.regime_path = Path("data/regimes/calibrated_regime_probabilities.csv")

        self.data_output_dir = Path("data/risk")
        self.results_output_dir = Path("results/risk")

        self.tail_report_path = self.results_output_dir / "tail_risk_report.csv"
        self.asset_report_path = self.results_output_dir / "asset_tail_risk_report.csv"
        self.tail_dependence_path = self.results_output_dir / "tail_dependence_report.csv"

    def load_inputs(self):
        logger.info("Loading institutional portfolio backtest from: %s", self.portfolio_backtest_path)
        self.portfolio = pd.read_csv(self.portfolio_backtest_path)
        self.portfolio["Date"] = pd.to_datetime(self.portfolio["Date"])

        logger.info("Loading asset return matrix from: %s", self.return_matrix_path)
        self.returns = pd.read_csv(self.return_matrix_path)
        self.returns["Date"] = pd.to_datetime(self.returns["Date"])

        logger.info("Loading calibrated regimes from: %s", self.regime_path)
        self.regimes = pd.read_csv(self.regime_path)
        self.regimes["Date"] = pd.to_datetime(self.regimes["Date"])

        self.asset_cols = [col for col in self.returns.columns if col != "Date"]

    def compute_tail_metrics(self, series: pd.Series) -> dict:
        series = series.dropna()

        if series.empty:
            return {
                "observations": 0,
                "var_95": np.nan,
                "var_99": np.nan,
                "cvar_95_expected_shortfall": np.nan,
                "cvar_99_expected_shortfall": np.nan,
                "downside_semivariance": np.nan,
                "max_drawdown": np.nan,
                "mean_return": np.nan,
                "volatility": np.nan,
            }

        var_95 = np.percentile(series, 5)
        var_99 = np.percentile(series, 1)

        cvar_95 = series[series <= var_95].mean()
        cvar_99 = series[series <= var_99].mean()

        downside = series[series < 0]
        downside_semivariance = np.mean(np.square(downside)) if len(downside) else 0.0

        cumulative = (1 + series).cumprod()
        drawdown = cumulative / cumulative.cummax() - 1

        return {
            "observations": len(series),
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95_expected_shortfall": cvar_95,
            "cvar_99_expected_shortfall": cvar_99,
            "downside_semivariance": downside_semivariance,
            "max_drawdown": drawdown.min(),
            "mean_return": series.mean(),
            "volatility": series.std(),
        }

    def build_portfolio_tail_risk(self):
        logger.info("Building portfolio tail risk from institutional backtest returns.")

        rows = []

        for col, label in [
            ("gross_portfolio_return", "portfolio_gross"),
            ("net_portfolio_return", "portfolio_net"),
        ]:
            metrics = self.compute_tail_metrics(self.portfolio[col])
            metrics["segment"] = label
            metrics["source"] = str(self.portfolio_backtest_path)
            rows.append(metrics)

        self.portfolio_tail_report = pd.DataFrame(rows)

    def build_regime_conditioned_tail_risk(self):
        logger.info("Building regime-conditioned tail risk using net portfolio returns.")

        merged = self.portfolio[["Date", "net_portfolio_return"]].merge(
            self.regimes[
                [
                    "Date",
                    "calibrated_most_likely_state",
                    "calibrated_regime_confidence",
                ]
            ],
            on="Date",
            how="inner",
        )

        rows = []

        for state in sorted(merged["calibrated_most_likely_state"].dropna().unique()):
            subset = merged[merged["calibrated_most_likely_state"] == state]

            metrics = self.compute_tail_metrics(subset["net_portfolio_return"])
            metrics["segment"] = f"regime_state_{state}"
            metrics["source"] = "net_portfolio_return"
            metrics["avg_regime_confidence"] = subset[
                "calibrated_regime_confidence"
            ].mean()

            rows.append(metrics)

        self.regime_tail_report = pd.DataFrame(rows)

    def build_asset_level_tail_risk(self):
        logger.info("Building asset-level tail risk diagnostics.")

        rows = []

        for asset in self.asset_cols:
            metrics = self.compute_tail_metrics(self.returns[asset])
            metrics["asset"] = asset
            rows.append(metrics)

        self.asset_report = pd.DataFrame(rows)

    def build_tail_dependence_report(self):
        logger.info("Building tail dependence diagnostics.")

        rows = []
        threshold = 0.05

        for i, asset_a in enumerate(self.asset_cols):
            for asset_b in self.asset_cols[i + 1:]:
                pair = self.returns[[asset_a, asset_b]].dropna()

                if len(pair) < 30:
                    continue

                a_tail = pair[asset_a] <= pair[asset_a].quantile(threshold)
                b_tail = pair[asset_b] <= pair[asset_b].quantile(threshold)

                rows.append(
                    {
                        "asset_a": asset_a,
                        "asset_b": asset_b,
                        "joint_tail_probability": (a_tail & b_tail).mean(),
                    }
                )

        self.tail_dependence_report = pd.DataFrame(rows).sort_values(
            "joint_tail_probability",
            ascending=False,
        )

    def save_outputs(self):
        logger.info("Saving tail risk outputs.")

        self.data_output_dir.mkdir(parents=True, exist_ok=True)
        self.results_output_dir.mkdir(parents=True, exist_ok=True)

        final_report = pd.concat(
            [
                self.portfolio_tail_report,
                self.regime_tail_report,
            ],
            ignore_index=True,
        )

        final_report.to_csv(self.tail_report_path, index=False)
        self.asset_report.to_csv(self.asset_report_path, index=False)
        self.tail_dependence_report.to_csv(self.tail_dependence_path, index=False)

        # Mirror to data/risk for backward compatibility
        final_report.to_csv(self.data_output_dir / "tail_risk_report.csv", index=False)
        self.asset_report.to_csv(self.data_output_dir / "asset_tail_risk_report.csv", index=False)
        self.tail_dependence_report.to_csv(
            self.data_output_dir / "tail_dependence_report.csv",
            index=False,
        )

        logger.info("Saved main tail risk report to: %s", self.tail_report_path)
        logger.info("Saved asset tail risk report to: %s", self.asset_report_path)
        logger.info("Saved tail dependence report to: %s", self.tail_dependence_path)

    def run(self):
        logger.info("Starting AURUM Tail Risk Engine v3.")

        self.load_inputs()
        self.build_portfolio_tail_risk()
        self.build_regime_conditioned_tail_risk()
        self.build_asset_level_tail_risk()
        self.build_tail_dependence_report()
        self.save_outputs()

        logger.info("Tail Risk Engine v3 completed successfully.")


if __name__ == "__main__":
    engine = TailRiskEngine()
    engine.run()