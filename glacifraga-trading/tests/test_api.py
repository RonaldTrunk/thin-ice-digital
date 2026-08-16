from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.universe import OBSIDIAN
from tests.helpers import make_bars


def test_universe_size():
    assert len(OBSIDIAN) == 48


def test_signal_models_import_from_package():
    from app.models import SignalRequest, SignalResponse

    req = SignalRequest(symbol="BTC-USD")
    assert req.account_size == 100_000.0
    assert SignalResponse.__name__ == "SignalResponse"


def test_health_and_universe():
    client = TestClient(create_app(Settings(api_key=None, bot_mode="BARON")))
    health = client.get("/api/v1/health").json()
    assert health["ok"] is True
    assert "mode" not in health
    locked_out = client.get("/api/v1/universe")
    assert locked_out.status_code == 503
    partner = TestClient(create_app(Settings(api_key="secret", bot_mode="BARON")))
    universe = partner.get("/api/v1/universe", headers={"X-API-Key": "secret"}).json()
    assert universe["count"] == 48
    assert "MSFT" in universe["tickers"]


def test_baron_unlinked_without_keys():
    client = TestClient(create_app(Settings(api_key=None, alpaca_api_key=None, alpaca_api_secret=None)))
    data = client.get("/api/v1/baron/status").json()
    assert data["linked"] is False
    assert data["tickers"] == 48
    assert "ALPACA" not in (data.get("message") or "")


def test_generate_signal_with_fixture_market(monkeypatch, settings):
    bars = make_bars(220, last_volume=2_200_000)

    monkeypatch.setattr("app.main.fetch_bars", lambda symbol, cfg=None: bars)
    monkeypatch.setattr("app.main.fetch_vix", lambda cfg=None: 16.1)

    client = TestClient(create_app(Settings(api_key="secret", bot_mode="BARON", account_size=100_000)))
    response = client.post(
        "/api/v1/signals/generate",
        json={"symbol": "MSFT", "account_size": 100000},
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "MSFT"
    assert body["signal"] == "BUY"
    assert body["shares"] > 0
    assert body["audit"]["vix"]["label"] == "green"
    assert "reason" in body


def test_api_key_required_when_configured(monkeypatch, settings):
    bars = make_bars(220, last_volume=2_200_000)
    monkeypatch.setattr("app.main.fetch_bars", lambda symbol, cfg=None: bars)
    monkeypatch.setattr("app.main.fetch_vix", lambda cfg=None: 16.1)
    unconfigured = TestClient(create_app(Settings(api_key=None, bot_mode="BARON")))
    denied_missing = unconfigured.post("/api/v1/signals/generate", json={"symbol": "MSFT"})
    assert denied_missing.status_code == 503
    locked = Settings(api_key="secret", bot_mode="BARON")
    client = TestClient(create_app(locked))
    denied = client.post("/api/v1/signals/generate", json={"symbol": "MSFT"})
    assert denied.status_code == 401
    ok = client.post(
        "/api/v1/signals/generate",
        json={"symbol": "MSFT"},
        headers={"X-API-Key": "secret"},
    )
    assert ok.status_code == 200


def test_duke_universe_and_aurora_status():
    client = TestClient(create_app(Settings(api_key="secret", bot_mode="DUKE")))
    universe = client.get("/api/v1/universe", headers={"X-API-Key": "secret"}).json()
    assert universe["count"] == 49
    assert universe["strategy"] == "Glacifraga Aurora"
    assert "BTC-USD" in universe["tickers"]
    aurora = client.get("/api/v1/aurora/status").json()
    assert aurora["strategy"] == "Glacifraga Aurora"
    assert aurora["crypto"] is True
    assert aurora["tickers"] == 49
    duke = client.get("/api/v1/duke/status").json()
    assert duke["mode"] == "DUKE"


def test_generate_btc_signal(monkeypatch, settings):
    bars = make_bars(220, start=60_000, step=500, last_volume=2_200_000, range_pad=400)
    monkeypatch.setattr("app.main.fetch_bars", lambda symbol, cfg=None: bars)
    monkeypatch.setattr("app.main.fetch_vix", lambda cfg=None: 16.1)
    client = TestClient(create_app(Settings(api_key="secret", bot_mode="BARON")))
    response = client.post(
        "/api/v1/signals/generate",
        json={"symbol": "BTCUSD", "account_size": 100000},
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "BTC-USD"
    assert body["signal"] == "BUY"
    assert body["qty"] > 0
    assert body["audit"]["strategy"] == "Glacifraga Aurora"


def test_openapi_and_docs_are_private():
    client = TestClient(create_app(Settings(api_key="secret")))
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/docs").status_code == 404


def test_home_page_has_v5_copy():
    client = TestClient(create_app(Settings(api_key=None)))
    html = client.get("/").text
    assert "Thin Ice Digital Ltd" in html
    assert "Thin Ice Digital UG" not in html
    assert "Patience, clarity, and the right moment." in html
    assert "Lielā" not in html
    assert "2017–2026" in html
    assert "2.65" in html
    assert "$618,591" in html
    assert "2.19" not in html
    assert "+22.0%" in html
    assert "Aurora" in html
    assert "Bitcoin" in html
    assert "BTC-USD" in html
    assert "info@thinicedigital.com" in html
    assert "contact@glacifraga.com" not in html
    assert "Worker separate" not in html
    assert "ALPACA_API_KEY" not in html
    assert "Tearsheet v5" in html
    assert "−7.1%" in html
    assert "EOD scan" not in html
    assert "BOT_MODE" not in html
    assert "/api/v1/aurora/status" not in html
    assert 'href="/docs"' not in html
    assert "Request access" in html
    hero = client.get("/assets/kemeru-hero.png")
    assert hero.status_code == 200
    assert len(hero.content) > 10_000
