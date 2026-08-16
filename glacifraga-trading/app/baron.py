from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import Settings, get_settings
from app.universe import is_aurora_mode, universe_for

ET = ZoneInfo("America/New_York")


def baron_status(settings: Settings | None = None) -> dict:
    cfg = settings or get_settings()
    tickers = len(universe_for(cfg.bot_mode))
    as_of = datetime.now(ET).isoformat()
    aurora = is_aurora_mode(cfg.bot_mode)
    strategy = "Glacifraga Aurora" if aurora else "Glacifraga Obsidian"
    if not cfg.alpaca_api_key or not cfg.alpaca_api_secret:
        return {
            "linked": False,
            "mode": cfg.bot_mode.upper(),
            "strategy": strategy,
            "paper": True,
            "scan_time_et": "16:05",
            "crypto": aurora,
            "tickers": tickers,
            "equity": None,
            "cash": None,
            "buying_power": None,
            "positions": [],
            "position_count": 0,
            "as_of_et": as_of,
            "message": "Add ALPACA_API_KEY and ALPACA_API_SECRET on the web service to mirror live paper positions.",
        }

    headers = {
        "APCA-API-KEY-ID": cfg.alpaca_api_key,
        "APCA-API-SECRET-KEY": cfg.alpaca_api_secret,
    }
    base = cfg.alpaca_base_url.rstrip("/")
    try:
        with httpx.Client(timeout=12.0, headers=headers) as client:
            account = client.get(f"{base}/v2/account").raise_for_status().json()
            positions = client.get(f"{base}/v2/positions").raise_for_status().json()
    except Exception as exc:  # noqa: BLE001
        return {
            "linked": False,
            "mode": cfg.bot_mode.upper(),
            "strategy": strategy,
            "paper": True,
            "scan_time_et": "16:05",
            "crypto": aurora,
            "tickers": tickers,
            "positions": [],
            "position_count": 0,
            "as_of_et": as_of,
            "message": f"Alpaca request failed: {exc}",
        }

    rows = []
    for pos in positions:
        rows.append(
            {
                "symbol": pos.get("symbol"),
                "qty": float(pos.get("qty") or 0),
                "market_value": float(pos.get("market_value") or 0),
                "unrealized_pl": float(pos.get("unrealized_pl") or 0),
                "unrealized_plpc": float(pos.get("unrealized_plpc") or 0) * 100.0,
            }
        )
    rows.sort(key=lambda row: row["symbol"] or "")
    return {
        "linked": True,
        "mode": cfg.bot_mode.upper(),
        "strategy": strategy,
        "paper": "paper" in base,
        "scan_time_et": "16:05",
        "crypto": aurora,
        "tickers": tickers,
        "equity": float(account.get("equity") or 0),
        "cash": float(account.get("cash") or 0),
        "buying_power": float(account.get("buying_power") or 0),
        "positions": rows,
        "position_count": len(rows),
        "as_of_et": as_of,
    }
