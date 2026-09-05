from pathlib import Path
import numpy as np
import pandas as pd


class BlackLittermanAllocator:
    def __init__(
        self,
        returns_path="data/market_matrix/market_return_matrix.csv",
        signals_path="data/forecasting/ensemble_forecast_signals.csv",
        output_weights_path="data/optimization/black_litterman_weights.csv",
        output_summary_path="data/optimization/black_litterman_summary.csv",
        lookback_days=126,
        risk_aversion=6.0,
        tau=0.05,
        max_weight=0.35,
        smoothing_alpha=0.10,
    ):
        self.returns_path = Path(returns_path)
        self.signals_path = Path(signals_path)
        self.output_weights_path = Path(output_weights_path)
        self.output_summary_path = Path(output_summary_path)
        self.lookback_days = lookback_days
        self.risk_aversion = risk_aversion
        self.tau = tau
        self.max_weight = max_weight
        self.smoothing_alpha = smoothing_alpha

    def load_data(self):
        returns = pd.read_csv(self.returns_path)
        signals = pd.read_csv(self.signals_path)

        returns["Date"] = pd.to_datetime(returns["Date"])
        signals["Date"] = pd.to_datetime(signals["Date"])

        returns = returns.sort_values("Date")
        signals = signals.sort_values("Date")

        return returns, signals

    def get_asset_columns(self, returns):
        return [c for c in returns.columns if c != "Date"]

    def market_implied_prior(self, window_returns):
        covariance = window_returns.cov()
        market_weights = pd.Series(
            1.0 / window_returns.shape[1],
            index=window_returns.columns,
        )

        prior_returns = self.risk_aversion * covariance.dot(market_weights)

        return prior_returns, covariance

    def build_views(self, date, signals, assets):
        signal_rows = signals[signals["Date"] <= date]

        if signal_rows.empty:
            return pd.Series(0.0, index=assets), 0.25

        latest = signal_rows.groupby("asset").tail(1)

        view_map = {}

        for asset in assets:
            row = latest[latest["asset"] == asset]

            if row.empty:
                view_map[asset] = 0.0
                continue

            if "uncertainty_adjusted_signal" in row.columns:
                view_map[asset] = row["uncertainty_adjusted_signal"].iloc[0]
            elif "final_expected_return_signal" in row.columns:
                view_map[asset] = row["final_expected_return_signal"].iloc[0]
            else:
                view_map[asset] = 0.0

        views = pd.Series(view_map).replace([np.inf, -np.inf], np.nan).fillna(0.0)

        if "forecast_conviction" in latest.columns:
            confidence = latest["forecast_conviction"].mean()
        elif "calibrated_regime_confidence" in latest.columns:
            confidence = latest["calibrated_regime_confidence"].mean()
        else:
            confidence = 0.25

        confidence = float(np.nan_to_num(confidence, nan=0.25))
        confidence = np.clip(confidence, 0.05, 1.0)

        return views, confidence

    def posterior_returns(self, prior_returns, views, confidence):
        views = views.reindex(prior_returns.index).fillna(0.0)

        view_scaled = views / (views.abs().max() + 1e-8)
        view_scaled = view_scaled * prior_returns.abs().mean()

        posterior = (1 - confidence) * prior_returns + confidence * view_scaled

        return posterior

    def optimize_weights(self, posterior, covariance, confidence):
        vol = np.sqrt(np.diag(covariance))
        score = posterior / (vol + 1e-8)

        score = pd.Series(score, index=posterior.index)
        score = score.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        score = score.clip(lower=0)

        cash_weight = min(0.25, max(0.0, (1 - confidence) * 0.40))
        investable_weight = 1.0 - cash_weight

        if score.sum() <= 0:
            weights = pd.Series(investable_weight / len(score), index=score.index)
        else:
            weights = score / score.sum() * investable_weight

        capped = pd.Series(0.0, index=score.index)
        remaining_assets = list(score.index)
        remaining_weight = investable_weight

        while remaining_assets:
            temp_score = score[remaining_assets]

            if temp_score.sum() <= 0:
                proposed = pd.Series(
                    remaining_weight / len(remaining_assets),
                    index=remaining_assets,
                )
            else:
                proposed = temp_score / temp_score.sum() * remaining_weight

            over_cap = proposed > self.max_weight

            if not over_cap.any():
                capped[remaining_assets] = proposed
                break

            capped_assets = proposed[over_cap].index

            for asset in capped_assets:
                capped[asset] = self.max_weight

            remaining_weight = investable_weight - capped.sum()
            remaining_assets = [a for a in remaining_assets if a not in capped_assets]

        capped["CASH"] = cash_weight

        return capped / capped.sum()

    def run(self):
        returns, signals = self.load_data()
        assets = self.get_asset_columns(returns)

        records = []
        previous_weights = None

        for i in range(self.lookback_days, len(returns)):
            date = returns.iloc[i]["Date"]
            window = returns.iloc[i - self.lookback_days:i][assets]

            prior, covariance = self.market_implied_prior(window)
            views, confidence = self.build_views(date, signals, assets)
            posterior = self.posterior_returns(prior, views, confidence)

            target_weights = self.optimize_weights(posterior, covariance, confidence)

            if previous_weights is None:
                weights = target_weights
            else:
                all_assets = sorted(set(target_weights.index).union(previous_weights.index))

                target_weights = target_weights.reindex(all_assets).fillna(0.0)
                previous_weights = previous_weights.reindex(all_assets).fillna(0.0)

                weights = (
                    self.smoothing_alpha * target_weights
                    + (1 - self.smoothing_alpha) * previous_weights
                )

                weights = weights / weights.sum()

            previous_weights = weights.copy()

            record = {
                "Date": date,
                "view_confidence": confidence,
                "cash_weight": weights.get("CASH", 0.0),
                "gross_exposure": weights.drop("CASH", errors="ignore").sum(),
                "max_asset_weight": weights.drop("CASH", errors="ignore").max(),
            }

            for asset in assets:
                record[f"{asset}_weight"] = weights.get(asset, 0.0)
                record[f"{asset}_posterior_return"] = posterior.get(asset, 0.0)

            record["CASH_weight"] = weights.get("CASH", 0.0)

            records.append(record)

        weights_df = pd.DataFrame(records)

        summary_rows = []
        for asset in assets + ["CASH"]:
            col = f"{asset}_weight"
            summary_rows.append({
                "asset": asset,
                "avg_weight": weights_df[col].mean(),
                "max_weight": weights_df[col].max(),
                "min_weight": weights_df[col].min(),
                "latest_weight": weights_df[col].iloc[-1],
            })

        summary = pd.DataFrame(summary_rows).sort_values("avg_weight", ascending=False)

        self.output_weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_df.to_csv(self.output_weights_path, index=False)
        summary.to_csv(self.output_summary_path, index=False)

        print("BLACK-LITTERMAN ALLOCATOR COMPLETE")
        print("=" * 60)
        print(f"Saved weights: {self.output_weights_path}")
        print(f"Saved summary: {self.output_summary_path}")
        print()
        print("Latest allocation:")
        print(summary[["asset", "latest_weight", "avg_weight", "max_weight"]].to_string(index=False))
        print()
        print(f"Average view confidence: {weights_df['view_confidence'].mean():.4f}")
        print(f"Average cash weight: {weights_df['cash_weight'].mean():.4f}")

        return weights_df, summary


if __name__ == "__main__":
    allocator = BlackLittermanAllocator()
    allocator.run()