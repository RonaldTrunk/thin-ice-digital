from __future__ import annotations

import csv
import io
import time
from datetime import date, datetime, timezone
from typing import Callable
from urllib.parse import quote

import httpx

from app.config import Settings, get_settings
from app.indicators import Bar
from app.universe import is_crypto_symbol


class MarketDataError(RuntimeError):
    pass


_CACHE: dict[str, tuple[float, list[Bar]]] = {}
_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Glacifraga/0.2; +https://glacifraga.com)",
    "Accept": "application/json,text/csv,*/*",
}


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


def yahoo_symbol(symbol: str) -> str:
    key = symbol.upper().strip()
    aliases = {
        "BTC": "BTC-USD",
        "BTCUSD": "BTC-USD",
        "BTC-USD": "BTC-USD",
        "XBTUSD": "BTC-USD",
        "BITCOIN": "BTC-USD",
        "VIX": "^VIX",
        "^VIX": "^VIX",
    }
    return aliases.get(key, key)


def parse_yahoo_chart(payload: dict) -> list[Bar]:
    results = (payload.get("chart") or {}).get("result") or []
    if not results:
        return []
    node = results[0]
    timestamps = node.get("timestamp") or []
    quote = ((node.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    bars: list[Bar] = []
    for i, ts in enumerate(timestamps):
        close = closes[i] if i < len(closes) else None
        if close is None or close <= 0:
            continue
        open_px = opens[i] if i < len(opens) and opens[i] is not None else close
        high_px = highs[i] if i < len(highs) and highs[i] is not None else close
        low_px = lows[i] if i < len(lows) and lows[i] is not None else close
        volume = volumes[i] if i < len(volumes) and volumes[i] is not None else 0
        bars.append(
            Bar(
                date=datetime.fromtimestamp(int(ts), tz=timezone.utc).date(),
                open=float(open_px),
                high=float(high_px),
                low=float(low_px),
                close=float(close),
                volume=float(volume),
            )
        )
    bars.sort(key=lambda bar: bar.date)
    return bars


def fetch_stooq_bars(
    symbol: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 12.0,
) -> list[Bar]:
    own_client = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True, headers=_HTTP_HEADERS)
    try:
        last_error = None
        for stooq_symbol in stooq_symbols(symbol):
            url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
            try:
                response = http.get(url)
                response.raise_for_status()
                first = response.text.splitlines()[0] if response.text else ""
                if "Date" not in first:
                    last_error = f"unexpected payload for {stooq_symbol}"
                    continue
                bars = parse_stooq_csv(response.text)
                if len(bars) >= 30:
                    return bars
                last_error = f"too few bars for {stooq_symbol}"
            except Exception as exc:  # noqa: BLE001 — try next alias
                last_error = str(exc)
        raise MarketDataError(f"No Stooq data for {symbol}: {last_error}")
    finally:
        if own_client:
            http.close()


def fetch_yahoo_bars(
    symbol: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 12.0,
    span: str = "10y",
) -> list[Bar]:
    ticker = yahoo_symbol(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(ticker, safe='-^')}?interval=1d&range={span}"
    own_client = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True, headers=_HTTP_HEADERS)
    try:
        response = http.get(url)
        response.raise_for_status()
        bars = parse_yahoo_chart(response.json())
        if len(bars) < 30:
            raise MarketDataError(f"too few Yahoo bars for {ticker}")
        return bars
    except MarketDataError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise MarketDataError(f"No Yahoo data for {symbol}: {exc}") from exc
    finally:
        if own_client:
            http.close()


def _fetch_uncached(symbol: str, timeout: float) -> list[Bar]:
    providers = (
        (fetch_yahoo_bars, fetch_stooq_bars)
        if is_crypto_symbol(symbol)
        else (fetch_stooq_bars, fetch_yahoo_bars)
    )
    errors: list[str] = []
    for provider in providers:
        try:
            return provider(symbol, timeout=timeout)
        except MarketDataError as exc:
            errors.append(str(exc))
    raise MarketDataError(f"No market data for {symbol}: {' | '.join(errors)}")


def latest_close(bars: list[Bar]) -> float | None:
    if not bars:
        return None
    return bars[-1].close


def fetch_bars(symbol: str, settings: Settings | None = None) -> list[Bar]:
    cfg = settings or get_settings()
    cached = _cache_get(f"bars:{symbol.upper()}", cfg.cache_ttl_s)
    if cached is not None:
        return cached
    bars = _fetch_uncached(symbol, cfg.market_timeout_s)
    return _cache_set(f"bars:{symbol.upper()}", bars, cfg.cache_ttl_s)


def fetch_vix(settings: Settings | None = None) -> float | None:
    cfg = settings or get_settings()
    cached = _cache_get("bars:VIX", cfg.cache_ttl_s)
    if cached is not None:
        return latest_close(cached)
    try:
        bars = _fetch_uncached("VIX", cfg.market_timeout_s)
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
        return datetime.now(timezone.utc).isoformat()
    return bars[-1].date.isoformat()
