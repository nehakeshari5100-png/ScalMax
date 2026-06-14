from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from services.indicators.engine import IndicatorEngine
from services.indicators.models import IndicatorSet, IndicatorResponse
from app.config import settings

router = APIRouter()
indicator_engine = IndicatorEngine()


@router.get("/{symbol}", response_model=IndicatorResponse)
async def get_indicators(
    symbol: str,
    timeframe: str = Query(default="5m", description="Candle timeframe"),
    exchange: str = Query(default="binance", description="Exchange"),
    lookback: int = Query(default=500, ge=100, le=1000, description="Candle lookback"),
    force_refresh: bool = Query(default=False, description="Bypass cache"),
):
    """Calculate all indicators for a symbol/timeframe."""
    symbol = symbol.upper()

    if timeframe not in settings.supported_timeframes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported timeframe '{timeframe}'. Supported: {settings.supported_timeframes}",
        )

    # Check cache first
    if not force_refresh:
        cached = indicator_engine.get_cached(symbol, timeframe, exchange)
        if cached:
            return IndicatorResponse(success=True, data=cached, cached=True)

    try:
        result = await indicator_engine.calculate(symbol, timeframe, exchange, lookback)
        return IndicatorResponse(success=True, data=result, cached=False)
    except Exception as e:
        return IndicatorResponse(success=False, error=str(e))


@router.get("/{symbol}/from-candles", response_model=IndicatorResponse)
async def get_indicators_from_candles(
    symbol: str,
    timeframe: str = Query(default="5m"),
    exchange: str = Query(default="binance"),
    lookback: int = Query(default=500),
):
    """Calculate indicators using candle data from market data engine."""
    symbol = symbol.upper()
    try:
        from services.market_data.exchange_manager import ExchangeManager
        manager = ExchangeManager.get_instance()
        response = await manager.get_candles(symbol, timeframe, exchange, lookback)

        if not response or not response.candles:
            return IndicatorResponse(
                success=False,
                error=f"No candle data available for {symbol} {timeframe}",
            )

        result = await indicator_engine.calculate_from_candles(
            symbol, timeframe, response.candles
        )
        return IndicatorResponse(success=True, data=result, cached=False)
    except Exception as e:
        return IndicatorResponse(success=False, error=str(e))


@router.post("/batch", response_model=dict)
async def get_indicators_batch(
    symbols: List[str],
    timeframe: str = Query(default="5m"),
    exchange: str = Query(default="binance"),
):
    """Calculate indicators for multiple symbols."""
    results = await indicator_engine.calculate_batch(symbols, timeframe, exchange)
    return {
        "success": True,
        "data": {
            sym: IndicatorResponse(success=True, data=result).model_dump()
            if result
            else IndicatorResponse(success=False, error="Calculation failed").model_dump()
            for sym, result in results.items()
        },
    }


@router.post("/invalidate-cache")
async def invalidate_cache(symbol: Optional[str] = Query(default=None)):
    """Invalidate indicator cache."""
    indicator_engine.invalidate_cache(symbol)
    return {"success": True, "message": f"Cache invalidated for {symbol or 'all'}"}
