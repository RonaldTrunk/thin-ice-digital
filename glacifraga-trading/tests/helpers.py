from datetime import date, timedelta

from app.indicators import Bar


def make_bars(
    n: int = 220,
    *,
    start: float = 100.0,
    step: float = 0.25,
    volume: float = 1_000_000,
    last_volume: float | None = None,
    last_close: float | None = None,
    start_date: date | None = None,
    range_pad: float = 0.08,
) -> list[Bar]:
    """Monotonic daily series. `step` > 0 is an uptrend (SMA200 below price)."""
    origin = start_date or date(2020, 1, 2)
    bars: list[Bar] = []
    price = start
    for i in range(n):
        nxt = price + step
        if i == n - 1 and last_close is not None:
            nxt = last_close
        high = max(price, nxt) + range_pad
        low = min(price, nxt) - range_pad
        vol = last_volume if last_volume is not None and i == n - 1 else volume
        bars.append(
            Bar(
                date=origin + timedelta(days=i),
                open=price,
                high=high,
                low=low,
                close=nxt,
                volume=vol,
            )
        )
        price = nxt
    return bars
