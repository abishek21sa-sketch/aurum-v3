import pandas as pd

from src.optimization.market_regime_detector import (
    MarketRegimeDetector,
)


detector = MarketRegimeDetector()


def test_crisis_regime():
    row = pd.Series(
        {
            "rolling_return": -0.01,
            "rolling_volatility": 0.01,
            "vix_level": 0.03,
        }
    )

    assert detector.classify_regime(row) == "crisis"


def test_high_volatility_regime():
    row = pd.Series(
        {
            "rolling_return": 0.0,
            "rolling_volatility": 0.02,
            "vix_level": 0.01,
        }
    )

    assert detector.classify_regime(row) == "high_volatility"


def test_bull_regime():
    row = pd.Series(
        {
            "rolling_return": 0.01,
            "rolling_volatility": 0.005,
            "vix_level": -0.01,
        }
    )

    assert detector.classify_regime(row) == "bull"


def test_normal_regime():
    row = pd.Series(
        {
            "rolling_return": 0.0005,
            "rolling_volatility": 0.01,
            "vix_level": 0.01,
        }
    )

    assert detector.classify_regime(row) == "normal"


def test_build_summary_counts():
    df = pd.DataFrame(
        {
            "regime": [
                "bull",
                "bull",
                "crisis",
                "normal",
            ]
        }
    )

    summary = detector.build_summary(df)

    bull_count = (
        summary.loc[
            summary["regime"] == "bull",
            "count",
        ].iloc[0]
    )

    assert bull_count == 2


def test_summary_percentages_sum_to_one():
    df = pd.DataFrame(
        {
            "regime": [
                "bull",
                "bull",
                "crisis",
                "normal",
            ]
        }
    )

    summary = detector.build_summary(df)

    assert abs(
        summary["percentage"].sum() - 1.0
    ) < 1e-9