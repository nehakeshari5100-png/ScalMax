import time
from typing import Dict, List, Optional, Any
from collections import OrderedDict
from threading import Lock
from services.market_data.models import Candle, Ticker, OrderBook


class DataCache:
    def __init__(self, max_entries: int = 10000, default_ttl: int = 300):
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = Lock()

    def _make_key(self, prefix: str, *parts: str) -> str:
        return f"{prefix}:{':'.join(parts)}"

    def _is_expired(self, expiry: float) -> bool:
        return time.time() > expiry

    def _evict(self):
        while len(self._cache) > self._max_entries:
            self._cache.popitem(last=False)

    def get(self, prefix: str, *parts: str) -> Optional[Any]:
        key = self._make_key(prefix, *parts)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            data, expiry = entry
            if self._is_expired(expiry):
                del self._cache[key]
                return None
            return data

    def set(self, prefix: str, data: Any, *parts: str, ttl: Optional[int] = None):
        key = self._make_key(prefix, *parts)
        expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
        with self._lock:
            self._cache[key] = (data, expiry)
            self._evict()

    def delete(self, prefix: str, *parts: str):
        key = self._make_key(prefix, *parts)
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()

    def clear_prefix(self, prefix: str):
        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(prefix + ":")]
            for k in keys_to_delete:
                del self._cache[k]

    def exists(self, prefix: str, *parts: str) -> bool:
        return self.get(prefix, *parts) is not None

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)


class CandleCache:
    def __init__(self, cache: DataCache):
        self._cache = cache

    def get_candles(self, exchange: str, symbol: str, timeframe: str) -> Optional[List[Candle]]:
        return self._cache.get("candles", exchange, symbol, timeframe)

    def set_candles(self, exchange: str, symbol: str, timeframe: str, candles: List[Candle]):
        self._cache.set("candles", candles, exchange, symbol, timeframe)

    def update_last_candle(self, exchange: str, symbol: str, timeframe: str, candle: Candle):
        candles = self.get_candles(exchange, symbol, timeframe)
        if candles is None:
            self.set_candles(exchange, symbol, timeframe, [candle])
            return

        if candles and candles[-1].timestamp == candle.timestamp:
            candles[-1] = candle
        else:
            candles.append(candle)
            if len(candles) > 500:
                candles = candles[-500:]

        self.set_candles(exchange, symbol, timeframe, candles)


class TickerCache:
    def __init__(self, cache: DataCache):
        self._cache = cache

    def get_ticker(self, exchange: str, symbol: str) -> Optional[Ticker]:
        return self._cache.get("ticker", exchange, symbol)

    def set_ticker(self, exchange: str, symbol: str, ticker: Ticker):
        self._cache.set("ticker", ticker, exchange, symbol, ttl=10)

    def get_all_tickers(self) -> Dict[str, Dict[str, Ticker]]:
        result: Dict[str, Dict[str, Ticker]] = {}
        for exchange in ["binance", "bybit", "hyperliquid"]:
            for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]:
                ticker = self.get_ticker(exchange, symbol)
                if ticker:
                    if exchange not in result:
                        result[exchange] = {}
                    result[exchange][symbol] = ticker
        return result


class OrderBookCache:
    def __init__(self, cache: DataCache):
        self._cache = cache

    def get_order_book(self, exchange: str, symbol: str) -> Optional[OrderBook]:
        return self._cache.get("orderbook", exchange, symbol)

    def set_order_book(self, exchange: str, symbol: str, ob: OrderBook):
        self._cache.set("orderbook", ob, exchange, symbol, ttl=5)
