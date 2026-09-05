from pathlib import Path
import logging
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class PortfolioConstructionEngine:
    def __init__(self):
        self.forecast_path = Path("data/forecasting/ensemble_forecast_signals.csv")
        self.hedge_path = Path("data/risk/dynamic_hedging_policy.csv")
        self.tail_risk_path = Path("data/risk/asset_tail_risk_report.csv")

        self.output_dir = Path("data/institutional")
        self.weights_path = self.output_dir / "portfolio_weights.csv"
        self.summary_path = self.output_dir / "portfolio_construction_summary.csv"

    def load_inputs(self):
        logger.info("Loading inputs.")
        self.forecasts = pd.read_csv(self.forecast_path)
        self.hedges = pd.read_csv(self.hedge_path)
        self.tail_risk = pd.read_csv(self.tail_risk_path)

        self.forecasts["Date"] = pd.to_datetime(self.forecasts["Date"])
        self.hedges["Date"] = pd.to_datetime(self.hedges["Date"])

    def build_allocation_dataset(self):
        logger.info("Building allocation dataset.")

        hedge_cols = [
            "Date", "equity_exposure", "bond_hedge_exposure",
            "gold_hedge_exposure", "cash_buffer",
            "hedge_intensity", "hedging_regime_label",
        ]

        tail_cols = [
            "asset",
            "cvar_95_expected_shortfall",
            "max_drawdown",
            "volatility",
        ]

        df = self.forecasts.copy()

        duplicate_hedge_cols = [
            col for col in hedge_cols
            if col != "Date" and col in df.columns
        ]

        duplicate_tail_cols = [
            col for col in tail_cols
            if col != "asset" and col in df.columns
        ]

        df = df.drop(
            columns=duplicate_hedge_cols + duplicate_tail_cols,
            errors="ignore",
        )

        df = df.merge(
            self.hedges[hedge_cols],
            on="Date",
            how="inner",
        )

        df = df.merge(
            self.tail_risk[tail_cols],
            on="asset",
            how="left",
        )

        self.allocation_data = df

        logger.info("Allocation dataset shape: %s", self.allocation_data.shape)
        logger.info("Allocation columns: %s", list(self.allocation_data.columns))

    def compute_raw_scores(self):
        df = self.allocation_data.copy()

        df["risk_adjusted_score"] = (
            df["uncertainty_adjusted_signal"]
            - 0.25 * df["cvar_95_expected_shortfall"].abs()
            - 0.15 * df["max_drawdown"].abs()
            - 0.10 * df["volatility"]
        )

        df["positive_score"] = df["risk_adjusted_score"].clip(lower=0)

        self.scored = df

    def allocate_one_day(self, group):
        group = group.copy()

        assets = group["asset"].tolist()

        caps = {
            "SPY": 0.35,
            "QQQ": 0.35,
            "DIA": 0.35,
            "TLT": 0.35,
            "GLD": 0.35,
            "BTC-USD": 0.04,
            "ETH-USD": 0.04,
            "VIX": 0.05,
            "CASH": 1.00,
        }

        scores = group.set_index("asset")["positive_score"].copy()

        if scores.sum() <= 0:
            raw = pd.Series(1 / len(scores), index=scores.index)
        else:
            raw = scores / scores.sum()

        # Regime exposure overlay.
        equity_exposure = group["equity_exposure"].iloc[0]
        bond_exposure = group["bond_hedge_exposure"].iloc[0]
        gold_exposure = group["gold_hedge_exposure"].iloc[0]
        hedge_exposure = group["hedge_intensity"].iloc[0]
        cash_buffer = group["cash_buffer"].iloc[0]

        multipliers = {}
        for asset in assets:
            if asset in {"SPY", "QQQ", "DIA"}:
                multipliers[asset] = equity_exposure
            elif asset in {"BTC-USD", "ETH-USD"}:
                multipliers[asset] = min(equity_exposure, 0.08)
            elif asset == "TLT":
                multipliers[asset] = bond_exposure
            elif asset == "GLD":
                multipliers[asset] = gold_exposure
            elif asset == "VIX":
                multipliers[asset] = min(hedge_exposure, 0.05)
            else:
                multipliers[asset] = 0.0

        weighted = raw * pd.Series(multipliers)

        if weighted.sum() > 0:
            weights = weighted / weighted.sum() * (1 - cash_buffer)
        else:
            weights = pd.Series(0.0, index=raw.index)

        weights["CASH"] = cash_buffer

        # Hard cap with overflow into CASH only.
        overflow = 0.0
        for asset in list(weights.index):
            cap = caps.get(asset, 0.35)
            if weights[asset] > cap:
                overflow += weights[asset] - cap
                weights[asset] = cap

        weights["CASH"] = min(weights.get("CASH", 0.0) + overflow, 1.0)

        # If total below 1, add remainder to CASH.
        remainder = 1.0 - weights.sum()
        if remainder > 0:
            weights["CASH"] += remainder

        # If CASH somehow exceeds 1, normalize defensive assets not caps.
        total = weights.sum()
        if total != 1.0 and total > 0:
            weights = weights / total

        # Final hard safety check.
        for asset, weight in weights.items():
            cap = caps.get(asset, 0.35)
            if weight > cap + 1e-8:
                raise ValueError(f"Cap violation: {asset} weight={weight:.6f}, cap={cap:.6f}")

        output_rows = []

        for _, row in group.iterrows():
            asset = row["asset"]
            row = row.copy()
            row["raw_weight"] = raw.get(asset, 0.0)
            row["constrained_weight"] = weighted.get(asset, 0.0)
            row["final_weight"] = weights.get(asset, 0.0)
            output_rows.append(row)

        cash_row = group.iloc[0].copy()
        cash_row["asset"] = "CASH"
        cash_row["uncertainty_adjusted_signal"] = 0.0
        cash_row["risk_adjusted_score"] = 0.0
        cash_row["raw_weight"] = 0.0
        cash_row["constrained_weight"] = 0.0
        cash_row["final_weight"] = weights.get("CASH", 0.0)
        output_rows.append(cash_row)

        return pd.DataFrame(output_rows)

    def apply_institutional_constraints(self):
        logger.info("Applying institutional hard-cap allocator.")

        daily = []

        for _, group in self.scored.groupby("Date"):
            daily.append(self.allocate_one_day(group))

        self.weights = pd.concat(daily, ignore_index=True)

        logger.info("Weight preview:\n%s", self.weights.tail())

    def build_summary(self):
        self.summary = (
            self.weights
            .groupby("asset")
            .agg(
                avg_weight=("final_weight", "mean"),
                max_weight=("final_weight", "max"),
                min_weight=("final_weight", "min"),
                avg_signal=("uncertainty_adjusted_signal", "mean"),
                avg_risk_adjusted_score=("risk_adjusted_score", "mean"),
            )
            .reset_index()
            .sort_values("avg_weight", ascending=False)
        )

        logger.info("Summary:\n%s", self.summary.round(4))

    def save_outputs(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        keep_cols = [
            "Date", "asset", "uncertainty_adjusted_signal",
            "risk_adjusted_score", "raw_weight",
            "constrained_weight", "final_weight",
            "hedging_regime_label",
        ]

        self.weights[keep_cols].to_csv(self.weights_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved weights to: %s", self.weights_path)
        logger.info("Saved summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Portfolio Construction Engine.")
        self.load_inputs()
        self.build_allocation_dataset()
        self.compute_raw_scores()
        self.apply_institutional_constraints()
        self.build_summary()
        self.save_outputs()
        logger.info("Portfolio Construction Engine completed successfully.")


if __name__ == "__main__":
    engine = PortfolioConstructionEngine()
    engine.run()