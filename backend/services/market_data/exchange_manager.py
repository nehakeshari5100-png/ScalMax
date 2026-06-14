import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from services.market_data.cache import DataCache, CandleCache, TickerCache, OrderBookCache
from services.market_data.models import (
    Candle, Ticker, OrderBook, Exchange, MarketDataResponse, ExchangeStatus,
)
from services.market_data.base import BaseExchange
from services.market_data.binance import BinanceExchange
from services.market_data.bybit import BybitExchange
from services.market_data.hyperliquid import HyperliquidExchange
from services.market_data.normalizer import aggregate_candles, TIMEFRAME_MS
from app.config import settings

logger = logging.getLogger(__name__)


class ExchangeManager:
    _instance: Optional['ExchangeManager'] = None

    def __init__(self):
        self._cache = DataCache(
            max_entries=settings.max_cache_entries,
            default_ttl=settings.cache_ttl_seconds,
        )
        self._candle_cache = CandleCache(self._cache)
        self._ticker_cache = TickerCache(self._cache)
        self._orderbook_cache = OrderBookCache(self._cache)
        self._exchanges: Dict[str, BaseExchange] = {}
        self._candle_callbacks: List[Callable] = []
        self._ticker_callbacks: List[Callable] = []
        self._running = False

    @classmethod
    def get_instance(cls) -> 'ExchangeManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self):
        if self._running:
            return
        self._running = True

        symbols = settings.supported_symbols

        binance = BinanceExchange(self._cache)
        bybit = BybitExchange(self._cache)
        hyperliquid = HyperliquidExchange(self._cache)

        self._exchanges = {
            "binance": binance,
            "bybit": bybit,
            "hyperliquid": hyperliquid,
        }

        # Wire up WebSocket event forwarding
        for exchange in self._exchanges.values():
            exchange.on_candle(self._on_candle)
            exchange.on_ticker(self._on_ticker)

        # Start all exchange connections concurrently
        tasks = [exchange.start(symbols) for exchange in self._exchanges.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Pre-fetch initial candle data
        await self._prefetch_initial_data(symbols)

        logger.info(f"ExchangeManager started with {len(self._exchanges)} exchanges")

    async def stop(self):
        self._running = False
        for exchange in self._exchanges.values():
            await exchange.stop()
        logger.info("ExchangeManager stopped")

    async def _prefetch_initial_data(self, symbols: List[str]):
        for symbol in symbols:
            for tf in settings.supported_timeframes:
                for exchange in self._exchanges.values():
                    candles = await exchange.fetch_candles(symbol, tf, limit=100)
                    if candles:
                        self._candle_cache.set_candles(
                            exchange.name, symbol, tf, candles
                        )
                    await asyncio.sleep(0.05)

    def _on_candle(self, candle: Candle):
        self._candle_cache.update_last_candle(
            candle.exchange, candle.symbol, candle.timeframe, candle
        )
        for cb in self._candle_callbacks:
            try:
                cb(candle)
            except Exception as e:
                logger.error(f"Candle callback error: {e}")

    def _on_ticker(self, ticker: Ticker):
        for cb in self._ticker_callbacks:
            try:
                cb(ticker)
            except Exception as e:
                logger.error(f"Ticker callback error: {e}")

    def on_candle(self, callback: Callable):
        self._candle_callbacks.append(callback)

    def on_ticker(self, callback: Callable):
        self._ticker_callbacks.append(callback)

    # ---- Public API ----

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        exchange: Optional[str] = None,
        limit: int = 100,
    ) -> MarketDataResponse:
        symbol = symbol.upper()
        target_exchanges = [exchange] if exchange else list(self._exchanges.keys())
        ts = int(time.time() * 1000)

        # Try cache first
        for ex_name in target_exchanges:
            cached = self._candle_cache.get_candles(ex_name, symbol, timeframe)
            if cached and len(cached) >= limit:
                return MarketDataResponse(
                    symbol=symbol,
                    timeframe=timeframe,
                    exchange=ex_name,
                    candles=cached[-limit:],
                    timestamp=ts,
                )

        # Fetch from first available exchange
        for ex_name in target_exchanges:
            exchange = self._exchanges.get(ex_name)
            if not exchange:
                continue
            try:
                candles = await exchange.fetch_candles(symbol, timeframe, limit)
                if candles:
                    self._candle_cache.set_candles(ex_name, symbol, timeframe, candles)
                    return MarketDataResponse(
                        symbol=symbol,
                        timeframe=timeframe,
                        exchange=ex_name,
                        candles=candles,
                        timestamp=ts,
                    )
            except Exception as e:
                logger.warning(f"[{ex_name}] get_candles failed: {e}")

        return MarketDataResponse(
            symbol=symbol,
            timeframe=timeframe,
            exchange=target_exchanges[0] if target_exchanges else "unknown",
            candles=[],
            timestamp=ts,
        )

    async def get_candles_multi_timeframe(
        self,
        symbol: str,
        timeframes: List[str],
        exchange: Optional[str] = None,
    ) -> Dict[str, MarketDataResponse]:
        results = {}
        for tf in timeframes:
            result = await self.get_candles(symbol, tf, exchange, limit=100)
            results[tf] = result
        return results

    async def get_ticker(
        self,
        symbol: str,
        exchange: Optional[str] = None,
    ) -> Optional[Ticker]:
        symbol = symbol.upper()

        # Check cache
        if exchange:
            cached = self._ticker_cache.get_ticker(exchange, symbol)
            if cached:
                return cached
        else:
            for ex_name in self._exchanges:
                cached = self._ticker_cache.get_ticker(ex_name, symbol)
                if cached:
                    return cached

        # Fetch
        target = [exchange] if exchange else list(self._exchanges.keys())
        for ex_name in target:
            ex = self._exchanges.get(ex_name)
            if not ex:
                continue
            try:
                ticker = await ex.fetch_ticker(symbol)
                if ticker:
                    self._ticker_cache.set_ticker(ex_name, symbol, ticker)
                    return ticker
            except Exception as e:
                logger.warning(f"[{ex_name}] fetch_ticker failed: {e}")

        return None

    async def get_all_tickers(self) -> Dict[str, Dict[str, Ticker]]:
        return self._ticker_cache.get_all_tickers()

    async def get_order_book(
        self,
        symbol: str,
        exchange: Optional[str] = None,
        limit: int = 25,
    ) -> Optional[OrderBook]:
        symbol = symbol.upper()

        # Check cache
        if exchange:
            cached = self._orderbook_cache.get_order_book(exchange, symbol)
            if cached:
                return cached
        else:
            for ex_name in self._exchanges:
                cached = self._orderbook_cache.get_order_book(ex_name, symbol)
                if cached:
                    return cached

        # Fetch
        target = [exchange] if exchange else list(self._exchanges.keys())
        for ex_name in target:
            ex = self._exchanges.get(ex_name)
            if not ex:
                continue
            try:
                ob = await ex.fetch_order_book(symbol, limit)
                if ob:
                    self._orderbook_cache.set_order_book(ex_name, symbol, ob)
                    return ob
            except Exception as e:
                logger.warning(f"[{ex_name}] fetch_order_book failed: {e}")

        return None

    async def get_status(self) -> List[ExchangeStatus]:
        statuses = []
        for name, exchange in self._exchanges.items():
            try:
                status = await exchange.get_status()
                statuses.append(ExchangeStatus(
                    exchange=name,
                    connected=status.get("connected", False),
                    symbols=status.get("symbols", []),
                    latency_ms=status.get("latency_ms"),
                    last_update=None,
                ))
            except Exception as e:
                statuses.append(ExchangeStatus(
                    exchange=name,
                    connected=False,
                    symbols=[],
                    error=str(e),
                ))
        return statuses

    async def search_symbols(self, query: str) -> List[str]:
        query = query.upper()
        results = []
        for symbol in settings.supported_symbols:
            if query in symbol:
                results.append(symbol)
        return results

    def get_exchange(self, name: str) -> Optional[BaseExchange]:
        return self._exchanges.get(name.lower())
