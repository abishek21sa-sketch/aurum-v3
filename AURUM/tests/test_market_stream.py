import pandas as pd

from src.ingestion.live_market_stream import _scalar


def test_scalar_from_float():
    assert _scalar(10.5) == 10.5


def test_scalar_from_int():
    assert _scalar(5) == 5.0


def test_scalar_from_series():
    value = pd.Series([42.0])
    assert _scalar(value) == 42.0