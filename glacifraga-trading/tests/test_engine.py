from app.engine import generate_signal, vix_regime
from app.universe import instrument_for
from tests.helpers import make_bars


def test_vix_regimes():
    assert vix_regime(16.1)["label"] == "green"
    assert vix_regime(24)["label"] == "amber"
    assert vix_regime(35)["multiplier"] == 0.4
    assert vix_regime(None)["label"] == "unknown"


def test_buy_when_all_gates_pass(settings):
    bars = make_bars(220, last_volume=2_200_000)
    result = generate_signal(bars, symbol="MSFT", vix=16.1, settings=settings)
    assert result.signal == "BUY"
    assert result.shares and result.shares > 0
    assert result.stop_loss < result.price < result.take_profit
    assert result.audit["breakout"]["passed"]
    assert result.audit["rsi"]["passed"]
    assert result.audit["volume"]["passed"]
    assert result.audit["sma200"]["passed"]
    assert result.audit["vix"]["label"] == "green"
    assert "breakout" in result.reason.lower()


def test_hold_without_volume_confirmation(settings):
    bars = make_bars(220, last_volume=1_000_000)
    result = generate_signal(bars, symbol="MSFT", vix=16.1, settings=settings)
    assert result.signal == "HOLD"
    assert "volume" in result.reason.lower()


def test_hold_without_breakout(settings):
    bars = make_bars(220, step=0.25, last_volume=2_200_000, last_close=80)
    result = generate_signal(bars, symbol="MSFT", vix=16.1, settings=settings)
    assert result.signal == "HOLD"
    assert "breakout" in result.reason.lower()


def test_hold_insufficient_history(settings):
    bars = make_bars(40, last_volume=2_200_000)
    result = generate_signal(bars, symbol="MSFT", settings=settings)
    assert result.signal == "HOLD"
    assert "history" in result.reason.lower()


def test_commodity_uses_wider_trail(settings):
    bars = make_bars(220, last_volume=2_200_000)
    gdx = generate_signal(
        bars, symbol="GDX", vix=16.1, instrument=instrument_for("GDX"), settings=settings
    )
    msft = generate_signal(bars, symbol="MSFT", vix=16.1, settings=settings)
    assert gdx.audit["risk"]["trail_atr"] == settings.trail_atr_commodity
    assert msft.audit["risk"]["trail_atr"] == settings.trail_atr_equity
