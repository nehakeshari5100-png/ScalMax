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
from services.market_data.normalizer import normalize_candles

logger = logging.getLogger(__name__)

BYBIT_TIMEFRAME_MAP = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "1h": "60",
    "4h": "240",
}

BYBIT_WS_TIMEFRAME = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
}


class BybitExchange(BaseExchange):
    def __init__(self, cache):
        super().__init__(
            exchange=Exchange.BYBIT,
            cache=cache,
            ws_url="wss://stream.bybit.com/v5/public/linear",
            rest_url="https://api.bybit.com",
        )
        self._http = httpx.AsyncClient(timeout=10.0)

    @property
    def name(self) -> str:
        return "bybit"

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> List[Candle]:
        tf = BYBIT_TIMEFRAME_MAP.get(timeframe, "5")

        try:
            response = await self._http.get(
                f"{self._rest_url}/v5/market/kline",
                params={
                    "category": "linear",
                    "symbol": symbol.upper(),
                    "interval": tf,
                    "limit": min(limit, 1000),
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0 or not data.get("result"):
                logger.warning(f"[Bybit] API error: {data.get('retMsg')}")
                return []

            raw_list = data["result"].get("list", [])
            candles = []
            for raw in raw_list:
                ts = int(raw[0])
                if len(str(ts)) == 10:
                    ts *= 1000
                candle = Candle(
                    timestamp=ts,
                    open=float(raw[1]),
                    high=float(raw[2]),
                    low=float(raw[3]),
                    close=float(raw[4]),
                    volume=float(raw[5]),
                    exchange="bybit",
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                )
                candles.append(candle)

            candles.sort(key=lambda c: c.timestamp)
            return candles
        except Exception as e:
            logger.error(f"[Bybit] fetch_candles error: {e}")
            return []

    async def fetch_ticker(self, symbol: str) -> Optional[Ticker]:
        try:
            response = await self._http.get(
                f"{self._rest_url}/v5/market/tickers",
                params={"category": "linear", "symbol": symbol.upper()},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0 or not data.get("result"):
                return None

            t = data["result"]["list"][0]
            ts = int(t.get("timestamp", 0))
            if len(str(ts)) == 10:
                ts *= 1000

            return Ticker(
                symbol=symbol.upper(),
                price=float(t.get("lastPrice", 0)),
                change_24h=float(t.get("change24h", t.get("price24hPcnt", 0))) * 100,
                volume_24h=float(t.get("volume24h", t.get("volume", 0))),
                high_24h=float(t.get("highPrice24h", t.get("highPrice", 0))),
                low_24h=float(t.get("lowPrice24h", t.get("lowPrice", 0))),
                exchange="bybit",
                timestamp=ts,
            )
        except Exception as e:
            logger.error(f"[Bybit] fetch_ticker error: {e}")
            return None

    async def fetch_order_book(self, symbol: str, limit: int = 25) -> Optional[OrderBook]:
        try:
            response = await self._http.get(
                f"{self._rest_url}/v5/market/orderbook",
                params={"category": "linear", "symbol": symbol.upper(), "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0 or not data.get("result"):
                return None

            result = data["result"]
            bids = [OrderBookLevel(price=float(b[0]), volume=float(b[1])) for b in result.get("b", [])[:limit]]
            asks = [OrderBookLevel(price=float(a[0]), volume=float(a[1])) for a in result.get("a", [])[:limit]]

            best_bid = bids[0].price if bids else 0.0
            best_ask = asks[0].price if asks else 0.0

            return OrderBook(
                symbol=symbol.upper(),
                exchange="bybit",
                bids=bids,
                asks=asks,
                spread=best_ask - best_bid,
                mid_price=(best_bid + best_ask) / 2,
                timestamp=int(time.time() * 1000),
            )
        except Exception as e:
            logger.error(f"[Bybit] fetch_order_book error: {e}")
            return None

    async def _build_ws_subscriptions(self, symbols: List[str]) -> List[Dict]:
        args = []
        for sym in symbols:
            args.append(f"kline.5.{sym}")
            args.append(f"ticker.{sym}")
            args.append(f"orderbook.25.{sym}")

        return [
            {
                "op": "subscribe",
                "args": args,
            }
        ]

    def _handle_ws_message(self, raw: dict):
        if not isinstance(raw, dict):
            return

        topic = raw.get("topic", "")
        data = raw.get("data", {})

        if not topic or not data:
            return

        if topic.startswith("kline"):
            parts = topic.split(".")
            if len(parts) >= 3:
                tf_map = {"1": "1m", "3": "3m", "5": "5m", "15": "15m", "60": "1h", "240": "4h"}
                tf = tf_map.get(parts[1], parts[1])
                symbol = parts[2]

                ts = int(data.get("timestamp", data.get("start", 0)))
                if len(str(ts)) == 10:
                    ts *= 1000

                candle = Candle(
                    timestamp=ts,
                    open=float(data.get("open", 0)),
                    high=float(data.get("high", 0)),
                    low=float(data.get("low", 0)),
                    close=float(data.get("close", 0)),
                    volume=float(data.get("volume", 0)),
                    exchange="bybit",
                    symbol=symbol,
                    timeframe=tf,
                )
                self._cache.set("candles", candle, "bybit", symbol, tf, ttl=5)
                self._emit_candle(candle)

        elif topic.startswith("ticker"):
            parts = topic.split(".")
            symbol = parts[1] if len(parts) >= 2 else ""

            ts = int(data.get("timestamp", data.get("ts", 0)))
            if len(str(ts)) == 10:
                ts *= 1000

            ticker = Ticker(
                symbol=symbol,
                price=float(data.get("lastPrice", data.get("markPrice", 0))),
                change_24h=float(data.get("price24hPcnt", 0)) * 100,
                volume_24h=float(data.get("volume24h", data.get("volume", 0))),
                high_24h=float(data.get("highPrice24h", data.get("highPrice", 0))),
                low_24h=float(data.get("lowPrice24h", data.get("lowPrice", 0))),
                exchange="bybit",
                timestamp=ts,
            )
            self._cache.set("ticker", ticker, "bybit", symbol, ttl=10)
            self._emit_ticker(ticker)

        elif topic.startswith("orderbook"):
            parts = topic.split(".")
            symbol = parts[2] if len(parts) >= 3 else ""

            bids_data = data.get("b", [])
            asks_data = data.get("a", [])
            ts = int(data.get("timestamp", data.get("ts", time.time() * 1000)))
            if len(str(ts)) == 10:
                ts *= 1000

            bids = [OrderBookLevel(price=float(b[0]), volume=float(b[1])) for b in bids_data[:25]]
            asks = [OrderBookLevel(price=float(a[0]), volume=float(a[1])) for a in asks_data[:25]]

            if bids and asks:
                orderbook = OrderBook(
                    symbol=symbol,
                    exchange="bybit",
                    bids=bids,
                    asks=asks,
                    spread=asks[0].price - bids[0].price,
                    mid_price=(bids[0].price + asks[0].price) / 2,
                    timestamp=ts,
                )
                self._cache.set("orderbook", orderbook, "bybit", symbol, ttl=5)
                self._emit_orderbook(orderbook)

    async def stop(self):
        await super().stop()
        await self._http.aclose()
