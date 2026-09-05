import pandas as pd

from src.anomalies.anomaly_detector import detect_market_anomalies


def test_normal_market_move_is_low_severity():
    snapshot = pd.DataFrame(
        [
            {
                "timestamp_utc": "2026-01-01T00:00:00+00:00",
                "ticker": "SPY",
                "daily_return": 0.01,
                "volume": 1000000,
            }
        ]
    )

    alerts = detect_market_anomalies(snapshot)

    assert len(alerts) == 1
    assert alerts.iloc[0]["alert_type"] == "NORMAL"
    assert alerts.iloc[0]["severity"] == "LOW"


def test_large_market_move_is_high_severity():
    snapshot = pd.DataFrame(
        [
            {
                "timestamp_utc": "2026-01-01T00:00:00+00:00",
                "ticker": "QQQ",
                "daily_return": -0.07,
                "volume": 1000000,
            }
        ]
    )

    alerts = detect_market_anomalies(snapshot)

    assert alerts.iloc[0]["alert_type"] == "RETURN_SHOCK"
    assert alerts.iloc[0]["severity"] == "HIGH"


def test_zero_volume_triggers_data_quality_alert():
    snapshot = pd.DataFrame(
        [
            {
                "timestamp_utc": "2026-01-01T00:00:00+00:00",
                "ticker": "TLT",
                "daily_return": 0.01,
                "volume": 0,
            }
        ]
    )

    alerts = detect_market_anomalies(snapshot)

    assert alerts.iloc[0]["alert_type"] == "DATA_QUALITY"
    assert alerts.iloc[0]["severity"] == "MEDIUM"