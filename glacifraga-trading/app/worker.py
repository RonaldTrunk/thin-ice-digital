"""Long-running Baron worker for Railway.

glacifraga-web is uvicorn. Baron-worker must stay alive; a one-shot
`python -m app.scan` exits and Railway marks the service as crashed.

Start command: python -m app.worker
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.config import get_settings
from app.scan import run_scan
from app.session import CRYPTO_SCAN_UTC, EQUITY_SCAN_ET, ET, aware_utc
from app.universe import is_aurora_mode

log = logging.getLogger("glacifraga.worker")
POLL_SECONDS = 30


def due_equity_scan(now: datetime, last_day) -> bool:
    et = aware_utc(now).astimezone(ET)
    if et.weekday() >= 5:
        return False
    if et.time() < EQUITY_SCAN_ET:
        return False
    return last_day != et.date()


def due_crypto_scan(now: datetime, last_day, *, aurora: bool) -> bool:
    if not aurora:
        return False
    utc = aware_utc(now).astimezone(timezone.utc)
    if utc.time() < CRYPTO_SCAN_UTC:
        return False
    return last_day != utc.date()


def _run_sleeve(sleeve: str) -> None:
    result = run_scan(sleeve=sleeve)
    log.info(
        "%s scan halt=%s buys=%s holds=%s errors=%s",
        sleeve,
        result.get("halt"),
        len(result.get("buys") or []),
        result.get("hold_count"),
        len(result.get("errors") or []),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = get_settings()
    last_equity = None
    last_crypto = None
    log.info("baron-worker up mode=%s", cfg.bot_mode.upper())
    while True:
        now = datetime.now(timezone.utc)
        try:
            if due_equity_scan(now, last_equity):
                _run_sleeve("equity")
                last_equity = now.astimezone(ET).date()
            if due_crypto_scan(now, last_crypto, aurora=is_aurora_mode(cfg.bot_mode)):
                _run_sleeve("crypto")
                last_crypto = now.astimezone(timezone.utc).date()
        except Exception:
            log.exception("scan failed; worker stays up")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
