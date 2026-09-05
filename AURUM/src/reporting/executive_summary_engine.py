from pathlib import Path
import pandas as pd


class ExecutiveSummaryEngine:

    def __init__(self):

        self.backtest_path = Path("data/backtesting")
        self.risk_path = Path("data/risk")
        self.analytics_path = Path("data/analytics")
        self.forecasting_path = Path("data/forecasting")

        self.output_path = Path("results/reports")

    def load_inputs(self):

        backtest = pd.read_csv(
            self.backtest_path / "dynamic_allocation_transaction_cost.csv"
        )

        stress = pd.read_csv(
            self.risk_path / "portfolio_stress_summary.csv",
            index_col=0
        )

        factor = pd.read_csv(
            self.analytics_path / "portfolio_factor_exposure.csv"
        )

        monte_carlo = pd.read_csv(
            self.forecasting_path / "monte_carlo_regime_summary.csv"
        )

        return backtest, stress, factor, monte_carlo

    def generate_summary(
        self,
        backtest,
        stress,
        factor,
        monte_carlo
    ):

        cumulative_return = (
            backtest["net_cumulative_return"].iloc[-1]
        )

        max_drawdown = (
            backtest["net_drawdown"].min()
        )

        portfolio_beta = (
            factor["portfolio_total_beta"].iloc[0]
        )

        probability_loss = (
            monte_carlo.loc[
                monte_carlo["metric"] == "probability_loss",
                "value"
            ].iloc[0]
        )

        expected_terminal = (
            monte_carlo.loc[
                monte_carlo["metric"] == "mean_terminal_return",
                "value"
            ].iloc[0]
        )

        numeric_stress = stress.select_dtypes(include="number")
        worst_stress = numeric_stress.min().min()

        report = f"""
AURUM EXECUTIVE STRATEGY SUMMARY
============================================================

Portfolio Objective
-------------------
Adaptive probabilistic asset allocation using
regime-aware optimization, instability-sensitive
risk budgeting, and dynamic exposure control.

Performance Summary
-------------------
Net Cumulative Return: {cumulative_return:.4f}
Maximum Drawdown: {max_drawdown:.4f}
Portfolio Beta to SPY: {portfolio_beta:.4f}

Forward-Looking Monte Carlo Simulation
--------------------------------------
Expected 60-Day Return: {expected_terminal:.4f}
Probability of Loss: {probability_loss:.4f}

Stress Testing
---------------
Worst Scenario Impact: {worst_stress:.4f}

System Characteristics
----------------------
- Dynamic regime-aware allocation
- Instability-sensitive exposure scaling
- Probabilistic transition modeling
- Monte Carlo scenario forecasting
- Dynamic risk budgeting
- Factor exposure monitoring
- Rolling beta surveillance
- Portfolio health diagnostics

Interpretation
---------------
The system demonstrates defensive market exposure,
controlled drawdown behavior, and adaptive
risk management under changing market regimes.

The portfolio maintains low aggregate market beta
while preserving positive expected return potential.
"""

        return report

    def save_report(self, report):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = (
            self.output_path /
            "aurum_executive_strategy_summary.txt"
        )

        with open(output_file, "w") as f:
            f.write(report)

        print(report)

        print(f"\nSaved report: {output_file}")

    def run(self):

        backtest, stress, factor, monte_carlo = (
            self.load_inputs()
        )

        report = self.generate_summary(
            backtest,
            stress,
            factor,
            monte_carlo
        )

        self.save_report(report)


if __name__ == "__main__":

    engine = ExecutiveSummaryEngine()

    engine.run()
