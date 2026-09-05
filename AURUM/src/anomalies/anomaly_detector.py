from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("results/anomalies")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANOMALY_PATH = OUTPUT_DIR / "latest_anomaly_alerts.csv"


def detect_market_anomalies(snapshot: pd.DataFrame) -> pd.DataFrame:
    if snapshot.empty:
        return pd.DataFrame()

    alerts = []

    for _, row in snapshot.iterrows():
        ticker = row["ticker"]
        daily_return = float(row["daily_return"])
        volume = float(row["volume"])

        alert_type = "NORMAL"
        severity = "LOW"
        message = "No major anomaly detected."

        if abs(daily_return) >= 0.05:
            alert_type = "RETURN_SHOCK"
            severity = "HIGH"
            message = f"{ticker} moved {daily_return:.2%} in one day."

        elif abs(daily_return) >= 0.025:
            alert_type = "RETURN_MOVE"
            severity = "MEDIUM"
            message = f"{ticker} showed a notable daily move of {daily_return:.2%}."

        if volume <= 0:
            alert_type = "DATA_QUALITY"
            severity = "MEDIUM"
            message = f"{ticker} has missing or zero volume."

        alerts.append(
            {
                "timestamp_utc": row["timestamp_utc"],
                "ticker": ticker,
                "daily_return": daily_return,
                "volume": volume,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
            }
        )

    alerts_df = pd.DataFrame(alerts)
    alerts_df.to_csv(ANOMALY_PATH, index=False)

    return alerts_df


if __name__ == "__main__":
    snapshot_path = Path("data/live/latest_live_market_snapshot.csv")

    if not snapshot_path.exists():
        raise FileNotFoundError("Run live_market_stream.py first.")

    snapshot = pd.read_csv(snapshot_path)
    alerts = detect_market_anomalies(snapshot)

    print("\nANOMALY ALERTS")
    print("=" * 80)
    print(alerts)