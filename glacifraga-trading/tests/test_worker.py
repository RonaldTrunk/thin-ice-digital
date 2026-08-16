from datetime import datetime
from zoneinfo import ZoneInfo

from app.worker import due_crypto_scan, due_equity_scan

ET = ZoneInfo("America/New_York")


def test_equity_scan_waits_until_1605_et_weekdays():
    friday_noon = datetime(2026, 8, 14, 16, 0, tzinfo=ET)  # 16:00 ET
    friday_scan = datetime(2026, 8, 14, 16, 5, tzinfo=ET)
    saturday = datetime(2026, 8, 15, 17, 0, tzinfo=ET)
    assert due_equity_scan(friday_noon, None) is False
    assert due_equity_scan(friday_scan, None) is True
    assert due_equity_scan(friday_scan, friday_scan.date()) is False
    assert due_equity_scan(saturday, None) is False


def test_crypto_scan_is_utc_and_aurora_only():
    utc_fire = datetime.fromisoformat("2026-08-16T00:05:00+00:00")
    utc_early = datetime.fromisoformat("2026-08-16T00:04:00+00:00")
    assert due_crypto_scan(utc_early, None, aurora=True) is False
    assert due_crypto_scan(utc_fire, None, aurora=True) is True
    assert due_crypto_scan(utc_fire, utc_fire.date(), aurora=True) is False
    assert due_crypto_scan(utc_fire, None, aurora=False) is False
