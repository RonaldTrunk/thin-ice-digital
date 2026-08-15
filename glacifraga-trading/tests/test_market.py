from app.market import parse_stooq_csv
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
    assert instrument_for("gdx").asset_class.value == "commodity"
