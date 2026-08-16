# Glacifraga Trading

Standalone source for [glacifraga.com](https://glacifraga.com) — Thin Ice Digital Ltd, Oxford.

This directory is the tree to push to **`6tbwmzr522-crypto/glacifraga-trading`** (Railway source). It is nested here only because this Cloud Agent workspace is `RonaldTrunk/thin-ice-digital` and cannot clone the private repo.

Long-only, cash-funded, rule-based. No leverage, no AI inference. Every signal carries an audit trail.

## Cut over glacifraga.com

Live glacifraga.com (Railway, last modified 23 Jul 2026) still shows the old 2022–2026 window (PF 2.19, Sharpe 6.01, UG, Latvian quote). Two ways to update it:

### A. Patch the live HTML in the private repo (fastest)

The production homepage is one HTML file with an inline Ķemeri hero. From a clone of `6tbwmzr522-crypto/glacifraga-trading`:

```bash
python scripts/patch_live_homepage.py --input path/to/current/index.html --output path/to/current/index.html
```

Or fetch the live page and write a drop-in:

```bash
python scripts/patch_live_homepage.py --output index.html
```

That rewrite (body only, hero image untouched):

- Stats → Obsidian v5: **2017–2026**, **+22.0% CAGR**, Sharpe **2.65**, ~61% win, −7.1% max DD, **$618,591** on $100k (PF 1.95 · Sortino 4.20 in the disclaimer)
- Quote → English only: *Patience, clarity, and the right moment.*
- Footer → **Thin Ice Digital Ltd**
- Restores `$` on the example signal (`$156.09`, Risk `$1,000`)

Push that file so Railway redeploys. `/docs` and Baron Live stay on the FastAPI app.

### B. Deploy this service

```
docker build -t glacifraga-trading .
```

Port **8080**. Env: `BOT_MODE`, `GLACIFRAGA_API_KEY`, `ALPACA_API_KEY`, `ALPACA_API_SECRET`. Point the glacifraga.com custom domain at the service.

`BOT_MODE=BARON` is Obsidian 48. `BOT_MODE=DUKE` (or `AURORA`) adds Bitcoin.

## Sleeves

| Mode | Strategy | Universe |
| --- | --- | --- |
| `BOT_MODE=BARON` | Obsidian | 48 equities + commodity ETFs, **no crypto** |
| `BOT_MODE=DUKE` or `AURORA` | Aurora | Obsidian **+ BTC-USD** |

Aurora uses the same 20-day breakout, SMA200, RSI(10) > 50, and 1.4× volume gates. Crypto trails at **3.0× ATR** (same as commodities) and sizes in **fractional BTC** so 1% risk still fires on a $100k book.

Bitcoin daily bars settle at **00:00 UTC**. A 16:05 ET equity scan would otherwise evaluate an unfinished UTC candle as a 20-day breakout. The engine drops the in-progress bar. Run the crypto sleeve on its own clock:

```bash
python -m app.scan --sleeve crypto   # 00:05 UTC
python -m app.scan --sleeve equity   # 16:05 ET
```

## Strategy (Obsidian)

| Gate | Rule |
| --- | --- |
| Breakout | Close above the prior 20-day high |
| Trend | Close above SMA200 |
| Momentum | RSI(10) > 50 |
| Volume | Last volume > 1.4× 20-day average |
| Risk | 1% of AUM; equities = whole shares, crypto = fractional qty; max ~10% AUM per name |
| Stops | Stop 2×ATR, partial target 4×ATR, trail 2.5×ATR equities / 3.0× commodities and Bitcoin |
| Regime | VIX scales confidence (green < 20, amber < 30, red otherwise) |
| Scan gates | Max 6 new entries; daily loss −2%; SPY day < −3% suspends longs |

Backtest on the site is Obsidian 48, 2017–24 Jul 2026: **+22.0% CAGR**, Sharpe **2.65**, max DD **−7.1%**, net P&L **$618,591** on $100k. Confidential — not indicative of future results. Aurora is the live crypto sleeve, not a second published tearsheet.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

- Site: http://localhost:8080
- Health: `GET /api/v1/health` (public)
- Signal: `POST /api/v1/signals/generate` with header `X-API-Key` (required; 503 if `GLACIFRAGA_API_KEY` is unset)
- Universe: `GET /api/v1/universe` (same key)
- `/docs` and `/openapi.json` are disabled

Set `GLACIFRAGA_API_KEY` on the Railway **web** service. Without it, generate and universe stay closed.

EOD scan (includes BTC when `BOT_MODE=DUKE`):

```bash
python -m app.scan
python -m app.scan --sleeve crypto
```

## Tests

```bash
pytest
```

## Granting Cursor access to the private repo

This agent is bound to `RonaldTrunk/thin-ice-digital`. The GitHub App installation for this workspace only lists that one repository. Granting the Cursor GitHub App access to `6tbwmzr522-crypto/glacifraga-trading` does **not** attach that repo to this run — a new Cloud Agent must be started with that repository selected in the picker.

1. GitHub account **`6tbwmzr522-crypto`**: [github.com/apps/cursor](https://github.com/apps/cursor) → select `glacifraga-trading` (or all repos)
2. Cursor dashboard → [Integrations](https://cursor.com/dashboard/integrations) → GitHub connected as that account
3. Start a **new** Cloud Agent whose repository is `6tbwmzr522-crypto/glacifraga-trading` (it must appear in the repo picker)
4. Prompt: `Update glacifraga.com with the v5 tearsheet, English-only quote, Ltd not UG. Add the Aurora/Duke BTC sleeve (UTC daily settlement).`
