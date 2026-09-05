import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class MarketRegimeDetector:

    def __init__(self):

        self.matrix_path = Path(
            "data/market_matrix"
        )

        self.output_path = Path(
            "data/regimes"
        )

    def load_market_matrix(self):

        df = pd.read_csv(
            self.matrix_path /
            "market_return_matrix.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def engineer_regime_features(
        self,
        df
    ):

        feature_df = df.copy()

        asset_columns = [
            col for col in feature_df.columns
            if col != "Date"
        ]

        feature_df["market_mean_return"] = (
            feature_df[asset_columns]
            .mean(axis=1)
        )

        feature_df["market_volatility"] = (
            feature_df[asset_columns]
            .std(axis=1)
        )

        feature_df["cross_asset_dispersion"] = (
            feature_df[asset_columns]
            .max(axis=1)
            -
            feature_df[asset_columns]
            .min(axis=1)
        )

        return feature_df

    def detect_regimes(
        self,
        feature_df,
        n_regimes=3
    ):

        clustering_features = [
            "market_mean_return",
            "market_volatility",
            "cross_asset_dispersion"
        ]

        X = feature_df[
            clustering_features
        ]

        scaler = StandardScaler()

        X_scaled = scaler.fit_transform(X)

        model = KMeans(
            n_clusters=n_regimes,
            random_state=42,
            n_init=10
        )

        regimes = model.fit_predict(X_scaled)

        feature_df["regime"] = regimes

        return feature_df, model

    def summarize_regimes(
        self,
        feature_df
    ):

        summary = (
            feature_df
            .groupby("regime")[
                [
                    "market_mean_return",
                    "market_volatility",
                    "cross_asset_dispersion"
                ]
            ]
            .mean()
        )

        return summary

    def save_outputs(
        self,
        feature_df,
        summary
    ):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        feature_df.to_csv(
            self.output_path /
            "market_regimes.csv",
            index=False
        )

        summary.to_csv(
            self.output_path /
            "regime_summary.csv"
        )

        print("\nSaved regime outputs")
    
    def assign_regime_labels(self, summary):

            sorted_summary = summary.sort_values(
                "market_volatility"
            )

            label_map = {
                sorted_summary.index[0]: "normal",
                sorted_summary.index[1]: "stress",
                sorted_summary.index[2]: "shock",
            }

            return label_map

    def run_pipeline(self):

        print("=" * 60)
        print("MARKET REGIME DETECTION")
        print("=" * 60)

        df = self.load_market_matrix()

        feature_df = (
            self.engineer_regime_features(df)
        )

        feature_df, model = (
            self.detect_regimes(feature_df)
        )

        summary = self.summarize_regimes(
            feature_df
        )
        
        label_map = self.assign_regime_labels(summary)

        feature_df["regime_label"] = (
            feature_df["regime"].map(label_map)
        )

        self.save_outputs(
            feature_df,
            summary
        )

        print("\nREGIME SUMMARY")
        print(summary)

        print("\nLATEST MARKET STATES")
        print(
            feature_df[
                [
                    "Date",
                    "market_mean_return",
                    "market_volatility",
                    "cross_asset_dispersion",
                    "regime",
                    "regime_label"
                ]
            ].tail(15)
        )

        


if __name__ == "__main__":

    detector = MarketRegimeDetector()

    detector.run_pipeline()
