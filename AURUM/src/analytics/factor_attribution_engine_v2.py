from pathlib import Path
import numpy as np
import pandas as pd


class FactorAttributionEngineV2:
    def __init__(
        self,
        strategy_returns_path="data/backtesting/meta_strategy_backtest.csv",
        market_returns_path="data/market_matrix/market_return_matrix.csv",
        output_path="data/analytics/factor_attribution_v2.csv",
        summary_path="data/analytics/factor_attribution_summary_v2.csv",
    ):
        self.strategy_returns_path = Path(strategy_returns_path)
        self.market_returns_path = Path(market_returns_path)
        self.output_path = Path(output_path)
        self.summary_path = Path(summary_path)

    def run(self):
        strategy = pd.read_csv(self.strategy_returns_path)
        market = pd.read_csv(self.market_returns_path)

        strategy["Date"] = pd.to_datetime(strategy["Date"])
        market["Date"] = pd.to_datetime(market["Date"])

        df = strategy.merge(market, on="Date", how="inner")

        factors = {
            "equity_beta": ["SPY", "QQQ", "DIA"],
            "defensive_bond": ["TLT"],
            "gold_hedge": ["GLD"],
            "crypto_beta": ["BTC-USD", "ETH-USD"],
            "volatility_hedge": ["VIX"],
        }

        rows = []

        target = df["meta_return"]

        for factor_name, assets in factors.items():
            available = [a for a in assets if a in df.columns]

            if not available:
                continue

            factor_return = df[available].mean(axis=1)

            beta = np.cov(target, factor_return)[0, 1] / (
                np.var(factor_return) + 1e-8
            )

            correlation = target.corr(factor_return)

            contribution = beta * factor_return.mean() * 252

            rows.append({
                "factor": factor_name,
                "assets": ",".join(available),
                "beta": beta,
                "correlation": correlation,
                "annualized_factor_return": factor_return.mean() * 252,
                "estimated_return_contribution": contribution,
                "factor_volatility": factor_return.std() * np.sqrt(252),
            })

        attribution = pd.DataFrame(rows)

        diversification_score = 1 - attribution["correlation"].abs().mean()

        summary = pd.DataFrame([{
            "strategy": "meta_strategy",
            "observations": len(df),
            "strategy_total_return": df["equity_curve"].iloc[-1] - 1,
            "strategy_volatility": target.std() * np.sqrt(252),
            "avg_abs_factor_correlation": attribution["correlation"].abs().mean(),
            "factor_diversification_score": diversification_score,
            "dominant_factor": attribution.sort_values(
                "correlation",
                key=lambda s: s.abs(),
                ascending=False,
            ).iloc[0]["factor"],
        }])

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        attribution.to_csv(self.output_path, index=False)
        summary.to_csv(self.summary_path, index=False)

        print("FACTOR ATTRIBUTION ENGINE V2 COMPLETE")
        print("=" * 70)
        print(attribution.to_string(index=False))
        print()
        print(summary.to_string(index=False))
        print()
        print(f"Saved attribution: {self.output_path}")
        print(f"Saved summary: {self.summary_path}")

        return attribution, summary


if __name__ == "__main__":
    engine = FactorAttributionEngineV2()
    engine.run()