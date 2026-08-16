"""EOD universe scan — evaluate Obsidian (or Aurora) with portfolio gates."""

from __future__ import annotations

import json
from dataclasses import replace

from app.config import get_settings
from app.engine import generate_signal
from app.guards import MarketHalt, PortfolioSnapshot, assert_scan_allowed
from app.market import MarketDataError, fetch_bars, fetch_vix, spy_day_return
from app.universe import universe_for


def run_scan(
    *,
    equity: float | None = None,
    prior_equity: float | None = None,
    open_symbols: set[str] | None = None,
) -> dict:
    cfg = get_settings()
    account = equity if equity is not None else cfg.account_size
    snapshot = PortfolioSnapshot(
        equity=account,
        prior_equity=prior_equity,
        spy_day_return=spy_day_return(cfg),
        open_symbols=open_symbols or set(),
        new_entries_today=0,
    )
    try:
        assert_scan_allowed(
            snapshot,
            daily_loss_limit=cfg.daily_loss_limit,
            spy_crash_day=cfg.spy_crash_day,
            max_new_entries=cfg.max_new_entries,
        )
        halt = None
    except MarketHalt as exc:
        halt = str(exc)

    vix = fetch_vix(cfg)
    buys = []
    holds = []
    errors = []
    for instrument in universe_for(cfg.bot_mode):
        if instrument.symbol in snapshot.open_symbols:
            continue
        if halt:
            break
        if snapshot.new_entries_today >= cfg.max_new_entries:
            break
        try:
            bars = fetch_bars(instrument.symbol, cfg)
        except MarketDataError as exc:
            errors.append({"symbol": instrument.symbol, "error": str(exc)})
            continue
        signal = generate_signal(
            bars,
            symbol=instrument.symbol,
            account_size=account,
            vix=vix,
            instrument=instrument,
            settings=cfg,
        )
        payload = signal.as_api()
        if signal.signal == "BUY":
            buys.append(payload)
            snapshot = replace(snapshot, new_entries_today=snapshot.new_entries_today + 1)
        else:
            holds.append({"symbol": signal.symbol, "reason": signal.reason, "confidence": signal.confidence})

    return {
        "mode": cfg.bot_mode.upper(),
        "halt": halt,
        "vix": vix,
        "spy_day_return": snapshot.spy_day_return,
        "buys": buys,
        "hold_count": len(holds),
        "errors": errors,
    }


if __name__ == "__main__":
    print(json.dumps(run_scan(), indent=2, default=str))
