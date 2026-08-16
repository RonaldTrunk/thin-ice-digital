from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol, Sequence

from app.indicators import Bar


@dataclass
class PortfolioSnapshot:
    equity: float
    prior_equity: float | None
    spy_day_return: float | None
    open_symbols: set[str]
    new_entries_today: int = 0


class MarketHalt(Exception):
    """Scan-level risk gate — no new longs."""


def assert_scan_allowed(
    snapshot: PortfolioSnapshot,
    *,
    daily_loss_limit: float = -0.02,
    spy_crash_day: float = -0.03,
    max_new_entries: int = 6,
) -> None:
    if snapshot.new_entries_today >= max_new_entries:
        raise MarketHalt(f"Max new entries reached ({max_new_entries} per scan).")
    if snapshot.prior_equity and snapshot.prior_equity > 0:
        day_pnl = (snapshot.equity / snapshot.prior_equity) - 1.0
        if day_pnl <= daily_loss_limit:
            raise MarketHalt(f"Daily loss limit hit ({day_pnl:.2%} ≤ {daily_loss_limit:.0%}).")
    if snapshot.spy_day_return is not None and snapshot.spy_day_return < spy_crash_day:
        raise MarketHalt(f"SPY session {snapshot.spy_day_return:.2%} < {spy_crash_day:.0%}; longs suspended.")


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def session_date(now: datetime | None = None) -> date:
    stamp = now or datetime.now(timezone.utc)
    return stamp.date()


def remaining_entry_slots(snapshot: PortfolioSnapshot, max_new_entries: int = 6) -> int:
    return max(0, max_new_entries - snapshot.new_entries_today)


def already_open(snapshot: PortfolioSnapshot, symbol: str) -> bool:
    return symbol.upper() in {item.upper() for item in snapshot.open_symbols}


def bars_are_daily(bars: Sequence[Bar]) -> bool:
    if len(bars) < 2:
        return True
    deltas = [(bars[i].date - bars[i - 1].date).days for i in range(1, min(len(bars), 6))]
    return all(delta >= 1 for delta in deltas)
