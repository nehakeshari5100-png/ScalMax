import asyncio
import json
import logging
import time
import struct
from typing import List, Optional, Dict, Any
import httpx
from services.market_data.base import BaseExchange
from services.market_data.models import (
    Exchange, Candle, Ticker, OrderBook, OrderBookLevel,
)

logger = logging.getLogger(__name__)

HL_SYMBOL_MAP = {
    "BTCUSDT": "BTC",
    "ETHUSDT": "ETH",
    "SOLUSDT": "SOL",
    "BNBUSDT": "BNB",
    "XRPUSDT": "XRP",
}

HL_REVERSE_MAP = {v: k for k, v in HL_SYMBOL_MAP.items()}


class HyperliquidExchange(BaseExchange):
    def __init__(self, cache):
        super().__init__(
            exchange=Exchange.HYPERLIQUID,
            cache=cache,
            ws_url="wss://api.hyperliquid.xyz/ws",
            rest_url="https://api.hyperliquid.xyz",
        )
        self._http = httpx.AsyncClient(timeout=10.0)
        self._candle_buffer: Dict[str, List[dict]] = {}
        self._last_candle_emit: Dict[str, int] = {}

    @property
    def name(self) -> str:
        return "hyperliquid"

    def _to_hl_symbol(self, symbol: str) -> str:
        return HL_SYMBOL_MAP.get(symbol.upper(), symbol.replace("USDT", ""))

    def _from_hl_symbol(self, hl_symbol: str) -> str:
        return HL_REVERSE_MAP.get(hl_symbol.upper(), f"{hl_symbol.upper()}USDT")

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> List[Candle]:
        hl_sym = self._to_hl_symbol(symbol)
        tf_ms = {
            "1m": 60000, "3m": 180000, "5m": 300000,
            "15m": 900000, "1h": 3600000, "4h": 14400000,
        }.get(timeframe, 300000)

        interval = timeframe.replace("m", "min").replace("h", "hour")

        try:
            response = await self._http.post(
                f"{self._rest_url}/info",
                json={
                    "type": "candleHistory",
                    "coin": hl_sym,
                    "interval": interval,
                    "limit": min(limit, 1000),
                },
            )
            response.raise_for_status()
            raw_data = response.json()

            candles = []
            for raw in raw_data:
                ts = int(raw.get("t", raw.get("time", 0)))
                if len(str(ts)) == 10:
                    ts *= 1000

                candle = Candle(
                    timestamp=ts,
                    open=float(raw.get("o", raw.get("open", 0))),
                    high=float(raw.get("h", raw.get("high", 0))),
                    low=float(raw.get("l", raw.get("low", 0))),
                    close=float(raw.get("c", raw.get("close", 0))),
                    volume=float(raw.get("v", raw.get("volume", 0))),
                    exchange="hyperliquid",
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                )
                candles.append(candle)

            candles.sort(key=lambda c: c.timestamp)
            return candles
        except Exception as e:
            logger.error(f"[Hyperliquid] fetch_candles error: {e}")
            return []

    async def fetch_ticker(self, symbol: str) -> Optional[Ticker]:
        hl_sym = self._to_hl_symbol(symbol)
        try:
            response = await self._http.post(
                f"{self._rest_url}/info",
                json={"type": "allMids"},
            )
            response.raise_for_status()
            data = response.json()

            mid = float(data.get(hl_sym, 0))
            if mid == 0:
                return None

            return Ticker(
                symbol=symbol.upper(),
                price=mid,
                change_24h=0.0,
                volume_24h=0.0,
                high_24h=mid,
                low_24h=mid,
                exchange="hyperliquid",
                timestamp=int(time.time() * 1000),
            )
        except Exception as e:
            logger.error(f"[Hyperliquid] fetch_ticker error: {e}")
            return None

    async def fetch_order_book(self, symbol: str, limit: int = 25) -> Optional[OrderBook]:
        hl_sym = self._to_hl_symbol(symbol)
        try:
            response = await self._http.post(
                f"{self._rest_url}/info",
                json={"type": "l2Book", "coin": hl_sym},
            )
            response.raise_for_status()
            data = response.json()

            bids_data = data.get("bids", data.get("levels", [{}])[0].get("bids", []))[:limit]
            asks_data = data.get("asks", data.get("levels", [{}])[0].get("asks", []))[:limit]

            bids = [OrderBookLevel(price=float(b[0]), volume=float(b[1])) for b in bids_data]
            asks = [OrderBookLevel(price=float(a[0]), volume=float(a[1])) for a in asks_data]

            best_bid = bids[0].price if bids else 0.0
            best_ask = asks[0].price if asks else 0.0

            return OrderBook(
                symbol=symbol.upper(),
                exchange="hyperliquid",
                bids=bids,
                asks=asks,
                spread=best_ask - best_bid,
                mid_price=(best_bid + best_ask) / 2,
                timestamp=int(time.time() * 1000),
            )
        except Exception as e:
            logger.error(f"[Hyperliquid] fetch_order_book error: {e}")
            return None

    async def _build_ws_subscriptions(self, symbols: List[str]) -> List[Dict]:
        subs = []
        for sym in symbols:
            hl_sym = self._to_hl_symbol(sym)
            subs.append({
                "type": "subscribe",
                "channel": "candle",
                "coin": hl_sym,
                "interval": "5m",
            })
            subs.append({
                "type": "subscribe",
                "channel": "book",
                "coin": hl_sym,
            })
            subs.append({
                "type": "subscribe",
                "channel": "allMids",
            })

        return subs

    def _handle_ws_message(self, raw: dict):
        if not isinstance(raw, dict):
            return

        channel = raw.get("channel", "")
        data = raw.get("data", {})

        if not channel:
            return

        if channel == "candle":
            coin = data.get("coin", data.get("s", ""))
            symbol = self._from_hl_symbol(coin)

            tf_map = {"5m": "5m"}
            tf = tf_map.get(data.get("interval", "5m"), "5m")

            ts = int(data.get("t", data.get("time", 0)))
            if len(str(ts)) == 10:
                ts *= 1000

            candle = Candle(
                timestamp=ts,
                open=float(data.get("o", data.get("open", 0))),
                high=float(data.get("h", data.get("high", 0))),
                low=float(data.get("l", data.get("low", 0))),
                close=float(data.get("c", data.get("close", 0))),
                volume=float(data.get("v", data.get("volume", 0))),
                exchange="hyperliquid",
                symbol=symbol,
                timeframe=tf,
            )
            self._cache.set("candles", candle, "hyperliquid", symbol, tf, ttl=5)
            self._emit_candle(candle)

        elif channel == "book":
            coin = data.get("coin", data.get("s", ""))
            symbol = self._from_hl_symbol(coin)

            bids_data = data.get("bids", data.get("b", []))[:25]
            asks_data = data.get("asks", data.get("a", []))[:25]

            bids = [OrderBookLevel(price=float(b[0]), volume=float(b[1])) for b in bids_data]
            asks = [OrderBookLevel(price=float(a[0]), volume=float(a[1])) for a in asks_data]

            if bids and asks:
                orderbook = OrderBook(
                    symbol=symbol,
                    exchange="hyperliquid",
                    bids=bids,
                    asks=asks,
                    spread=asks[0].price - bids[0].price,
                    mid_price=(bids[0].price + asks[0].price) / 2,
                    timestamp=int(time.time() * 1000),
                )
                self._cache.set("orderbook", orderbook, "hyperliquid", symbol, ttl=5)
                self._emit_orderbook(orderbook)

        elif channel == "allMids":
            mids = data.get("mids", data if isinstance(data, dict) else {})
            for hl_sym, mid in mids.items():
                symbol = self._from_hl_symbol(hl_sym)
                ticker = Ticker(
                    symbol=symbol,
                    price=float(mid),
                    change_24h=0.0,
                    volume_24h=0.0,
                    high_24h=float(mid),
                    low_24h=float(mid),
                    exchange="hyperliquid",
                    timestamp=int(time.time() * 1000),
                )
                self._cache.set("ticker", ticker, "hyperliquid", symbol, ttl=10)
                self._emit_ticker(ticker)

    async def stop(self):
        await super().stop()
        await self._http.aclose()
