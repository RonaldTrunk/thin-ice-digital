from datetime import datetime, timezone

from app.engine import generate_signal
from app.risk import position_plan
from app.scan import _sleeve_instruments
from app.universe import BTC, instrument_for, is_aurora_mode, universe_for
from tests.helpers import make_bars


def test_fractional_btc_size_on_typical_account():
    plan = position_plan(
        price=63_000,
        atr_value=1_800,
        account_size=100_000,
        fractional=True,
        qty_precision=6,
    )
    assert plan is not None
    assert plan.fractional is True
    assert plan.shares is None
    assert 0 < plan.qty < 1
    assert plan.stop_distance == 3_600
    assert plan.capped is True  # 10% AUM cap (~0.158 BTC) binds before 1% risk (~0.278)


def test_integer_equities_unchanged():
    plan = position_plan(price=50, atr_value=2.5, account_size=100_000)
    assert plan is not None
    assert plan.shares == 200
    assert plan.qty == 200.0
    assert plan.fractional is False


def test_crypto_buy_uses_aurora_trail_and_qty(settings):
    bars = make_bars(220, start=60_000, step=500, last_volume=2_200_000, range_pad=400)
    result = generate_signal(
        bars,
        symbol="BTC",
        vix=16.1,
        instrument=instrument_for("BTC-USD"),
        settings=settings,
    )
    assert result.symbol == "BTC-USD"
    assert result.signal == "BUY"
    assert result.qty and result.qty > 0
    assert result.shares is None or result.shares == int(result.qty)
    assert result.audit["strategy"] == "Glacifraga Aurora"
    assert result.audit["asset_class"] == "crypto"
    assert result.audit["risk"]["trail_atr"] == settings.trail_atr_commodity
    assert result.audit["risk"]["fractional"] is True


def test_duke_universe_includes_bitcoin():
    assert is_aurora_mode("duke")
    assert is_aurora_mode("AURORA")
    assert not is_aurora_mode("BARON")
    duke = universe_for("DUKE")
    assert len(duke) == 49
    assert duke[-1] == BTC
    assert "BTC-USD" not in {item.symbol for item in universe_for("BARON")}


def test_crypto_sleeve_is_bitcoin_only():
    assert [item.symbol for item in _sleeve_instruments("DUKE", "crypto")] == ["BTC-USD"]
    assert "BTC-USD" not in {item.symbol for item in _sleeve_instruments("DUKE", "equity")}
    assert _sleeve_instruments("BARON", "crypto") == ()


def test_incomplete_utc_bitcoin_bar_cannot_false_breakout(settings):
    now = datetime(2026, 8, 16, 20, 5, tzinfo=timezone.utc)  # 16:05 ET, UTC day still open
    # Complete history that does not break out, plus an in-progress today spike.
    base = make_bars(
        219,
        start=60_000,
        step=20,
        last_volume=2_200_000,
        range_pad=40,
        last_close=50_000,
        start_date=now.date().replace(year=2025, month=12, day=1),
    )
    spike = make_bars(
        1,
        start=80_000,
        step=5_000,
        last_volume=9_000_000,
        range_pad=100,
        start_date=now.date(),
    )
    live = generate_signal(
        base + spike,
        symbol="BTC-USD",
        vix=16.1,
        instrument=instrument_for("BTC-USD"),
        settings=settings,
        as_of=now,
    )
    assert live.audit["session"]["dropped_intraday"] is True
    assert live.signal == "HOLD"
    assert "breakout" in live.reason.lower()
