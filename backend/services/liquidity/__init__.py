"""
Liquidity Engine - Pure-math detection of liquidity structures.

Detectors:
- FVGDetector: Fair Value Gaps & Imbalances
- OrderBlockDetector: Order Blocks & Breaker Blocks
- LiquidityDetector: Equal Highs/Lows, Liquidity Pools, Liquidity Sweeps

Engine orchestrator runs all detectors and computes overall confidence.
"""

from typing import List

from services.liquidity.fvg import FVGDetector
from services.liquidity.liquidity import LiquidityDetector
from services.liquidity.orderblocks import OrderBlockDetector
from services.liquidity.models import LiquidityMap, LiquidityLevel


def build_liquidity_map(
    symbol: str,
    timeframe: str,
    highs: List[float],
    lows: List[float],
    closes: List[float],
    opens: List[float],
    volumes: List[float],
    timestamp: int = 0,
) -> LiquidityMap:
    """
    Run all liquidity detectors and return a consolidated LiquidityMap.

    All calculations are pure math using built-in Python types.
    """
    if not highs or not lows or not closes or len(highs) < 10:
        return LiquidityMap(symbol=symbol, timeframe=timeframe, timestamp=timestamp)

    avg_volume = sum(volumes) / max(len(volumes), 1)

    # --- Run all detectors ---
    fvg, imbalances = FVGDetector.detect_fvg(highs, lows, closes, opens, volumes, avg_volume)
    order_blocks, breaker_blocks = OrderBlockDetector.detect_order_blocks(
        highs, lows, closes, opens, volumes, avg_volume
    )
    equal_highs, equal_lows = LiquidityDetector.detect_equal_highs_lows(highs, lows)
    buy_liquidity, sell_liquidity = LiquidityDetector.detect_liquidity_pools(
        highs, lows, closes, volumes, avg_volume
    )
    sweeps = LiquidityDetector.detect_liquidity_sweeps(
        highs, lows, closes, opens, volumes, avg_volume
    )

    # --- Compute overall confidence ---
    confidence = _compute_confidence(
        len(fvg), len(order_blocks), len(equal_highs) + len(equal_lows),
        len(sweeps), len(buy_liquidity) + len(sell_liquidity)
    )

    return LiquidityMap(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=timestamp,
        bullish_liquidity=buy_liquidity,
        bearish_liquidity=sell_liquidity,
        equal_highs=equal_highs,
        equal_lows=equal_lows,
        fvg=fvg,
        order_blocks=order_blocks,
        breaker_blocks=breaker_blocks,
        liquidity_sweeps=sweeps,
        imbalances=imbalances,
        overall_confidence=confidence,
    )


def _compute_confidence(
    fvg_count: int,
    ob_count: int,
    equal_count: int,
    sweep_count: int,
    pool_count: int,
) -> int:
    """Compute overall liquidity confidence score 0-100."""
    score = 0
    score += min(fvg_count * 8, 25)
    score += min(ob_count * 6, 20)
    score += min(equal_count * 5, 20)
    score += min(sweep_count * 10, 25)
    score += min(pool_count * 3, 10)
    return min(100, max(0, score))
