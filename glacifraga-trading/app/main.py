from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.baron import baron_status
from app.config import Settings, get_settings
from app.engine import generate_signal
from app.market import MarketDataError, fetch_bars, fetch_vix
from app.models import SignalRequest, SignalResponse
from app.universe import instrument_for, is_aurora_mode, universe_for

PACKAGE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_DIR.parent
WEB_DIR = PACKAGE_DIR / "web"


def _first_dir(*candidates: Path) -> Path | None:
    for path in candidates:
        if path.is_dir():
            return path
    return None


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()
    app = FastAPI(
        title="Glacifraga Trading",
        version=__version__,
        description=(
            "\n## Automated Breakout Strategy Engine\n\n"
            "**Multi-asset signal generation** across equities, commodities and crypto.\n\n"
            "- Real-time momentum breakout signals\n"
            "- ATR-based position sizing and risk management\n"
            "- VIX regime filter for market stress detection\n"
            "- Full audit trail on every signal\n"
            "- White-label ready via REST API\n\n"
            "**Authentication:** Use your API key in the `X-API-Key` header.\n"
        ),
    )

    def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
        expected = cfg.api_key
        if not expected:
            return
        if x_api_key != expected:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    @app.get("/api/v1/health")
    def health() -> dict:
        return {"ok": True, "version": __version__, "mode": cfg.bot_mode.upper()}

    @app.get("/api/v1/universe")
    def universe() -> dict:
        names = universe_for(cfg.bot_mode)
        return {
            "mode": cfg.bot_mode.upper(),
            "strategy": "Glacifraga Aurora" if is_aurora_mode(cfg.bot_mode) else "Glacifraga Obsidian",
            "tickers": [item.symbol for item in names],
            "count": len(names),
            "crypto": ["BTC-USD"] if is_aurora_mode(cfg.bot_mode) else [],
        }

    @app.post(
        "/api/v1/signals/generate",
        response_model=SignalResponse,
        tags=["signals"],
        summary="Generate Signals",
        dependencies=[Depends(require_api_key)],
    )
    def generate(request: SignalRequest) -> SignalResponse:
        instrument = instrument_for(request.symbol)
        try:
            bars = fetch_bars(instrument.symbol, cfg)
            vix = fetch_vix(cfg)
        except MarketDataError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        result = generate_signal(
            bars,
            symbol=instrument.symbol,
            account_size=request.account_size,
            vix=vix,
            instrument=instrument,
            settings=cfg,
        )
        return SignalResponse.model_validate(result.as_api())

    @app.get("/api/v1/baron/status", tags=["baron"], summary="Baron Status")
    def baron() -> dict:
        return baron_status(cfg)

    @app.get("/api/v1/aurora/status", tags=["baron"], summary="Aurora Status")
    def aurora() -> dict:
        return baron_status(cfg)

    @app.get("/api/v1/duke/status", tags=["baron"], summary="Duke Status")
    def duke() -> dict:
        return baron_status(cfg)

    index = WEB_DIR / "index.html"
    if index.exists():
        @app.get("/", include_in_schema=False)
        def home() -> FileResponse:
            return FileResponse(index)

        assets = _first_dir(WEB_DIR / "assets", REPO_ROOT / "assets")
        fonts = _first_dir(WEB_DIR / "fonts", REPO_ROOT / "fonts")
        css = WEB_DIR / "css"
        if assets:
            app.mount("/assets", StaticFiles(directory=assets), name="assets")
        if fonts:
            app.mount("/fonts", StaticFiles(directory=fonts), name="fonts")
        if css.is_dir():
            app.mount("/css", StaticFiles(directory=css), name="css")

    return app


app = create_app()
