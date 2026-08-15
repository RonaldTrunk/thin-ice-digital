from __future__ import annotations

import csv
import io
import time
from datetime import date, datetime
from typing import Callable

import httpx

from app.config import Settings, get_settings
from app.indicators import Bar


class MarketDataError(RuntimeError):
    pass


_CACHE: dict[str, tuple[float, list[Bar]]] = {}


def _cache_get(key: str, ttl: float) -> list[Bar] | None:
    hit = _CACHE.get(key)
    if not hit:
        return None
    expires, bars = hit
    if time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return bars


def _cache_set(key: str, bars: list[Bar], ttl: float) -> list[Bar]:
    _CACHE[key] = (time.time() + ttl, bars)
    return bars


def parse_stooq_csv(text: str) -> list[Bar]:
    rows = list(csv.DictReader(io.StringIO(text)))
    bars: list[Bar] = []
    for row in rows:
        try:
            close = float(row["Close"])
            if close <= 0:
                continue
            bars.append(
                Bar(
                    date=date.fromisoformat(row["Date"]),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=close,
                    volume=float(row.get("Volume") or 0),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    bars.sort(key=lambda bar: bar.date)
    return bars


def stooq_symbols(symbol: str) -> list[str]:
    key = symbol.upper().replace("-", "").replace("=", "")
    if key in {"BTC", "BTCUSD"}:
        return ["btc.v", "btcusd"]
    if key in {"VIX", "^VIX"}:
        return ["^vix", "$vix", "vix.us"]
    if key.endswith(".US"):
        return [key.lower()]
    return [f"{symbol.lower()}.us", symbol.lower()]


def fetch_stooq_bars(
    symbol: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 12.0,
) -> list[Bar]:
    own_client = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "glacifraga/0.1"})
    try:
        last_error = None
        for stooq_symbol in stooq_symbols(symbol):
            url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
            try:
                response = http.get(url)
                response.raise_for_status()
                if "Date" not in response.text.splitlines()[0]:
                    last_error = f"unexpected payload for {stooq_symbol}"
                    continue
                bars = parse_stooq_csv(response.text)
                if len(bars) >= 30:
                    return bars
                last_error = f"too few bars for {stooq_symbol}"
            except Exception as exc:  # noqa: BLE001 — try next alias
                last_error = str(exc)
        raise MarketDataError(f"No market data for {symbol}: {last_error}")
    finally:
        if own_client:
            http.close()


def latest_close(bars: list[Bar]) -> float | None:
    if not bars:
        return None
    return bars[-1].close


def fetch_bars(symbol: str, settings: Settings | None = None) -> list[Bar]:
    cfg = settings or get_settings()
    cached = _cache_get(f"bars:{symbol.upper()}", cfg.cache_ttl_s)
    if cached is not None:
        return cached
    bars = fetch_stooq_bars(symbol, timeout=cfg.market_timeout_s)
    return _cache_set(f"bars:{symbol.upper()}", bars, cfg.cache_ttl_s)


def fetch_vix(settings: Settings | None = None) -> float | None:
    cfg = settings or get_settings()
    cached = _cache_get("bars:VIX", cfg.cache_ttl_s)
    if cached is not None:
        return latest_close(cached)
    try:
        bars = fetch_stooq_bars("VIX", timeout=cfg.market_timeout_s)
        _cache_set("bars:VIX", bars, cfg.cache_ttl_s)
        return latest_close(bars)
    except MarketDataError:
        return None


def spy_day_return(settings: Settings | None = None) -> float | None:
    bars = fetch_bars("SPY", settings)
    if len(bars) < 2:
        return None
    prev, last = bars[-2], bars[-1]
    if prev.close <= 0:
        return None
    return (last.close / prev.close) - 1.0


Fetcher = Callable[[str], list[Bar]]


def as_of_label(bars: list[Bar]) -> str:
    if not bars:
        return datetime.utcnow().isoformat()
    return bars[-1].date.isoformat()
