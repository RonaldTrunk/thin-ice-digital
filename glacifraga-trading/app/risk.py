from __future__ import annotations

from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class RiskPlan:
    price: float
    atr: float
    stop_distance: float
    stop_loss: float
    take_profit: float
    trail_atr_multiple: float
    risk_amount: float
    shares: int
    capped: bool


def position_plan(
    *,
    price: float,
    atr_value: float,
    account_size: float,
    risk_fraction: float = 0.01,
    stop_atr: float = 2.0,
    take_profit_atr: float = 4.0,
    trail_atr_multiple: float = 2.5,
    max_position_fraction: float = 0.10,
) -> RiskPlan | None:
    if price <= 0 or atr_value <= 0 or account_size <= 0:
        return None
    stop_distance = stop_atr * atr_value
    if stop_distance <= 0:
        return None
    risk_amount = account_size * risk_fraction
    raw_shares = floor(risk_amount / stop_distance)
    max_shares = floor((account_size * max_position_fraction) / price)
    shares = min(raw_shares, max_shares)
    if shares < 1:
        return None
    actual_risk = shares * stop_distance
    return RiskPlan(
        price=price,
        atr=atr_value,
        stop_distance=round(stop_distance, 4),
        stop_loss=round(price - stop_distance, 4),
        take_profit=round(price + take_profit_atr * atr_value, 4),
        trail_atr_multiple=trail_atr_multiple,
        risk_amount=round(actual_risk, 2),
        shares=shares,
        capped=shares < raw_shares,
    )
