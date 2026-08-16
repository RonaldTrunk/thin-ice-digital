from app.market import parse_stooq_csv, parse_yahoo_chart, yahoo_symbol
from app.universe import instrument_for, universe_for


def test_stooq_csv_parse():
    csv = """Date,Open,High,Low,Close,Volume
2024-01-02,100,101,99,100.5,1000
2024-01-03,100.5,102,100,101.5,1100
"""
    bars = parse_stooq_csv(csv)
    assert len(bars) == 2
    assert bars[0].close == 100.5
    assert bars[1].volume == 1100


def test_duke_adds_bitcoin():
    baron = universe_for("BARON")
    duke = universe_for("DUKE")
    assert len(baron) == 48
    assert len(duke) == 49
    assert duke[-1].symbol == "BTC-USD"


def test_instrument_aliases():
    assert instrument_for("btc").symbol == "BTC-USD"
    assert instrument_for("btcusd").asset_class.value == "crypto"
    assert instrument_for("XBT-USD").symbol == "BTC-USD"
    assert instrument_for("gdx").asset_class.value == "commodity"


def test_yahoo_chart_parse():
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1704153600, 1704240000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [42000.0, 43000.0],
                                "high": [42500.0, 44000.0],
                                "low": [41000.0, 42800.0],
                                "close": [42200.0, 43500.0],
                                "volume": [100.0, 150.0],
                            }
                        ]
                    },
                }
            ]
        }
    }
    bars = parse_yahoo_chart(payload)
    assert len(bars) == 2
    assert bars[1].close == 43500.0
    assert bars[1].volume == 150.0
    assert yahoo_symbol("BTCUSD") == "BTC-USD"
    assert yahoo_symbol("VIX") == "^VIX"


def test_equity_falls_back_to_yahoo(monkeypatch):
    from app import market

    yahoo_bars = parse_stooq_csv(
        "Date,Open,High,Low,Close,Volume\n"
        + "\n".join(f"2024-01-{i:02d},100,101,99,100.5,1000" for i in range(1, 32))
    )

    def boom(symbol, **kwargs):
        raise market.MarketDataError("stooq blocked")

    monkeypatch.setattr(market, "fetch_stooq_bars", boom)
    monkeypatch.setattr(market, "fetch_yahoo_bars", lambda symbol, **kwargs: yahoo_bars)
    bars = market._fetch_uncached("MSFT", timeout=1)
    assert len(bars) >= 30
