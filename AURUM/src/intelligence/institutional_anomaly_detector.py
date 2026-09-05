"""
AURUM Institutional Anomaly Detector

Upgrades anomaly detection from simple thresholding to:

1. Rolling z-score
2. Isolation Forest
3. Combined anomaly score
4. Institutional severity labels
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()

@dataclass
class AnomalyDetectionResult:
    latest_timestamp: str
    latest_return: float
    latest_rolling_z_score: float
    latest_isolation_score: float
    latest_combined_score: float
    latest_is_anomaly: bool
    latest_severity: str
    anomaly_count: int
    anomaly_rate: float
    method: str


class InstitutionalAnomalyDetector:
    def __init__(
        self,
        rolling_window: int = 60,
        z_threshold: float = 2.5,
        contamination: float = 0.03,
    ):
        self.rolling_window = rolling_window
        self.z_threshold = z_threshold
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=200,
        )

    def detect(self, returns: pd.Series) -> pd.DataFrame:
        if returns.empty:
            raise ValueError("Returns Series is empty.")

        df = pd.DataFrame({"return": returns.dropna()})

        df["rolling_mean"] = df["return"].rolling(self.rolling_window).mean()
        df["rolling_std"] = df["return"].rolling(self.rolling_window).std()

        df["rolling_z_score"] = (
            (df["return"] - df["rolling_mean"]) / df["rolling_std"]
        )

        df["rolling_z_score"] = df["rolling_z_score"].replace(
            [np.inf, -np.inf], np.nan
        )

        feature_df = df.dropna().copy()

        if len(feature_df) < self.rolling_window:
            raise ValueError("Not enough observations for anomaly detection.")

        features = feature_df[
            ["return", "rolling_z_score", "rolling_std"]
        ].replace([np.inf, -np.inf], np.nan).dropna()

        scaled = self.scaler.fit_transform(features)

        isolation_labels = self.model.fit_predict(scaled)
        isolation_raw_scores = self.model.decision_function(scaled)

        features["isolation_label"] = isolation_labels
        features["isolation_score"] = -isolation_raw_scores

        z_component = np.minimum(
            np.abs(features["rolling_z_score"]) / self.z_threshold,
            2.0,
        )

        iso_component = (
            features["isolation_score"] - features["isolation_score"].min()
        ) / (
            features["isolation_score"].max()
            - features["isolation_score"].min()
            + 1e-12
        )

        features["combined_score"] = 0.6 * z_component + 0.4 * iso_component

        features["z_score_anomaly"] = (
            np.abs(features["rolling_z_score"]) >= self.z_threshold
        )

        features["isolation_anomaly"] = features["isolation_label"] == -1

        features["is_anomaly"] = (
            features["z_score_anomaly"] | features["isolation_anomaly"]
        )

        features["severity"] = features["combined_score"].apply(self._severity)

        output = df.join(
            features[
                [
                    "isolation_score",
                    "combined_score",
                    "z_score_anomaly",
                    "isolation_anomaly",
                    "is_anomaly",
                    "severity",
                ]
            ],
            how="left",
        )

        output["severity"] = output["severity"].fillna("insufficient_data")
        output["is_anomaly"] = output["is_anomaly"].fillna(False)

        self.save_dataframe(output)
        self.save_summary(output)

        return output

    @staticmethod
    def _severity(score: float) -> str:
        if score >= 1.25:
            return "critical"
        if score >= 0.90:
            return "alert"
        if score >= 0.60:
            return "watch"
        return "normal"

    def summarize(self, detected: pd.DataFrame) -> AnomalyDetectionResult:
        valid = detected[detected["severity"] != "insufficient_data"].copy()
        latest = valid.iloc[-1]

        anomaly_count = int(valid["is_anomaly"].sum())
        anomaly_rate = float(anomaly_count / len(valid)) if len(valid) else 0.0

        result = AnomalyDetectionResult(
            latest_timestamp=str(latest.name),
            latest_return=float(latest["return"]),
            latest_rolling_z_score=float(latest["rolling_z_score"]),
            latest_isolation_score=float(latest["isolation_score"]),
            latest_combined_score=float(latest["combined_score"]),
            latest_is_anomaly=bool(latest["is_anomaly"]),
            latest_severity=str(latest["severity"]),
            anomaly_count=anomaly_count,
            anomaly_rate=anomaly_rate,
            method="rolling_z_score + isolation_forest",
        )

        return result

    def save_summary(self, detected: pd.DataFrame) -> None:
        result = self.summarize(detected)
        output_path = artifact_path("intelligence", "institutional_anomaly_summary.json")

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=4)

    @staticmethod
    def save_dataframe(detected: pd.DataFrame) -> None:
        output_path = artifact_path("intelligence", "institutional_anomaly_timeseries.csv")
        detected.to_csv(output_path)


def load_sample_returns() -> pd.Series:
    np.random.seed(42)

    n = 750
    returns = np.random.normal(0.00035, 0.01, n)

    shock_indices = [120, 260, 410, 590, 700]
    returns[shock_indices] = [-0.055, 0.041, -0.064, 0.052, -0.075]

    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    return pd.Series(returns, index=dates, name="SPY_return")


def main() -> None:
    returns = load_sample_returns()

    detector = InstitutionalAnomalyDetector(
        rolling_window=60,
        z_threshold=2.5,
        contamination=0.03,
    )

    detected = detector.detect(returns)
    summary = detector.summarize(detected)

    print("=" * 80)
    print("AURUM INSTITUTIONAL ANOMALY DETECTOR")
    print("=" * 80)
    print(f"Method:                {summary.method}")
    print(f"Latest Timestamp:      {summary.latest_timestamp}")
    print(f"Latest Return:         {summary.latest_return:.4f}")
    print(f"Rolling Z-Score:       {summary.latest_rolling_z_score:.4f}")
    print(f"Isolation Score:       {summary.latest_isolation_score:.4f}")
    print(f"Combined Score:        {summary.latest_combined_score:.4f}")
    print(f"Latest Is Anomaly:     {summary.latest_is_anomaly}")
    print(f"Latest Severity:       {summary.latest_severity}")
    print(f"Anomaly Count:         {summary.anomaly_count}")
    print(f"Anomaly Rate:          {summary.anomaly_rate:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()