from pathlib import Path
import numpy as np
import pandas as pd


class BayesianRobustAllocator:
    def __init__(
        self,
        returns_path="data/market_matrix/market_return_matrix.csv",
        regimes_path="data/regimes/calibrated_regime_probabilities.csv",
        output_weights_path="data/optimization/bayesian_robust_weights.csv",
        output_summary_path="data/optimization/bayesian_robust_summary.csv",
        lookback_days=126,
        risk_aversion=8.0,
        uncertainty_penalty=4.0,
        max_weight=0.35,
        min_weight=0.0,
        smoothing_alpha=0.10,
    ):
        self.returns_path = Path(returns_path)
        self.regimes_path = Path(regimes_path)
        self.output_weights_path = Path(output_weights_path)
        self.output_summary_path = Path(output_summary_path)
        self.lookback_days = lookback_days
        self.risk_aversion = risk_aversion
        self.uncertainty_penalty = uncertainty_penalty
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.smoothing_alpha = smoothing_alpha

    def load_data(self):
        returns = pd.read_csv(self.returns_path)
        regimes = pd.read_csv(self.regimes_path)

        returns["Date"] = pd.to_datetime(returns["Date"])
        regimes["Date"] = pd.to_datetime(regimes["Date"])

        returns = returns.sort_values("Date")
        regimes = regimes.sort_values("Date")

        return returns, regimes

    def get_asset_columns(self, returns):
        excluded = {"Date", "CASH"}
        return [c for c in returns.columns if c not in excluded]
    
    def compute_posterior_mean(self, window_returns, regime_row):
        sample_mean = window_returns.mean()

        regime_confidence = regime_row.get("calibrated_regime_confidence", 0.25)
        max_probability = regime_row.get("calibrated_max_probability", regime_confidence)

        confidence = float(np.nan_to_num(max(regime_confidence, max_probability), nan=0.25))
        confidence = np.clip(confidence, 0.05, 1.0)

        prior_mean = sample_mean.mean()
        posterior_mean = confidence * sample_mean + (1 - confidence) * prior_mean

        return posterior_mean, confidence

    def compute_robust_covariance(self, window_returns, confidence):
        covariance = window_returns.cov()

        uncertainty = 1 - confidence
        diagonal_inflation = np.diag(np.diag(covariance)) * uncertainty * self.uncertainty_penalty

        robust_covariance = covariance + diagonal_inflation

        return robust_covariance, uncertainty

    def score_assets(self, posterior_mean, robust_covariance, uncertainty):
        asset_vol = np.sqrt(np.diag(robust_covariance))

        raw_score = posterior_mean / (asset_vol + 1e-8)
        robust_score = raw_score - self.uncertainty_penalty * uncertainty * asset_vol

        robust_score = robust_score.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        return robust_score

    def convert_scores_to_weights(self, scores, uncertainty):
        scores = scores.clip(lower=0)

        cash_weight = min(0.25, max(0.0, uncertainty * 0.40))
        investable_weight = 1.0 - cash_weight

        if scores.sum() <= 0:
            risky_weights = pd.Series(
                investable_weight / len(scores),
                index=scores.index,
            )
        else:
            risky_weights = scores / scores.sum() * investable_weight

        capped = pd.Series(0.0, index=scores.index)
        remaining_assets = list(scores.index)
        remaining_weight = investable_weight

        while remaining_assets:
            temp_scores = scores[remaining_assets]

            if temp_scores.sum() <= 0:
                proposed = pd.Series(
                    remaining_weight / len(remaining_assets),
                    index=remaining_assets,
                )
            else:
                proposed = temp_scores / temp_scores.sum() * remaining_weight

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

        total = capped.sum()
        if total > 0:
            capped = capped / total

        return capped

    def run(self):
        returns, regimes = self.load_data()
        asset_cols = self.get_asset_columns(returns)

        merged = returns.merge(regimes, on="Date", how="left")
        weight_records = []
        previous_weights = None

        for i in range(self.lookback_days, len(returns)):
            date = returns.iloc[i]["Date"]
            window = returns.iloc[i - self.lookback_days:i][asset_cols]

            regime_rows = regimes[regimes["Date"] <= date]

            if regime_rows.empty:
                regime_row = {}
            else:
                regime_row = regime_rows.iloc[-1].to_dict()

            posterior_mean, confidence = self.compute_posterior_mean(window, regime_row)
            robust_covariance, uncertainty = self.compute_robust_covariance(window, confidence)
            scores = self.score_assets(posterior_mean, robust_covariance, uncertainty)
            target_weights = self.convert_scores_to_weights(scores, uncertainty)

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
                "regime_confidence": confidence,
                "model_uncertainty": uncertainty,
                "gross_exposure": weights.sum(),
                "max_asset_weight": weights.max(),
                "min_asset_weight": weights.min(),
            }

            for asset in asset_cols:
                record[f"{asset}_weight"] = weights.get(asset, 0.0)
                record[f"{asset}_score"] = scores.get(asset, 0.0)

            record["CASH_weight"] = weights.get("CASH", 0.0)
            record["CASH_score"] = 0.0

            weight_records.append(record)

        weights_df = pd.DataFrame(weight_records)

        summary_rows = []
        for asset in asset_cols + ["CASH"]:
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

        print("BAYESIAN ROBUST ALLOCATOR COMPLETE")
        print("=" * 60)
        print(f"Saved weights: {self.output_weights_path}")
        print(f"Saved summary: {self.output_summary_path}")
        print()
        print("Latest allocation:")
        print(summary[["asset", "latest_weight", "avg_weight", "max_weight"]].to_string(index=False))
        print()
        print(f"Average regime confidence: {weights_df['regime_confidence'].mean():.4f}")
        print(f"Average model uncertainty: {weights_df['model_uncertainty'].mean():.4f}")

        return weights_df, summary


if __name__ == "__main__":
    allocator = BayesianRobustAllocator()
    allocator.run()