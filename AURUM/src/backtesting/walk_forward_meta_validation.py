from pathlib import Path
import numpy as np
import pandas as pd


class WalkForwardMetaValidation:
    def __init__(
        self,
        output_path="data/validation/walk_forward_meta_validation.csv",
        summary_path="data/validation/walk_forward_meta_validation_summary.csv",
        train_window=126,
        test_window=21,
        max_strategy_weight=0.40,
    ):
        self.output_path = Path(output_path)
        self.summary_path = Path(summary_path)
        self.train_window = train_window
        self.test_window = test_window
        self.max_strategy_weight = max_strategy_weight

        self.strategy_return_files = {
            "rolling_min_variance": "data/backtesting/rolling_min_variance_backtest.csv",
            "dynamic_allocation": "data/backtesting/dynamic_allocation_transaction_cost.csv",
            "regime_aware": "data/backtesting/regime_aware_backtest.csv",
            "black_litterman": "data/backtesting/black_litterman_backtest.csv",
            "hrp": "data/backtesting/hrp_backtest.csv",
            "bayesian_robust": "data/backtesting/bayesian_robust_backtest.csv",
        }

    def load_strategy_returns(self):
        frames = []

        for strategy, path in self.strategy_return_files.items():
            path = Path(path)

            if not path.exists():
                continue

            df = pd.read_csv(path)

            if "Date" not in df.columns:
                continue

            df["Date"] = pd.to_datetime(df["Date"])

            if "net_return" in df.columns:
                ret_col = "net_return"
            elif "portfolio_return" in df.columns:
                ret_col = "portfolio_return"
            else:
                continue

            temp = df[["Date", ret_col]].copy()
            temp.columns = ["Date", strategy]
            frames.append(temp)

        merged = frames[0]

        for frame in frames[1:]:
            merged = merged.merge(frame, on="Date", how="inner")

        return merged.sort_values("Date").reset_index(drop=True)

    def compute_strategy_scores(self, train_returns):
        rows = []

        for strategy in train_returns.columns:
            if strategy == "Date":
                continue

            r = train_returns[strategy].dropna()

            if len(r) < 20:
                continue

            equity = (1 + r).cumprod()
            drawdown = equity / equity.cummax() - 1

            vol = r.std() * np.sqrt(252)
            sharpe = (r.mean() * 252) / (vol + 1e-8)
            total_return = equity.iloc[-1] - 1
            max_drawdown = drawdown.min()

            score = (
                sharpe
                + 0.75 * total_return
                - 1.50 * abs(max_drawdown)
            )

            rows.append({
                "strategy": strategy,
                "train_return": total_return,
                "train_volatility": vol,
                "train_sharpe": sharpe,
                "train_max_drawdown": max_drawdown,
                "score": max(score, 0),
            })

        score_df = pd.DataFrame(rows)

        if score_df["score"].sum() <= 0:
            score_df["weight"] = 1 / len(score_df)
        else:
            score_df["weight"] = score_df["score"] / score_df["score"].sum()

        score_df["weight"] = score_df["weight"].clip(upper=self.max_strategy_weight)
        score_df["weight"] = score_df["weight"] / score_df["weight"].sum()

        return score_df

    def run(self):
        returns = self.load_strategy_returns()

        strategy_cols = [c for c in returns.columns if c != "Date"]

        records = []

        start = self.train_window

        while start + self.test_window <= len(returns):
            train = returns.iloc[start - self.train_window:start]
            test = returns.iloc[start:start + self.test_window]

            score_df = self.compute_strategy_scores(train)

            weight_map = dict(zip(score_df["strategy"], score_df["weight"]))

            weights = np.array([
                weight_map.get(strategy, 0.0)
                for strategy in strategy_cols
            ])

            test_matrix = test[strategy_cols].values
            meta_returns = test_matrix.dot(weights)

            for idx, date in enumerate(test["Date"]):
                record = {
                    "Date": date,
                    "walk_forward_meta_return": meta_returns[idx],
                    "train_start": train["Date"].iloc[0],
                    "train_end": train["Date"].iloc[-1],
                    "test_start": test["Date"].iloc[0],
                    "test_end": test["Date"].iloc[-1],
                }

                for strategy in strategy_cols:
                    record[f"{strategy}_weight"] = weight_map.get(strategy, 0.0)

                records.append(record)

            start += self.test_window

        result = pd.DataFrame(records)

        result["equity_curve"] = (
            1 + result["walk_forward_meta_return"]
        ).cumprod()

        result["running_peak"] = result["equity_curve"].cummax()

        result["drawdown"] = (
            result["equity_curve"]
            / result["running_peak"]
            - 1
        )

        vol = result["walk_forward_meta_return"].std() * np.sqrt(252)

        sharpe = (
            result["walk_forward_meta_return"].mean() * 252
        ) / (vol + 1e-8)

        summary = pd.DataFrame([{
            "observations": len(result),
            "total_return": result["equity_curve"].iloc[-1] - 1,
            "volatility": vol,
            "sharpe_like": sharpe,
            "max_drawdown": result["drawdown"].min(),
        }])

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(self.output_path, index=False)
        summary.to_csv(self.summary_path, index=False)

        print("WALK-FORWARD META VALIDATION COMPLETE")
        print("=" * 70)
        print(summary.to_string(index=False))
        print()
        print(f"Saved validation: {self.output_path}")
        print(f"Saved summary: {self.summary_path}")

        return result, summary


if __name__ == "__main__":
    validator = WalkForwardMetaValidation()
    validator.run()