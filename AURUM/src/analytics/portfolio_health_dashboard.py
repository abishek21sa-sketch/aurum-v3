import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class PortfolioHealthDashboard:

    def __init__(self):
        self.backtest_path = Path("data/backtesting")
        self.regime_path = Path("data/regimes")
        self.analytics_path = Path("data/analytics")
        self.output_path = Path("results/figures")

    def load_inputs(self):
        dynamic = pd.read_csv(self.backtest_path / "dynamic_allocation_transaction_cost.csv")
        stability = pd.read_csv(self.regime_path / "regime_stability.csv")
        factor = pd.read_csv(self.analytics_path / "rolling_factor_exposure.csv")

        dynamic["Date"] = pd.to_datetime(dynamic["Date"])
        stability["Date"] = pd.to_datetime(stability["Date"])
        factor["Date"] = pd.to_datetime(factor["Date"])

        return dynamic, stability, factor

    def plot_health_dashboard(self, dynamic, stability, factor):
        self.output_path.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

        axes[0].plot(dynamic["Date"], dynamic["net_cumulative_return"])
        axes[0].set_title("Net Cumulative Return")
        axes[0].set_ylabel("Return")
        axes[0].grid(True)

        axes[1].plot(dynamic["Date"], dynamic["net_drawdown"])
        axes[1].set_title("Net Drawdown")
        axes[1].set_ylabel("Drawdown")
        axes[1].grid(True)

        axes[2].plot(stability["Date"], stability["instability_score"])
        axes[2].set_title("Regime Instability Score")
        axes[2].set_ylabel("Instability")
        axes[2].grid(True)

        axes[3].plot(factor["Date"], factor["portfolio_beta_to_spy"])
        axes[3].set_title("Portfolio Beta to SPY")
        axes[3].set_ylabel("Beta")
        axes[3].set_xlabel("Date")
        axes[3].grid(True)

        plt.tight_layout()

        output_file = self.output_path / "portfolio_health_dashboard.png"
        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved health dashboard: {output_file}")

        plt.show()

    def run(self):
        dynamic, stability, factor = self.load_inputs()
        self.plot_health_dashboard(dynamic, stability, factor)


if __name__ == "__main__":
    dashboard = PortfolioHealthDashboard()
    dashboard.run()
