
"""
Historical data replay — loads candles and feeds them one-by-one
to the simulation engine for deterministic candle-by-candle replay.
"""

import random
from typing import List, Optional

from services.backtesting.models import (
    BacktestCandle,
    BacktestConfig,
    BacktestSignal,
    SUPPORTED_ASSETS,
    SUPPORTED_TIMEFRAMES,
)


# Deterministic seed for slippage simulation reproducibility
RNG = random.Random(42)


class CandleReplay:
    """
    Feeds candles one-by-one to a callback for deterministic simulation.

    Supports:
    - Time-range filtering
    - Candle-by-candle iteration
    - Signal injection at specific candle indices
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.candles: List[BacktestCandle] = []
        self.current_index = -1

    def load_candles(self, candles: List[BacktestCandle]) -> None:
        """Load candles and filter by date range if specified."""
        filtered = list(candles)

        # Sort by timestamp ascending
        filtered.sort(key=lambda c: c.timestamp)

        if self.config.start_date:
            import datetime
            start_ts = int(datetime.datetime.fromisoformat(self.config.start_date).timestamp() * 1000)
            filtered = [c for c in filtered if c.timestamp >= start_ts]
        if self.config.end_date:
            import datetime
            end_ts = int(datetime.datetime.fromisoformat(self.config.end_date).timestamp() * 1000)
            filtered = [c for c in filtered if c.timestamp <= end_ts]

        self.candles = filtered
        self.current_index = -1

    def generate_sample_candles(self, count: int = 5000) -> None:
        """
        Generate deterministic sample candles for testing when
        live exchange data is unavailable.

        Uses a seeded random walk so results are reproducible.
        """
        RNG.seed(42)
        price = 50000.0
        base_time = 1700000000000  # 2023-11-14
        timeframe_ms = self._timeframe_ms()

        candles = []
        for i in range(count):
            ts = base_time + i * timeframe_ms
            change = RNG.gauss(0, price * 0.002)
            o = price
            c = price + change
            h = max(o, c) + abs(RNG.gauss(0, abs(change) * 0.5))
            l = min(o, c) - abs(RNG.gauss(0, abs(change) * 0.5))
            v = RNG.uniform(100, 10000)

            candles.append(BacktestCandle(
                timestamp=ts, open=round(o, 2), high=round(h, 2),
                low=round(l, 2), close=round(c, 2), volume=round(v, 2),
            ))
            price = c

        self.load_candles(candles)

    def __len__(self) -> int:
        return len(self.candles)

    def __iter__(self):
        self.current_index = -1
        return self

    def __next__(self) -> BacktestCandle:
        self.current_index += 1
        if self.current_index >= len(self.candles):
            raise StopIteration
        return self.candles[self.current_index]

    @property
    def is_done(self) -> bool:
        return self.current_index >= len(self.candles) - 1

    @property
    def progress(self) -> float:
        if not self.candles:
            return 1.0
        return (self.current_index + 1) / len(self.candles)

    def get_previous_candles(self, n: int) -> List[BacktestCandle]:
        """Get the last n candles before current_index."""
        if self.current_index < 0:
            return []
        start = max(0, self.current_index - n + 1)
        return self.candles[start:self.current_index + 1]

    def _timeframe_ms(self) -> int:
        mapping = {"1m": 60_000, "3m": 180_000, "5m": 300_000,
                    "15m": 900_000, "1h": 3_600_000}
        return mapping.get(self.config.timeframe, 300_000)
