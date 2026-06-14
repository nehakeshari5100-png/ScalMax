import time
import logging
from typing import List, Optional
from services.indicators.models import (
    IndicatorSet,
    IndicatorRequest,
    IndicatorResponse,
)
from services.indicators.trend import TrendIndicators
from services.indicators.momentum import MomentumIndicators
from services.indicators.volume import VolumeIndicators
from services.indicators.volatility import VolatilityIndicators
from services.market_data.models import Candle
from services.market_data.exchange_manager import ExchangeManager

logger = logging.getLogger(__name__)


class IndicatorEngine:
    """
    Orchestrates all indicator calculations.

    Pure mathematical pipeline:
    1. Fetch candles from Market Data Engine
    2. Extract OHLCV arrays
    3. Calculate all indicator categories
    4. Aggregate into IndicatorSet
    """

    def __init__(self):
        self._cache: dict = {}

    async def calculate(
        self,
        symbol: str,
        timeframe: str,
        exchange: str = "binance",
        lookback: int = 500,
    ) -> IndicatorSet:
        """Calculate all indicators for a symbol/timeframe."""
        # 1. Fetch candles
        candles = await self._fetch_candles(symbol, timeframe, exchange, lookback)

        if not candles:
            return IndicatorSet(
                symbol=symbol.upper(),
                timeframe=timeframe,
                timestamp=int(time.time() * 1000),
            )

        # 2. Extract OHLCV arrays
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        opens = [c.open for c in candles]
        volumes = [c.volume for c in candles]
        current_price = closes[-1] if closes else 0.0

        # 3. Calculate all indicators
        timestamp = int(time.time() * 1000)

        # Trend
        ema_result, trend_strength, trend_score = TrendIndicators.get_all(
            closes, current_price
        )

        # Momentum
        rsi_data, macd_result, stoch_data, momentum_strength, momentum_score = \
            MomentumIndicators.get_all(closes)

        # Volume
        vwap_result, volume_delta_value, volume_spike = VolumeIndicators.get_all(
            closes, highs, lows, volumes
        )

        # Volatility
        atr_result, bb_result, vol_result, vol_score = VolatilityIndicators.get_all(
            highs, lows, closes
        )

        # 4. Assemble result
        result = IndicatorSet(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=timestamp,

            # Trend
            ema9=ema_result.ema9,
            ema20=ema_result.ema20,
            ema50=ema_result.ema50,
            ema200=ema_result.ema200,

            # Momentum
            rsi=rsi_data.rsi,
            macd=macd_result,
            stoch_rsi=stoch_data,

            # Volume
            vwap=vwap_result.vwap,
            volume_delta=volume_delta_value,
            volume_spike=volume_spike,

            # Volatility
            atr=atr_result.atr,
            atr_percent=atr_result.atr_percent,
            bollinger=bb_result,

            # Composite Scores
            trend_score=trend_score,
            momentum_score=momentum_score,
            volatility_score=vol_score,
        )

        # Cache result
        cache_key = f"{symbol}:{timeframe}:{exchange}"
        self._cache[cache_key] = {
            "result": result,
            "timestamp": timestamp,
        }

        return result

    async def calculate_batch(
        self,
        symbols: List[str],
        timeframe: str,
        exchange: str = "binance",
    ) -> dict:
        """Calculate indicators for multiple symbols."""
        results = {}
        for symbol in symbols:
            try:
                result = await self.calculate(symbol, timeframe, exchange)
                results[symbol] = result
            except Exception as e:
                logger.error(f"Failed to calculate indicators for {symbol}: {e}")
                results[symbol] = None
        return results

    async def calculate_from_candles(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Candle],
    ) -> IndicatorSet:
        """Calculate indicators from pre-fetched candle data."""
        if not candles:
            return IndicatorSet(
                symbol=symbol.upper(),
                timeframe=timeframe,
                timestamp=int(time.time() * 1000),
            )

        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        volumes = [c.volume for c in candles]
        current_price = closes[-1] if closes else 0.0

        timestamp = int(time.time() * 1000)

        # Trend
        ema_result, trend_strength, trend_score = TrendIndicators.get_all(
            closes, current_price
        )

        # Momentum
        rsi_data, macd_result, stoch_data, momentum_strength, momentum_score = \
            MomentumIndicators.get_all(closes)

        # Volume
        vwap_result, volume_delta_value, volume_spike = VolumeIndicators.get_all(
            closes, highs, lows, volumes
        )

        # Volatility
        atr_result, bb_result, vol_result, vol_score = VolatilityIndicators.get_all(
            highs, lows, closes
        )

        return IndicatorSet(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=timestamp,
            ema9=ema_result.ema9,
            ema20=ema_result.ema20,
            ema50=ema_result.ema50,
            ema200=ema_result.ema200,
            rsi=rsi_data.rsi,
            macd=macd_result,
            stoch_rsi=stoch_data,
            vwap=vwap_result.vwap,
            volume_delta=volume_delta_value,
            volume_spike=volume_spike,
            atr=atr_result.atr,
            atr_percent=atr_result.atr_percent,
            bollinger=bb_result,
            trend_score=trend_score,
            momentum_score=momentum_score,
            volatility_score=vol_score,
        )

    async def _fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        exchange: str,
        lookback: int,
    ) -> List[Candle]:
        """Fetch candles from the Market Data Engine."""
        try:
            manager = ExchangeManager.get_instance()
            response = await manager.get_candles(symbol, timeframe, exchange, lookback)
            return response.candles if response else []
        except Exception as e:
            logger.error(f"Candle fetch error: {e}")
            return []

    def get_cached(self, symbol: str, timeframe: str, exchange: str = "binance") -> Optional[IndicatorSet]:
        """Get cached indicator set if available."""
        cache_key = f"{symbol}:{timeframe}:{exchange}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached["result"]
        return None

    def invalidate_cache(self, symbol: Optional[str] = None):
        """Invalidate cache for a symbol or all."""
        if symbol:
            keys_to_delete = [k for k in self._cache if k.startswith(symbol)]
            for k in keys_to_delete:
                del self._cache[k]
        else:
            self._cache.clear()


engine = IndicatorEngine()
