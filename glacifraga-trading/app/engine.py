from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

from app.config import Settings, get_settings
from app.indicators import atr, prior_high, rsi, sma, volume_ratio
from app.indicators import Bar
from app.risk import RiskPlan, position_plan
from app.universe import AssetClass, Instrument, instrument_for


def vix_regime(vix: float | None) -> dict[str, Any]:
    if vix is None:
        return {"value": None, "label": "unknown", "multiplier": 0.85}
    if vix < 20:
        return {"value": round(vix, 2), "label": "green", "multiplier": 1.0}
    if vix < 30:
        return {"value": round(vix, 2), "label": "amber", "multiplier": 0.75}
    return {"value": round(vix, 2), "label": "red", "multiplier": 0.4}


def _confidence(
    *,
    breakout: bool,
    trend: bool,
    rsi_value: float | None,
    rsi_ok: bool,
    volume_ok: bool,
    volume_mult: float | None,
    vix_mult: float,
    rsi_threshold: float,
) -> float:
    score = 0.0
    if breakout:
        score += 0.25
    if trend:
        score += 0.20
    if rsi_ok and rsi_value is not None:
        score += 0.15
        if rsi_value >= 70:
            score += 0.10
    if volume_ok and volume_mult is not None:
        score += 0.15
        if volume_mult >= 2.0:
            score += 0.10
    return round(min(score * vix_mult, 0.99), 4)


@dataclass
class SignalResult:
    symbol: str
    signal: str
    confidence: float
    price: float
    reason: str
    timestamp: str
    stop_loss: float | None = None
    take_profit: float | None = None
    shares: int | None = None
    stop_distance: float | None = None
    risk_amount: float | None = None
    audit: dict[str, Any] = field(default_factory=dict)

    def as_api(self) -> dict[str, Any]:
        payload = {
            "symbol": self.symbol,
            "signal": self.signal,
            "confidence": self.confidence,
            "price": self.price,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "shares": self.shares,
            "stop_distance": self.stop_distance,
            "risk_amount": self.risk_amount,
            "audit": self.audit,
        }
        return payload


def generate_signal(
    bars: Sequence[Bar],
    *,
    symbol: str,
    account_size: float = 100_000.0,
    vix: float | None = None,
    instrument: Instrument | None = None,
    settings: Settings | None = None,
    as_of: datetime | None = None,
) -> SignalResult:
    cfg = settings or get_settings()
    inst = instrument or instrument_for(symbol)
    stamp = (as_of or datetime.now(timezone.utc)).isoformat()
    if len(bars) < cfg.sma_period + 1:
        return SignalResult(
            symbol=inst.symbol,
            signal="HOLD",
            confidence=0.0,
            price=bars[-1].close if bars else 0.0,
            reason=f"Insufficient history ({len(bars)} bars; need {cfg.sma_period + 1}).",
            timestamp=stamp,
            audit={"bars": len(bars), "required": cfg.sma_period + 1},
        )

    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    volumes = [b.volume for b in bars]
    price = bars[-1].close
    breakout_level = prior_high(highs, cfg.breakout_lookback)
    rsi_value = rsi(closes, cfg.rsi_period)
    sma_value = sma(closes, cfg.sma_period)
    vol_mult = volume_ratio(volumes, cfg.volume_lookback)
    atr_value = atr(bars, cfg.atr_period)
    regime = vix_regime(vix)

    breakout_ok = breakout_level is not None and price > breakout_level
    trend_ok = sma_value is not None and price > sma_value
    rsi_ok = rsi_value is not None and rsi_value > cfg.rsi_threshold
    volume_ok = vol_mult is not None and vol_mult > cfg.volume_multiple

    trail_mult = (
        cfg.trail_atr_commodity
        if inst.asset_class in {AssetClass.COMMODITY, AssetClass.CRYPTO}
        else cfg.trail_atr_equity
    )
    plan: RiskPlan | None = None
    if atr_value is not None:
        plan = position_plan(
            price=price,
            atr_value=atr_value,
            account_size=account_size,
            risk_fraction=cfg.risk_fraction,
            stop_atr=cfg.stop_atr,
            take_profit_atr=cfg.take_profit_atr,
            trail_atr_multiple=trail_mult,
            max_position_fraction=cfg.max_position_fraction,
        )

    confidence = _confidence(
        breakout=breakout_ok,
        trend=trend_ok,
        rsi_value=rsi_value,
        rsi_ok=rsi_ok,
        volume_ok=volume_ok,
        volume_mult=vol_mult,
        vix_mult=regime["multiplier"],
        rsi_threshold=cfg.rsi_threshold,
    )

    failures: list[str] = []
    if not breakout_ok:
        failures.append(f"no {cfg.breakout_lookback}d high breakout")
    if not trend_ok:
        failures.append("below SMA200")
    if not rsi_ok:
        failures.append(f"RSI({cfg.rsi_period}) ≤ {cfg.rsi_threshold:g}")
    if not volume_ok:
        failures.append(f"volume ≤ {cfg.volume_multiple:g}× 20d average")
    if plan is None:
        failures.append("position below minimum size")

    buy = not failures and confidence >= cfg.min_buy_confidence
    signal = "BUY" if buy else "HOLD"
    if buy:
        reason = (
            f"{cfg.breakout_lookback}-day high breakout with RSI({cfg.rsi_period}) "
            f"{rsi_value:.1f}, volume {vol_mult:.2f}×, SMA200 trend, VIX {regime['label']}."
        )
    else:
        reason = "HOLD — " + "; ".join(failures) if failures else "HOLD — confidence below threshold."

    audit = {
        "strategy": "Glacifraga Obsidian" if inst.asset_class != AssetClass.CRYPTO else "Glacifraga Aurora",
        "asset_class": inst.asset_class.value,
        "breakout": {
            "lookback": cfg.breakout_lookback,
            "level": None if breakout_level is None else round(breakout_level, 4),
            "close": round(price, 4),
            "passed": breakout_ok,
        },
        "sma200": {
            "value": None if sma_value is None else round(sma_value, 4),
            "passed": trend_ok,
        },
        "rsi": {
            "period": cfg.rsi_period,
            "value": None if rsi_value is None else round(rsi_value, 2),
            "threshold": cfg.rsi_threshold,
            "passed": rsi_ok,
        },
        "volume": {
            "ratio": None if vol_mult is None else round(vol_mult, 3),
            "threshold": cfg.volume_multiple,
            "passed": volume_ok,
        },
        "atr": None if atr_value is None else round(atr_value, 4),
        "vix": regime,
        "risk": {
            "fraction": cfg.risk_fraction,
            "stop_atr": cfg.stop_atr,
            "take_profit_atr": cfg.take_profit_atr,
            "trail_atr": trail_mult,
            "max_position_fraction": cfg.max_position_fraction,
            "capped": None if plan is None else plan.capped,
        },
        "gates": failures,
    }

    return SignalResult(
        symbol=inst.symbol,
        signal=signal,
        confidence=confidence,
        price=round(price, 4),
        reason=reason,
        timestamp=stamp,
        stop_loss=None if plan is None else plan.stop_loss,
        take_profit=None if plan is None else plan.take_profit,
        shares=None if plan is None else plan.shares,
        stop_distance=None if plan is None else plan.stop_distance,
        risk_amount=None if plan is None else plan.risk_amount,
        audit=audit,
    )
