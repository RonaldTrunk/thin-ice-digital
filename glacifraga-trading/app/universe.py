from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssetClass(str, Enum):
    EQUITY = "equity"
    COMMODITY = "commodity"
    CRYPTO = "crypto"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset_class: AssetClass
    name: str


# Representative Obsidian 48: liquid US equities + commodity ETFs, no crypto.
# Live BARON may use a slightly different partner universe; the rules are the same.
OBSIDIAN: tuple[Instrument, ...] = (
    Instrument("AAPL", AssetClass.EQUITY, "Apple"),
    Instrument("MSFT", AssetClass.EQUITY, "Microsoft"),
    Instrument("AMZN", AssetClass.EQUITY, "Amazon"),
    Instrument("GOOGL", AssetClass.EQUITY, "Alphabet"),
    Instrument("META", AssetClass.EQUITY, "Meta"),
    Instrument("NVDA", AssetClass.EQUITY, "NVIDIA"),
    Instrument("AVGO", AssetClass.EQUITY, "Broadcom"),
    Instrument("JPM", AssetClass.EQUITY, "JPMorgan"),
    Instrument("V", AssetClass.EQUITY, "Visa"),
    Instrument("UNH", AssetClass.EQUITY, "UnitedHealth"),
    Instrument("LLY", AssetClass.EQUITY, "Eli Lilly"),
    Instrument("XOM", AssetClass.EQUITY, "Exxon Mobil"),
    Instrument("JNJ", AssetClass.EQUITY, "Johnson & Johnson"),
    Instrument("WMT", AssetClass.EQUITY, "Walmart"),
    Instrument("MA", AssetClass.EQUITY, "Mastercard"),
    Instrument("PG", AssetClass.EQUITY, "Procter & Gamble"),
    Instrument("HD", AssetClass.EQUITY, "Home Depot"),
    Instrument("ORCL", AssetClass.EQUITY, "Oracle"),
    Instrument("COST", AssetClass.EQUITY, "Costco"),
    Instrument("ABBV", AssetClass.EQUITY, "AbbVie"),
    Instrument("CRM", AssetClass.EQUITY, "Salesforce"),
    Instrument("KO", AssetClass.EQUITY, "Coca-Cola"),
    Instrument("MRK", AssetClass.EQUITY, "Merck"),
    Instrument("BAC", AssetClass.EQUITY, "Bank of America"),
    Instrument("AMD", AssetClass.EQUITY, "AMD"),
    Instrument("NFLX", AssetClass.EQUITY, "Netflix"),
    Instrument("DIS", AssetClass.EQUITY, "Disney"),
    Instrument("CSCO", AssetClass.EQUITY, "Cisco"),
    Instrument("CAT", AssetClass.EQUITY, "Caterpillar"),
    Instrument("GE", AssetClass.EQUITY, "GE Aerospace"),
    Instrument("HON", AssetClass.EQUITY, "Honeywell"),
    Instrument("AMGN", AssetClass.EQUITY, "Amgen"),
    Instrument("LMT", AssetClass.EQUITY, "Lockheed Martin"),
    Instrument("QCOM", AssetClass.EQUITY, "Qualcomm"),
    Instrument("TXN", AssetClass.EQUITY, "Texas Instruments"),
    Instrument("PEP", AssetClass.EQUITY, "PepsiCo"),
    Instrument("GLD", AssetClass.COMMODITY, "SPDR Gold"),
    Instrument("SLV", AssetClass.COMMODITY, "iShares Silver"),
    Instrument("GDX", AssetClass.COMMODITY, "VanEck Gold Miners"),
    Instrument("NEM", AssetClass.COMMODITY, "Newmont"),
    Instrument("COPX", AssetClass.COMMODITY, "Global X Copper Miners"),
    Instrument("USO", AssetClass.COMMODITY, "United States Oil"),
    Instrument("UNG", AssetClass.COMMODITY, "United States Natural Gas"),
    Instrument("DBA", AssetClass.COMMODITY, "Invesco DB Agriculture"),
    Instrument("CPER", AssetClass.COMMODITY, "United States Copper"),
    Instrument("PALL", AssetClass.COMMODITY, "Aberdeen Palladium"),
    Instrument("PPLT", AssetClass.COMMODITY, "Aberdeen Platinum"),
    Instrument("WEAT", AssetClass.COMMODITY, "Teucrium Wheat"),
)

BTC = Instrument("BTC-USD", AssetClass.CRYPTO, "Bitcoin")
CRYPTO_ALIASES = {
    "BTC": "BTC-USD",
    "BTCUSD": "BTC-USD",
    "BTC-USD": "BTC-USD",
    "XBTUSD": "BTC-USD",
    "XBT-USD": "BTC-USD",
    "BITCOIN": "BTC-USD",
}

assert len(OBSIDIAN) == 48


def normalize_symbol(symbol: str) -> str:
    key = symbol.upper().strip().replace(" ", "")
    return CRYPTO_ALIASES.get(key, key)


def is_crypto_symbol(symbol: str) -> bool:
    return normalize_symbol(symbol) == BTC.symbol


def is_aurora_mode(bot_mode: str) -> bool:
    return bot_mode.upper().strip() in {"DUKE", "AURORA"}


def instrument_for(symbol: str) -> Instrument:
    key = normalize_symbol(symbol)
    for item in OBSIDIAN:
        if item.symbol == key:
            return item
    if key == BTC.symbol:
        return BTC
    return Instrument(key, AssetClass.EQUITY, key)


def universe_for(bot_mode: str) -> tuple[Instrument, ...]:
    if is_aurora_mode(bot_mode):
        return OBSIDIAN + (BTC,)
    return OBSIDIAN
