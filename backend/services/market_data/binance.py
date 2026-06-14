import asyncio
import json
import logging
import time
from typing import List, Optional, Dict, Any
import httpx
from services.market_data.base import BaseExchange
from services.market_data.models import (
    Exchange, Candle, Ticker, OrderBook, OrderBookLevel,
)
from services.market_data.normalizer import normalize_candle, normalize_candles

logger = logging.getLogger(__name__)

BINANCE_SYMBOL_MAP = {
    "BTCUSDT": "btcusdt",
    "ETHUSDT": "ethusdt",
    "SOLUSDT": "solusdt",
    "BNBUSDT": "bnbusdt",
    "XRPUSDT": "xrpusdt",
}

BINANCE_TIMEFRAME_MAP = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
}


class BinanceExchange(BaseExchange):
    def __init__(self, cache):
        super().__init__(
            exchange=Exchange.BINANCE,
            cache=cache,
            ws_url="wss://stream.binance.com:9443/ws",
            rest_url="https://api.binance.com",
        )
        self._http = httpx.AsyncClient(timeout=10.0)
        self._listen_key: Optional[str] = None

    @property
    def name(self) -> str:
        return "binance"

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> List[Candle]:
        tf = BINANCE_TIMEFRAME_MAP.get(timeframe, "5m")
        sym = BINANCE_SYMBOL_MAP.get(symbol.upper(), symbol.lower())

        try:
            response = await self._http.get(
                f"{self._rest_url}/api/v3/klines",
                params={
                    "symbol": sym.upper(),
                    "interval": tf,
                    "limit": min(limit, 1000),
                },
            )
            response.raise_for_status()
            raw_data = response.json()
            candles = normalize_candles(raw_data, "binance", symbol.upper(), timeframe)
            return candles
        except Exception as e:
            logger.error(f"[Binance] fetch_candles error: {e}")
            return []

    async def fetch_ticker(self, symbol: str) -> Optional[Ticker]:
        sym = BINANCE_SYMBOL_MAP.get(symbol.upper(), symbol.lower())
        try:
            response = await self._http.get(
                f"{self._rest_url}/api/v3/ticker/24hr",
                params={"symbol": sym.upper()},
            )
            response.raise_for_status()
            data = response.json()
            return Ticker(
                symbol=symbol.upper(),
                price=float(data["lastPrice"]),
                change_24h=float(data["priceChangePercent"]),
                volume_24h=float(data["volume"]),
                high_24h=float(data["highPrice"]),
                low_24h=float(data["lowPrice"]),
                exchange="binance",
                timestamp=int(data["closeTime"]),
            )
        except Exception as e:
            logger.error(f"[Binance] fetch_ticker error: {e}")
            return None

    async def fetch_order_book(self, symbol: str, limit: int = 25) -> Optional[OrderBook]:
        sym = BINANCE_SYMBOL_MAP.get(symbol.upper(), symbol.lower())
        try:
            response = await self._http.get(
                f"{self._rest_url}/api/v3/depth",
                params={"symbol": sym.upper(), "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            bids = [OrderBookLevel(price=float(b[0]), volume=float(b[1])) for b in data["bids"][:limit]]
            asks = [OrderBookLevel(price=float(a[0]), volume=float(a[1])) for a in data["asks"][:limit]]

            best_bid = bids[0].price if bids else 0.0
            best_ask = asks[0].price if asks else 0.0

            return OrderBook(
                symbol=symbol.upper(),
                exchange="binance",
                bids=bids,
                asks=asks,
                spread=best_ask - best_bid,
                mid_price=(best_bid + best_ask) / 2,
                timestamp=int(time.time() * 1000),
            )
        except Exception as e:
            logger.error(f"[Binance] fetch_order_book error: {e}")
            return None

    async def _build_ws_subscriptions(self, symbols: List[str]) -> List[Dict]:
        streams = []
        for sym in symbols:
            s = BINANCE_SYMBOL_MAP.get(sym.upper(), sym.lower())
            streams.extend([
                f"{s}@kline_1m",
                f"{s}@kline_5m",
                f"{s}@kline_15m",
                f"{s}@kline_1h",
                f"{s}@ticker",
                f"{s}@depth20@100ms",
            ])

        return [
            {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": 1,
            }
        ]

    def _handle_ws_message(self, raw: dict):
        if not isinstance(raw, dict):
            return

        event_type = raw.get("e", "")
        symbol = raw.get("s", "")

        if not symbol:
            return

        symbol = symbol.upper()

        if event_type == "kline":
            k = raw.get("k", {})
            tf_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h",
            }
            tf = tf_map.get(k.get("i", ""))
            if not tf:
                return

            candle = Candle(
                timestamp=int(k["t"]),
                open=float(k["o"]),
                high=float(k["h"]),
                low=float(k["l"]),
                close=float(k["c"]),
                volume=float(k["v"]),
                exchange="binance",
                symbol=symbol,
                timeframe=tf,
            )
            self._cache.set("candles", candle, "binance", symbol, tf, ttl=5)
            self._emit_candle(candle)

        elif event_type == "24hrTicker":
            ticker = Ticker(
                symbol=symbol,
                price=float(raw.get("c", 0)),
                change_24h=float(raw.get("P", 0)),
                volume_24h=float(raw.get("v", 0)),
                high_24h=float(raw.get("h", 0)),
                low_24h=float(raw.get("l", 0)),
                exchange="binance",
                timestamp=int(raw.get("E", 0)),
            )
            self._cache.set("ticker", ticker, "binance", symbol, ttl=10)
            self._emit_ticker(ticker)

        elif event_type == "depthUpdate":
            symbol_upper = symbol
            self._cache.set("orderbook", raw, "binance", symbol_upper, ttl=5)

    async def stop(self):
        await super().stop()
        await self._http.aclose()
