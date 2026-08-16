from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.session import settled_daily_bars
from app.universe import instrument_for
from tests.helpers import make_bars

ET = ZoneInfo("America/New_York")


def test_crypto_drops_in_progress_utc_day():
    today = datetime(2026, 8, 16, 20, 0, tzinfo=timezone.utc)  # 16:00 ET, UTC day still open
    bars = make_bars(5, start_date=today.date().replace(day=12))
    # helpers start at start_date and add n days: 12,13,14,15,16
    assert bars[-1].date.isoformat() == "2026-08-16"
    settled, dropped = settled_daily_bars(bars, instrument_for("BTC-USD"), now=today)
    assert dropped is True
    assert settled[-1].date.isoformat() == "2026-08-15"


def test_crypto_keeps_completed_utc_day():
    now = datetime(2026, 8, 16, 0, 10, tzinfo=timezone.utc)
    bars = make_bars(3, start_date=now.date().replace(day=13))  # 13, 14, 15
    settled, dropped = settled_daily_bars(bars, instrument_for("BTC-USD"), now=now)
    assert dropped is False
    assert settled[-1].date.isoformat() == "2026-08-15"


def test_equity_keeps_bar_after_nyse_close():
    now = datetime(2026, 8, 14, 20, 10, tzinfo=timezone.utc)  # 16:10 ET
    session = now.astimezone(ET).date()
    bars = make_bars(1, start_date=session)
    settled, dropped = settled_daily_bars(bars, instrument_for("MSFT"), now=now)
    assert dropped is False
    assert len(settled) == 1


def test_equity_drops_bar_before_nyse_close():
    now = datetime(2026, 8, 14, 18, 0, tzinfo=timezone.utc)  # 14:00 ET
    session = now.astimezone(ET).date()
    bars = make_bars(1, start_date=session)
    settled, dropped = settled_daily_bars(bars, instrument_for("MSFT"), now=now)
    assert dropped is True
    assert settled == []
