import pytest

from app.config import Settings, get_settings
from app.market import _CACHE


@pytest.fixture(autouse=True)
def _reset_caches():
    get_settings.cache_clear()
    _CACHE.clear()
    yield
    get_settings.cache_clear()
    _CACHE.clear()


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key=None, bot_mode="BARON", account_size=100_000)
