import logging
from typing import List, Optional
from services.market_data.models import Candle
from services.market_data.exchange_manager import ExchangeManager

logger = logging.getLogger(__name__)


class DataProvider:
    """Fetch candle data from exchange adapters or generate sample data."""

    @staticmethod
    async def fetch_candles(
        symbol: str,
        timeframe: str,
        exchange: str,
        lookback: int = 200,
    ) -> List[Candle]:
        try:
            manager = ExchangeManager.get_instance()
            response = await manager.get_candles(symbol, timeframe, exchange, lookback)
            if response and response.candles:
                logger.info(f"Fetched {len(response.candles)} candles from {exchange}")
                return response.candles
        except Exception as e:
            logger.warning(f"Live candle fetch failed ({exchange}/{symbol}): {e}")

        logger.info("Falling back to sample data generation")
        return DataProvider._generate_sample_candles(lookback)

    @staticmethod
    def _generate_sample_candles(count: int) -> List[Candle]:
        import math
        import time

        candles = []
        base_price = 67500.0
        now = int(time.time() * 1000)
        interval_ms = 300_000

        price = base_price
        for i in range(count):
            ts = now - (count - i) * interval_ms
            phase = math.sin(i * 0.05) * 200
            noise = (hash(f"n{i}") % 200) - 100
            change = phase * 0.1 + noise * 0.3

            open_p = price
            close_p = price + change
            high_p = max(open_p, close_p) + abs(noise) * 0.5
            low_p = min(open_p, close_p) - abs(noise) * 0.3
            vol = max(1.0, 100 + (hash(f"v{i}") % 200))

            candles.append(Candle(
                timestamp=ts,
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=round(vol, 2),
            ))
            price = close_p

        return candles
