from app.indicators import atr, prior_high, rsi, sma, volume_ratio
from tests.helpers import make_bars


def test_sma():
    assert sma([1, 2, 3, 4, 5], 5) == 3
    assert sma([1, 2, 3], 5) is None


def test_prior_high_excludes_current_bar():
    highs = [1, 2, 10, 4, 5]
    assert prior_high(highs, 3) == 10
    assert prior_high(highs, 2) == 10
    assert prior_high([1, 2, 3], 3) is None


def test_volume_ratio():
    volumes = [10] * 20 + [25]
    assert volume_ratio(volumes, 20) == 2.5
    assert volume_ratio([10] * 20, 20) is None


def test_rsi_uptrend_is_maxed():
    closes = [100 + i for i in range(30)]
    value = rsi(closes, 10)
    assert value is not None
    assert value == 100


def test_atr_positive_on_range():
    bars = make_bars(30)
    value = atr(bars, 14)
    assert value is not None
    assert value > 0
