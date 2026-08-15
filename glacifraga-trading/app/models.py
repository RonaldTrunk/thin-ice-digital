from __future__ import annotations

from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
    symbol: str
    account_size: float = Field(default=100_000.0, gt=0)


class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    price: float
    reason: str
    timestamp: str
    stop_loss: float | None = None
    take_profit: float | None = None
    shares: int | None = None
    qty: float | None = None
    stop_distance: float | None = None
    risk_amount: float | None = None
    audit: dict | None = None

    model_config = {"extra": "allow"}
