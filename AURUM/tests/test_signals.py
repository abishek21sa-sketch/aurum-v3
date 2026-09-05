import pandas as pd

from src.signals.signal_engine import QuantSignalEngine


engine = QuantSignalEngine()


def test_shock_regime_generates_risk_off():
    row = pd.Series(
        {
            "regime_label": "shock",
            "market_mean_return": -0.03,
            "market_volatility": 0.04,
            "cross_asset_dispersion": 0.02,
        }
    )

    assert engine.generate_risk_signal(row) == "risk_off"


def test_stress_regime_generates_defensive():
    row = pd.Series(
        {
            "regime_label": "stress",
            "market_mean_return": -0.01,
            "market_volatility": 0.03,
            "cross_asset_dispersion": 0.02,
        }
    )

    assert engine.generate_risk_signal(row) == "defensive"


def test_positive_normal_regime_generates_risk_on():
    row = pd.Series(
        {
            "regime_label": "normal",
            "market_mean_return": 0.01,
            "market_volatility": 0.01,
            "cross_asset_dispersion": 0.01,
        }
    )

    assert engine.generate_risk_signal(row) == "risk_on"


def test_negative_normal_regime_generates_neutral():
    row = pd.Series(
        {
            "regime_label": "normal",
            "market_mean_return": -0.01,
            "market_volatility": 0.01,
            "cross_asset_dispersion": 0.01,
        }
    )

    assert engine.generate_risk_signal(row) == "neutral"


def test_signal_strength_is_sum_of_abs_return_volatility_and_dispersion():
    row = pd.Series(
        {
            "market_mean_return": -0.02,
            "market_volatility": 0.03,
            "cross_asset_dispersion": 0.04,
        }
    )

    assert engine.generate_signal_strength(row) == 0.09


def test_build_signals_adds_expected_columns():
    df = pd.DataFrame(
        [
            {
                "regime_label": "normal",
                "market_mean_return": 0.01,
                "market_volatility": 0.02,
                "cross_asset_dispersion": 0.03,
            }
        ]
    )

    output = engine.build_signals(df)

    assert "risk_signal" in output.columns
    assert "signal_strength" in output.columns
    assert output.iloc[0]["risk_signal"] == "risk_on"
    assert output.iloc[0]["signal_strength"] == 0.06