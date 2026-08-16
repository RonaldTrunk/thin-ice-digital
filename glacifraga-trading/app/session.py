"""Daily-bar settlement — do not evaluate breakouts on an in-progress candle.

Equities and commodity ETFs complete at the NYSE regular close (16:00 ET).
Bitcoin daily bars on Yahoo/Stooq are UTC days; the in-progress UTC candle
must be dropped or a 16:05 ET scan would treat an 8-hour-old Bitcoin bar as
a finished 20-day breakout.
"""

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Sequence
from zoneinfo import ZoneInfo

from app.indicators import Bar
from app.universe import AssetClass, Instrument

ET = ZoneInfo("America/New_York")
EQUITY_CLOSE_ET = time(16, 0)
EQUITY_SCAN_ET = time(16, 5)
CRYPTO_SCAN_UTC = time(0, 5)


def aware_utc(now: datetime | None = None) -> datetime:
    stamp = now or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp


def settled_daily_bars(
    bars: Sequence[Bar],
    instrument: Instrument,
    *,
    now: datetime | None = None,
) -> tuple[list[Bar], bool]:
    """Return completed daily candles only.

    The second value is True when an in-progress last bar was dropped.
    """
    series = list(bars)
    if not series:
        return series, False
    stamp = aware_utc(now)
    last = series[-1]
    if instrument.asset_class == AssetClass.CRYPTO:
        today = stamp.astimezone(timezone.utc).date()
        if last.date >= today:
            return series[:-1], True
        return series, False
    et = stamp.astimezone(ET)
    if last.date >= et.date() and et.time() < EQUITY_CLOSE_ET:
        return series[:-1], True
    return series, False
