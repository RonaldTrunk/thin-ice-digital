from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True)
class Bar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


def _last_n(values: Sequence[float], period: int) -> list[float] | None:
    if len(values) < period:
        return None
    return list(values[-period:])


def sma(values: Sequence[float], period: int) -> float | None:
    window = _last_n(values, period)
    if window is None:
        return None
    return sum(window) / period


def true_ranges(bars: Sequence[Bar]) -> list[float]:
    out: list[float] = []
    for i, bar in enumerate(bars):
        if i == 0:
            out.append(bar.high - bar.low)
            continue
        prev_close = bars[i - 1].close
        out.append(max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close)))
    return out


def wilder_smooth(values: Sequence[float], period: int) -> float | None:
    if len(values) < period:
        return None
    seed = sum(values[:period]) / period
    current = seed
    for value in values[period:]:
        current = (current * (period - 1) + value) / period
    return current


def atr(bars: Sequence[Bar], period: int = 14) -> float | None:
    return wilder_smooth(true_ranges(bars), period)


def rsi(closes: Sequence[float], period: int = 10) -> float | None:
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = wilder_smooth(gains, period)
    avg_loss = wilder_smooth(losses, period)
    if avg_gain is None or avg_loss is None:
        return None
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def prior_high(highs: Sequence[float], lookback: int) -> float | None:
    """Highest high over the lookback window, excluding the current bar."""
    if len(highs) < lookback + 1:
        return None
    return max(highs[-(lookback + 1) : -1])


def volume_ratio(volumes: Sequence[float], lookback: int) -> float | None:
    if len(volumes) < lookback + 1:
        return None
    average = sum(volumes[-(lookback + 1) : -1]) / lookback
    if average <= 0:
        return None
    return volumes[-1] / average
