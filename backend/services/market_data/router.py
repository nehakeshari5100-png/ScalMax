from fastapi import APIRouter, Query, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
import asyncio
import json
import time
import logging
from services.market_data.exchange_manager import ExchangeManager
from services.market_data.models import (
    MarketDataResponse, Ticker, OrderBook, ExchangeStatus,
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_manager() -> ExchangeManager:
    return ExchangeManager.get_instance()


@router.get("/candles/{symbol}", response_model=MarketDataResponse)
async def get_candles(
    symbol: str,
    timeframe: str = Query(default="5m", description="Candle timeframe"),
    exchange: Optional[str] = Query(default=None, description="Exchange name"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of candles"),
):
    if timeframe not in settings.supported_timeframes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported timeframe '{timeframe}'. Supported: {settings.supported_timeframes}",
        )
    if symbol.upper() not in [s.upper() for s in settings.supported_symbols]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported symbol '{symbol}'. Supported: {settings.supported_symbols}",
        )

    manager = get_manager()
    return await manager.get_candles(symbol.upper(), timeframe, exchange, limit)


@router.get("/candles/{symbol}/multi")
async def get_candles_multi(
    symbol: str,
    timeframes: str = Query(default="5m,15m,1h", description="Comma-separated timeframes"),
    exchange: Optional[str] = Query(default=None),
):
    tf_list = [t.strip() for t in timeframes.split(",")]
    invalid = [t for t in tf_list if t not in settings.supported_timeframes]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported timeframes: {invalid}. Supported: {settings.supported_timeframes}",
        )

    manager = get_manager()
    return await manager.get_candles_multi_timeframe(symbol.upper(), tf_list, exchange)


@router.get("/ticker/{symbol}", response_model=Ticker)
async def get_ticker(
    symbol: str,
    exchange: Optional[str] = Query(default=None),
):
    manager = get_manager()
    ticker = await manager.get_ticker(symbol.upper(), exchange)
    if ticker is None:
        raise HTTPException(status_code=404, detail=f"No ticker data for {symbol}")
    return ticker


@router.get("/tickers")
async def get_all_tickers():
    manager = get_manager()
    return await manager.get_all_tickers()


@router.get("/tokens")
async def get_tokens():
    manager = get_manager()
    tickers = await manager.get_all_tickers()
    result = []
    for exchange_name, exchange_tickers in tickers.items():
        for symbol, ticker in exchange_tickers.items():
            result.append({
                "symbol": ticker.symbol,
                "baseAsset": ticker.symbol.replace("USDT", "").replace("USD", ""),
                "quoteAsset": "USDT" if "USDT" in ticker.symbol else "USD",
                "price": ticker.price,
                "change24h": ticker.change_24h,
                "volume24h": ticker.volume_24h,
                "high24h": ticker.high_24h,
                "low24h": ticker.low_24h,
            })
        break
    return result


@router.get("/orderbook/{symbol}")
async def get_order_book(
    symbol: str,
    exchange: Optional[str] = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
):
    manager = get_manager()
    ob = await manager.get_order_book(symbol.upper(), exchange, limit)
    if ob is None:
        raise HTTPException(status_code=404, detail=f"No order book data for {symbol}")
    return ob


@router.get("/status", response_model=List[ExchangeStatus])
async def get_status():
    manager = get_manager()
    return await manager.get_status()


@router.get("/symbols")
async def get_symbols(query: Optional[str] = Query(default=None)):
    manager = get_manager()
    if query:
        return await manager.search_symbols(query)
    return settings.supported_symbols


@router.get("/timeframes")
async def get_timeframes():
    return settings.supported_timeframes


@router.websocket("/ws/{exchange}")
async def market_data_websocket(websocket: WebSocket, exchange: str):
    await websocket.accept()

    manager = get_manager()
    exchange_obj = manager.get_exchange(exchange)
    if not exchange_obj:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown exchange: {exchange}. Supported: binance, bybit, hyperliquid",
        })
        await websocket.close()
        return

    subscriptions = set()

    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "exchange": exchange,
            "symbols": settings.supported_symbols,
            "timeframes": settings.supported_timeframes,
        })

        # Forward messages from exchange
        def on_candle(candle):
            asyncio.ensure_future(
                websocket.send_json({
                    "type": "candle",
                    "exchange": exchange,
                    "symbol": candle.symbol,
                    "timeframe": candle.timeframe,
                    "data": candle.model_dump(),
                    "timestamp": int(time.time() * 1000),
                })
            )

        def on_ticker(ticker):
            asyncio.ensure_future(
                websocket.send_json({
                    "type": "ticker",
                    "exchange": exchange,
                    "symbol": ticker.symbol,
                    "data": ticker.model_dump(),
                    "timestamp": int(time.time() * 1000),
                })
            )

        exchange_obj.on_candle(on_candle)
        exchange_obj.on_ticker(on_ticker)

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "subscribe":
                symbol = msg.get("symbol", "").upper()
                timeframe = msg.get("timeframe", "5m")

                if symbol in settings.supported_symbols:
                    subscriptions.add(f"{symbol}:{timeframe}")
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbol": symbol,
                        "timeframe": timeframe,
                    })

            elif msg_type == "unsubscribe":
                symbol = msg.get("symbol", "").upper()
                timeframe = msg.get("timeframe", "5m")
                subscriptions.discard(f"{symbol}:{timeframe}")

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "fetch_candles":
                symbol = msg.get("symbol", "").upper()
                timeframe = msg.get("timeframe", "5m")
                limit = msg.get("limit", 100)
                candles = await manager.get_candles(symbol, timeframe, exchange, limit)
                await websocket.send_json({
                    "type": "candles_data",
                    **candles.model_dump(),
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {exchange}")
    except Exception as e:
        logger.error(f"WebSocket error ({exchange}): {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
