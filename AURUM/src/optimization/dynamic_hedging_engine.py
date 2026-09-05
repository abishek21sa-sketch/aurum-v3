from pathlib import Path
import pandas as pd
import numpy as np


class DynamicHedgingEngine:
    def __init__(
        self,
        returns_path="data/market_matrix/market_return_matrix.csv",
        output_path="results/optimization/dynamic_hedging_report.csv",
        target_vol=0.12,
        max_leverage=1.25,
        min_exposure=0.25,
        drawdown_limit=-0.08,
    ):
        self.returns_path = Path(returns_path)
        self.output_path = Path(output_path)
        self.target_vol = target_vol
        self.max_leverage = max_leverage
        self.min_exposure = min_exposure
        self.drawdown_limit = drawdown_limit

    def load_returns(self):
        if not self.returns_path.exists():
            raise FileNotFoundError(f"Missing returns file: {self.returns_path}")

        returns = pd.read_csv(self.returns_path)

        if "Date" in returns.columns:
            returns["Date"] = pd.to_datetime(returns["Date"])
            returns = returns.set_index("Date")

        return returns.select_dtypes(include=[np.number]).dropna()

    def compute_portfolio_return(self, returns):
        weights = np.repeat(1 / returns.shape[1], returns.shape[1])
        return returns @ weights

    def compute_volatility_scaler(self, portfolio_returns):
        rolling_vol = portfolio_returns.rolling(21).std() * np.sqrt(252)
        scaler = self.target_vol / rolling_vol
        scaler = scaler.clip(self.min_exposure, self.max_leverage)
        return scaler.fillna(1.0)

    def compute_drawdown_scaler(self, portfolio_returns):
        cumulative = (1 + portfolio_returns).cumprod()
        peak = cumulative.cummax()
        drawdown = cumulative / peak - 1

        scaler = pd.Series(1.0, index=portfolio_returns.index)
        scaler[drawdown < self.drawdown_limit] = 0.5
        scaler[drawdown < self.drawdown_limit * 1.5] = 0.35

        return scaler, drawdown

    def compute_hedged_returns(self, returns, exposure):
        risky_assets = [c for c in returns.columns if c not in ["TLT", "GLD", "VIX"]]
        defensive_assets = [c for c in returns.columns if c in ["TLT", "GLD"]]

        risky_return = returns[risky_assets].mean(axis=1)

        if defensive_assets:
            defensive_return = returns[defensive_assets].mean(axis=1)
        else:
            defensive_return = pd.Series(0.0, index=returns.index)

        hedged_return = exposure * risky_return + (1 - exposure) * defensive_return
        return hedged_return

    def run(self):
        returns = self.load_returns()

        base_portfolio_return = self.compute_portfolio_return(returns)

        vol_scaler = self.compute_volatility_scaler(base_portfolio_return)
        dd_scaler, drawdown = self.compute_drawdown_scaler(base_portfolio_return)

        final_exposure = (vol_scaler * dd_scaler).clip(
            self.min_exposure, self.max_leverage
        )

        hedged_return = self.compute_hedged_returns(returns, final_exposure)

        report = pd.DataFrame({
            "base_portfolio_return": base_portfolio_return,
            "rolling_vol_scaler": vol_scaler,
            "drawdown": drawdown,
            "drawdown_scaler": dd_scaler,
            "final_exposure": final_exposure,
            "hedged_return": hedged_return,
        })

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(self.output_path)

        print("DYNAMIC HEDGING ENGINE COMPLETE")
        print("=" * 60)
        print(f"Saved report: {self.output_path}")
        print(f"Average exposure: {final_exposure.mean():.4f}")
        print(f"Minimum exposure: {final_exposure.min():.4f}")
        print(f"Maximum exposure: {final_exposure.max():.4f}")
        print(f"Base cumulative return: {(1 + base_portfolio_return).prod() - 1:.4f}")
        print(f"Hedged cumulative return: {(1 + hedged_return).prod() - 1:.4f}")
        print(f"Base max drawdown: {drawdown.min():.4f}")

        hedged_cum = (1 + hedged_return).cumprod()
        hedged_dd = hedged_cum / hedged_cum.cummax() - 1
        print(f"Hedged max drawdown: {hedged_dd.min():.4f}")

        return report


if __name__ == "__main__":
    engine = DynamicHedgingEngine()
    engine.run()