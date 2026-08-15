# Glacifraga Trading

Institutional breakout engine for [glacifraga.com](https://glacifraga.com) — Thin Ice Digital Ltd, Oxford.

Long-only, cash-funded, rule-based. No leverage, no AI inference. Every signal carries an audit trail.

## Sleeves

| Mode | Strategy | Universe |
| --- | --- | --- |
| `BOT_MODE=BARON` | Obsidian | 48 equities + commodity ETFs, **no crypto** |
| `BOT_MODE=DUKE` or `AURORA` | Aurora | Obsidian **+ BTC-USD** |

Aurora uses the same 20-day breakout, SMA200, RSI(10) > 50, and 1.4× volume gates. Crypto trails at **3.0× ATR** (same as commodities) and sizes in **fractional BTC** so 1% risk still fires on a $100k book.

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
cd glacifraga-trading
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

- Site: http://localhost:8080
- API docs: http://localhost:8080/docs
- Health: `GET /api/v1/health`
- Signal: `POST /api/v1/signals/generate` with `{"symbol":"MSFT","account_size":100000}`
- Bitcoin: `POST /api/v1/signals/generate` with `{"symbol":"BTC-USD"}` (aliases: `BTC`, `BTCUSD`)
- Baron: `GET /api/v1/baron/status`
- Aurora: `GET /api/v1/aurora/status` (alias `GET /api/v1/duke/status`)

Market data: Stooq daily bars, with Yahoo Finance as fallback (Yahoo first for Bitcoin). Set `GLACIFRAGA_API_KEY` to require `X-API-Key` on signal generation. Set Alpaca paper keys to mirror live positions on the Baron panel.

EOD scan (includes BTC when `BOT_MODE=DUKE`):

```bash
python -m app.scan
```

## Tests

```bash
pytest
```

## Deploy

Railway (or any container host). Port **8080**. Build from the repository root:

```
docker build -f glacifraga-trading/Dockerfile .
```

Env: `BOT_MODE`, `GLACIFRAGA_API_KEY`, `ALPACA_API_KEY`, `ALPACA_API_SECRET`. Point `glacifraga.com` at the service. Use `BOT_MODE=DUKE` for the Aurora crypto sleeve.
