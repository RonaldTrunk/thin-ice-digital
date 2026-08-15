import pytest

from app.guards import MarketHalt, PortfolioSnapshot, already_open, assert_scan_allowed


def test_spy_crash_suspends_longs():
    snap = PortfolioSnapshot(equity=100_000, prior_equity=100_000, spy_day_return=-0.04, open_symbols=set())
    with pytest.raises(MarketHalt, match="SPY"):
        assert_scan_allowed(snap)


def test_daily_loss_limit():
    snap = PortfolioSnapshot(equity=97_000, prior_equity=100_000, spy_day_return=0.0, open_symbols=set())
    with pytest.raises(MarketHalt, match="Daily loss"):
        assert_scan_allowed(snap)


def test_max_new_entries():
    snap = PortfolioSnapshot(
        equity=100_000, prior_equity=100_000, spy_day_return=0.0, open_symbols=set(), new_entries_today=6
    )
    with pytest.raises(MarketHalt, match="Max new entries"):
        assert_scan_allowed(snap)


def test_allows_normal_session():
    snap = PortfolioSnapshot(equity=100_500, prior_equity=100_000, spy_day_return=-0.01, open_symbols={"MSFT"})
    assert_scan_allowed(snap)
    assert already_open(snap, "msft")
    assert not already_open(snap, "AAPL")
