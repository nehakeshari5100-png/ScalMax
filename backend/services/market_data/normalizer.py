from typing import List, Optional
from datetime import datetime, timezone
from services.market_data.models import Candle


TIMEFRAME_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
}


def normalize_candle(
    raw: dict,
    exchange: str,
    symbol: str,
    timeframe: str,
) -> Optional[Candle]:
    try:
        if exchange == "binance":
            return _normalize_binance(raw, symbol, timeframe)
        elif exchange == "bybit":
            return _normalize_bybit(raw, symbol, timeframe)
        elif exchange == "hyperliquid":
            return _normalize_hyperliquid(raw, symbol, timeframe)
        return None
    except (KeyError, TypeError, ValueError) as e:
        return None


def normalize_candles(
    raw_list: List[dict],
    exchange: str,
    symbol: str,
    timeframe: str,
) -> List[Candle]:
    candles = []
    for raw in raw_list:
        candle = normalize_candle(raw, exchange, symbol, timeframe)
        if candle:
            candles.append(candle)
    candles.sort(key=lambda c: c.timestamp)
    return candles


def _normalize_binance(raw: dict, symbol: str, timeframe: str) -> Candle:
    return Candle(
        timestamp=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
        exchange="binance",
        symbol=symbol,
        timeframe=timeframe,
    )


def _normalize_bybit(raw: dict, symbol: str, timeframe: str) -> Candle:
    ts = int(raw.get("timestamp", raw.get("start", 0)))
    if len(str(ts)) == 10:
        ts *= 1000
    return Candle(
        timestamp=ts,
        open=float(raw.get("open", 0)),
        high=float(raw.get("high", 0)),
        low=float(raw.get("low", 0)),
        close=float(raw.get("close", 0)),
        volume=float(raw.get("volume", raw.get("vol", 0))),
        exchange="bybit",
        symbol=symbol,
        timeframe=timeframe,
    )


def _normalize_hyperliquid(raw: dict, symbol: str, timeframe: str) -> Candle:
    raw_candle = raw.get("T", {})
    return Candle(
        timestamp=int(raw_candle.get("t", raw_candle.get("timestamp", raw.get("t", 0)))),
        open=float(raw_candle.get("o", raw_candle.get("open", raw.get("o", 0)))),
        high=float(raw_candle.get("h", raw_candle.get("high", raw.get("h", 0)))),
        low=float(raw_candle.get("l", raw_candle.get("low", raw.get("l", 0)))),
        close=float(raw_candle.get("c", raw_candle.get("close", raw.get("c", 0)))),
        volume=float(raw_candle.get("v", raw_candle.get("volume", raw.get("v", 0)))),
        exchange="hyperliquid",
        symbol=symbol,
        timeframe=timeframe,
    )


def aggregate_candles(
    candles: List[Candle],
    source_timeframe: str,
    target_timeframe: str,
) -> List[Candle]:
    if source_timeframe == target_timeframe:
        return candles

    target_ms = TIMEFRAME_MS.get(target_timeframe)
    if not target_ms:
        return []

    grouped: dict = {}
    for candle in candles:
        aligned_ts = (candle.timestamp // target_ms) * target_ms
        if aligned_ts not in grouped:
            grouped[aligned_ts] = {
                "timestamp": aligned_ts,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": 0.0,
                "exchange": candle.exchange,
                "symbol": candle.symbol,
                "timeframe": target_timeframe,
            }

        g = grouped[aligned_ts]
        g["high"] = max(g["high"], candle.high)
        g["low"] = min(g["low"], candle.low)
        g["close"] = candle.close
        g["volume"] += candle.volume

    result = [Candle(**v) for v in grouped.values()]
    result.sort(key=lambda c: c.timestamp)
    return result


def round_timestamp(ts: int, timeframe: str) -> int:
    ms = TIMEFRAME_MS.get(timeframe, 60_000)
    return (ts // ms) * ms


def get_timeframe_ms(timeframe: str) -> int:
    return TIMEFRAME_MS.get(timeframe, 60_000)
