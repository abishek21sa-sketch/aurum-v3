import pandas as pd
from pathlib import Path


class PortfolioHealthMonitor:

    def __init__(self):
        self.backtest_path = Path("data/backtesting")
        self.regime_path = Path("data/regimes")
        self.analytics_path = Path("data/analytics")
        self.output_path = Path("results/reports")

    def load_inputs(self):
        dynamic = pd.read_csv(
            self.backtest_path / "dynamic_allocation_transaction_cost.csv"
        )

        stability = pd.read_csv(
            self.regime_path / "regime_stability.csv"
        )

        factor = pd.read_csv(
            self.analytics_path / "rolling_factor_exposure.csv"
        )

        dynamic["Date"] = pd.to_datetime(dynamic["Date"])
        stability["Date"] = pd.to_datetime(stability["Date"])
        factor["Date"] = pd.to_datetime(factor["Date"])

        return dynamic, stability, factor

    def evaluate_health(self, dynamic, stability, factor):
        latest_dynamic = dynamic.iloc[-1]
        latest_stability = stability.iloc[-1]
        latest_factor = factor.iloc[-1]

        net_return = latest_dynamic["net_cumulative_return"]
        max_drawdown = dynamic["net_drawdown"].min()
        instability = latest_stability["instability_score"]
        beta = latest_factor["portfolio_beta_to_spy"]

        risk_flags = []

        if max_drawdown < -0.10:
            risk_flags.append("Drawdown risk elevated")

        if instability > 0.50:
            risk_flags.append("Regime instability elevated")

        if beta > 0.50:
            risk_flags.append("Equity beta exposure elevated")

        if not risk_flags:
            health_status = "HEALTHY"
        elif len(risk_flags) <= 2:
            health_status = "WATCH"
        else:
            health_status = "RISK-OFF"

        report = f"""
PORTFOLIO HEALTH MONITOR
========================

Latest Portfolio State
----------------------
Net Cumulative Return: {net_return:.4f}
Maximum Net Drawdown: {max_drawdown:.4f}
Latest Regime Instability Score: {instability:.4f}
Latest Portfolio Beta to SPY: {beta:.4f}

Health Status:
{health_status}

Risk Flags:
{risk_flags if risk_flags else "None"}

Interpretation:
The portfolio health monitor combines drawdown, regime instability, and market beta exposure into a single operational risk view. This acts as a control-tower layer for the allocation system.
"""

        return report

    def save_report(self, report):
        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "portfolio_health_monitor.txt"

        with open(output_file, "w") as f:
            f.write(report)

        print(report)
        print(f"\nSaved health monitor report: {output_file}")

    def run(self):
        print("=" * 60)
        print("PORTFOLIO HEALTH MONITOR")
        print("=" * 60)

        dynamic, stability, factor = self.load_inputs()

        report = self.evaluate_health(dynamic, stability, factor)

        self.save_report(report)


if __name__ == "__main__":
    monitor = PortfolioHealthMonitor()
    monitor.run()
