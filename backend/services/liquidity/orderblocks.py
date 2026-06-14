import math
from typing import List, Tuple
from services.liquidity.models import OrderBlock


class OrderBlockDetector:
    """
    Pure-math detector for Order Blocks and Breaker Blocks.

    Order Block: The last candle before a strong impulse move.
    - Bullish OB: Last bearish/below-average candle before >= 2 bullish candles with momentum
    - Bearish OB: Last bullish/above-average candle before >= 2 bearish candles with momentum

    Breaker Block: An order block that failed (mitigated) and polarity flipped.
    - Former support becomes resistance (bearish breaker)
    - Former resistance becomes support (bullish breaker)
    """

    # Minimum impulse move as multiple of ATR
    IMPULSE_MULTIPLIER = 0.5

    @staticmethod
    def detect_order_blocks(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        opens: List[float],
        volumes: List[float],
        avg_volume: float,
    ) -> Tuple[List[OrderBlock], List[OrderBlock]]:
        """
        Detect order blocks and breaker blocks from OHLC data.

        Returns:
            (order_blocks, breaker_blocks)
        """
        order_blocks: List[OrderBlock] = []
        breaker_blocks: List[OrderBlock] = []

        if len(closes) < 5:
            return order_blocks, breaker_blocks

        # Calculate ATR-like range for impulse measurement
        ranges = [highs[i] - lows[i] for i in range(len(highs))]
        avg_range = sum(ranges) / max(len(ranges), 1)
        impulse_threshold = avg_range * OrderBlockDetector.IMPULSE_MULTIPLIER

        for i in range(2, len(closes) - 3):
            # Look for impulse move: at least 2 consecutive candles
            # in same direction exceeding impulse_threshold
            candle_body = abs(closes[i] - opens[i])
            next_body = abs(closes[i + 1] - opens[i + 1])
            prev_body = abs(closes[i - 1] - opens[i - 1])

            # ---- Bullish Order Block ----
            # Current and next candle are bullish with momentum
            if (closes[i] > opens[i] and closes[i + 1] > opens[i + 1]
                    and (closes[i] - opens[i]) + (closes[i + 1] - opens[i + 1]) > impulse_threshold):

                # The order block is the candle BEFORE the impulse
                ob_index = i - 1
                if ob_index >= 0:
                    # OB is the last consolidation/pre-impulse candle
                    ob_range = abs(closes[ob_index] - opens[ob_index])

                    # Stronger if it's a bearish candle (liquidity grab) before move up
                    is_bearish_ob = closes[ob_index] < opens[ob_index]

                    # Volume confirmation
                    vol_ratio = volumes[i] / max(avg_volume, 0.001)
                    ob_vol_ratio = volumes[ob_index] / max(avg_volume, 0.001) if ob_index < len(volumes) else 1.0

                    strength = OrderBlockDetector._ob_strength(
                        ob_range / max(avg_range, 0.001),
                        vol_ratio,
                        ob_vol_ratio,
                        is_bearish_ob,
                    )

                    ob = OrderBlock(
                        direction="bullish",
                        start_price=round(lows[ob_index], 2),
                        end_price=round(highs[ob_index], 2),
                        start_index=ob_index,
                        strength=strength,
                        type="order_block",
                    )

                    # Check if mitigated (price returned into OB range)
                    mitigation_idx = OrderBlockDetector._check_mitigation(
                        highs[ob_index], lows[ob_index],
                        highs, lows, ob_index + 3, len(highs)
                    )
                    if mitigation_idx is not None:
                        ob.mitigated = True
                        ob.mitigation_index = mitigation_idx

                    order_blocks.append(ob)

            # ---- Bearish Order Block ----
            if (closes[i] < opens[i] and closes[i + 1] < opens[i + 1]
                    and abs(closes[i] - opens[i]) + abs(closes[i + 1] - opens[i + 1]) > impulse_threshold):

                ob_index = i - 1
                if ob_index >= 0:
                    is_bullish_ob = closes[ob_index] > opens[ob_index]
                    ob_range = abs(closes[ob_index] - opens[ob_index])
                    vol_ratio = volumes[i] / max(avg_volume, 0.001)
                    ob_vol_ratio = volumes[ob_index] / max(avg_volume, 0.001) if ob_index < len(volumes) else 1.0

                    strength = OrderBlockDetector._ob_strength(
                        ob_range / max(avg_range, 0.001),
                        vol_ratio,
                        ob_vol_ratio,
                        is_bullish_ob,
                    )

                    ob = OrderBlock(
                        direction="bearish",
                        start_price=round(highs[ob_index], 2),
                        end_price=round(lows[ob_index], 2),
                        start_index=ob_index,
                        strength=strength,
                        type="order_block",
                    )

                    mitigation_idx = OrderBlockDetector._check_mitigation(
                        highs[ob_index], lows[ob_index],
                        highs, lows, ob_index + 3, len(highs)
                    )
                    if mitigation_idx is not None:
                        ob.mitigated = True
                        ob.mitigation_index = mitigation_idx

                    order_blocks.append(ob)

        # ---- Breaker Blocks Detection ----
        # A breaker block is a mitigated order block that has flipped polarity.
        # If an OB was mitigated (price returned to it), and then continued
        # in the opposite direction, it becomes a breaker.
        for ob in order_blocks:
            if ob.mitigated and ob.mitigation_index is not None:
                # Check if price continued past the OB in the opposite direction
                mit_idx = ob.mitigation_index
                if mit_idx is not None and mit_idx + 2 < len(closes):
                    if ob.direction == "bullish":
                        # Bullish OB mitigated then turned into resistance
                        if closes[mit_idx + 2] < ob.start_price:
                            breaker = ob.model_copy(deep=True)
                            breaker.direction = "bearish"
                            breaker.type = "breaker"
                            breaker_blocks.append(breaker)
                    else:
                        # Bearish OB mitigated then turned into support
                        if closes[mit_idx + 2] > ob.end_price:
                            breaker = ob.model_copy(deep=True)
                            breaker.direction = "bullish"
                            breaker.type = "breaker"
                            breaker_blocks.append(breaker)

        return order_blocks, breaker_blocks

    @staticmethod
    def _check_mitigation(
        ob_high: float,
        ob_low: float,
        highs: List[float],
        lows: List[float],
        start_idx: int,
        end_idx: int,
    ) -> int | None:
        """Check if price has returned into the OB zone."""
        for j in range(start_idx, min(end_idx, len(highs))):
            if highs[j] >= ob_low and lows[j] <= ob_high:
                return j
        return None

    @staticmethod
    def _ob_strength(
        range_ratio: float,
        vol_ratio: float,
        ob_vol_ratio: float,
        is_opposite_candle: bool,
    ) -> int:
        """Compute order block strength 1-10."""
        raw = (
            min(range_ratio, 2.0) / 2.0 * 3
            + min(vol_ratio, 3.0) / 3.0 * 3
            + min(ob_vol_ratio, 2.0) / 2.0 * 2
            + (2 if is_opposite_candle else 0)
        )
        return max(1, min(10, int(round(raw))))
