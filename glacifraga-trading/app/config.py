from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False, populate_by_name=True
    )

    api_key: str | None = Field(default=None, validation_alias=AliasChoices("GLACIFRAGA_API_KEY"))
    bot_mode: str = Field(default="BARON", validation_alias=AliasChoices("BOT_MODE"))
    account_size: float = 100_000.0

    alpaca_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("ALPACA_API_KEY", "APCA_API_KEY_ID")
    )
    alpaca_api_secret: str | None = Field(
        default=None, validation_alias=AliasChoices("ALPACA_API_SECRET", "APCA_API_SECRET_KEY")
    )
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets",
        validation_alias=AliasChoices("ALPACA_BASE_URL", "APCA_API_BASE_URL"),
    )

    market_timeout_s: float = 12.0
    cache_ttl_s: float = 900.0

    risk_fraction: float = 0.01
    stop_atr: float = 2.0
    take_profit_atr: float = 4.0
    trail_atr_equity: float = 2.5
    trail_atr_commodity: float = 3.0
    max_position_fraction: float = 0.10
    breakout_lookback: int = 20
    rsi_period: int = 10
    rsi_threshold: float = 50.0
    volume_lookback: int = 20
    volume_multiple: float = 1.4
    sma_period: int = 200
    atr_period: int = 14
    max_new_entries: int = 6
    daily_loss_limit: float = -0.02
    spy_crash_day: float = -0.03
    min_buy_confidence: float = 0.55
    crypto_qty_precision: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
