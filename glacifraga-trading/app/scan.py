"""Universe scan — Obsidian at 16:05 ET, Aurora Bitcoin at 00:05 UTC."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace

from app.config import get_settings
from app.engine import generate_signal
from app.guards import MarketHalt, PortfolioSnapshot, assert_scan_allowed
from app.market import MarketDataError, fetch_bars, fetch_vix, spy_day_return
from app.universe import AssetClass, universe_for


def _sleeve_instruments(bot_mode: str, sleeve: str):
    instruments = universe_for(bot_mode)
    key = sleeve.lower().strip()
    if key == "crypto":
        return tuple(item for item in instruments if item.asset_class == AssetClass.CRYPTO)
    if key in {"equity", "equities", "obsidian"}:
        return tuple(item for item in instruments if item.asset_class != AssetClass.CRYPTO)
    return instruments


def run_scan(
    *,
    equity: float | None = None,
    prior_equity: float | None = None,
    open_symbols: set[str] | None = None,
    sleeve: str = "all",
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
    instruments = _sleeve_instruments(cfg.bot_mode, sleeve)
    for instrument in instruments:
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
        "sleeve": sleeve.lower().strip(),
        "halt": halt,
        "vix": vix,
        "spy_day_return": snapshot.spy_day_return,
        "scanned": len(instruments),
        "buys": buys,
        "hold_count": len(holds),
        "errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Glacifraga EOD / UTC scan")
    parser.add_argument(
        "--sleeve",
        default="all",
        choices=["all", "crypto", "equity"],
        help="all (default), equity at 16:05 ET, or crypto at 00:05 UTC",
    )
    args = parser.parse_args()
    print(json.dumps(run_scan(sleeve=args.sleeve), indent=2, default=str))
