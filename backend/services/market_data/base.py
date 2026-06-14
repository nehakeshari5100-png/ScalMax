import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Dict, Any
from services.market_data.models import Candle, Ticker, OrderBook, Exchange
from services.market_data.cache import DataCache
from services.market_data.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class BaseExchange(ABC):
    def __init__(
        self,
        exchange: Exchange,
        cache: DataCache,
        ws_url: str,
        rest_url: str,
    ):
        self.exchange = exchange
        self._cache = cache
        self._ws_url = ws_url
        self._rest_url = rest_url
        self._ws_manager: Optional[WebSocketManager] = None
        self._candle_callbacks: List[Callable] = []
        self._ticker_callbacks: List[Callable] = []
        self._orderbook_callbacks: List[Callable] = []
        self._symbols: List[str] = []
        self._running = False

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> List[Candle]:
        pass

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Optional[Ticker]:
        pass

    @abstractmethod
    async def fetch_order_book(self, symbol: str, limit: int = 25) -> Optional[OrderBook]:
        pass

    @abstractmethod
    async def _build_ws_subscriptions(self, symbols: List[str]) -> List[Dict]:
        pass

    @abstractmethod
    def _handle_ws_message(self, raw: dict):
        pass

    async def start(self, symbols: List[str]):
        self._symbols = symbols
        self._running = True

        subs = await self._build_ws_subscriptions(symbols)
        self._ws_manager = WebSocketManager(
            name=self.name,
            max_reconnect_delay=60.0,
            initial_reconnect_delay=1.0,
        )
        self._ws_manager.on_message(self._handle_ws_message)
        await self._ws_manager.connect(self._ws_url, subs)

    async def stop(self):
        self._running = False
        if self._ws_manager:
            await self._ws_manager.disconnect()

    def on_candle(self, callback: Callable):
        self._candle_callbacks.append(callback)

    def on_ticker(self, callback: Callable):
        self._ticker_callbacks.append(callback)

    def on_orderbook(self, callback: Callable):
        self._orderbook_callbacks.append(callback)

    def _emit_candle(self, candle: Candle):
        for cb in self._candle_callbacks:
            try:
                cb(candle)
            except Exception as e:
                logger.error(f"[{self.name}] Candle callback error: {e}")

    def _emit_ticker(self, ticker: Ticker):
        for cb in self._ticker_callbacks:
            try:
                cb(ticker)
            except Exception as e:
                logger.error(f"[{self.name}] Ticker callback error: {e}")

    def _emit_orderbook(self, orderbook: OrderBook):
        for cb in self._orderbook_callbacks:
            try:
                cb(orderbook)
            except Exception as e:
                logger.error(f"[{self.name}] Orderbook callback error: {e}")

    async def get_status(self) -> dict:
        ws_stats = self._ws_manager.get_stats() if self._ws_manager else {}
        return {
            "exchange": self.name,
            "connected": self._ws_manager.state.value == "connected" if self._ws_manager else False,
            "symbols": self._symbols,
            "latency_ms": ws_stats.get("latency_ms"),
            "ws_state": ws_stats.get("state", "disconnected"),
        }

    def supports_symbol(self, symbol: str) -> bool:
        return symbol.upper() in [s.upper() for s in self._symbols]
