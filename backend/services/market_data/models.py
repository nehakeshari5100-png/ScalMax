from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class Exchange(str, Enum):
    BINANCE = "binance"
    BYBIT = "bybit"
    HYPERLIQUID = "hyperliquid"


class Candle(BaseModel):
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Close price")
    volume: float = Field(..., description="Volume in base asset")
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None


class Ticker(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    exchange: str
    timestamp: int


class OrderBookLevel(BaseModel):
    price: float
    volume: float


class OrderBook(BaseModel):
    symbol: str
    exchange: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    spread: float
    mid_price: float
    timestamp: int


class MarketDataResponse(BaseModel):
    symbol: str
    timeframe: str
    exchange: str
    candles: List[Candle]
    timestamp: int

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "exchange": "binance",
                "candles": [
                    {
                        "timestamp": 1700000000000,
                        "open": 67500.0,
                        "high": 67600.0,
                        "low": 67400.0,
                        "close": 67550.0,
                        "volume": 123.45,
                        "exchange": "binance",
                        "symbol": "BTCUSDT",
                        "timeframe": "5m",
                    }
                ],
                "timestamp": 1700000000000,
            }
        }


class ExchangeStatus(BaseModel):
    exchange: str
    connected: bool
    symbols: List[str]
    latency_ms: Optional[float] = None
    last_update: Optional[int] = None
    error: Optional[str] = None


class WSMessage(BaseModel):
    type: str = Field(..., description="candle | ticker | orderbook | status")
    exchange: str
    symbol: str
    data: dict
    timestamp: int
