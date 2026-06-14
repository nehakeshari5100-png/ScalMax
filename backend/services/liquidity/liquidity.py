import math
from typing import List, Tuple
from services.liquidity.models import EqualHighLow, LiquidityLevel, LiquiditySweep


class LiquidityDetector:
    """
    Pure-math detector for liquidity structures.

    Detects:
    - Equal Highs / Equal Lows (liquidity clusters)
    - Buy-side / Sell-side liquidity pools
    - Liquidity sweeps and stop hunts
    """

    # Proximity threshold as fraction of price
    EQUAL_THRESHOLD_PCT = 0.001  # 0.1%

    @staticmethod
    def detect_equal_highs_lows(
        highs: List[float],
        lows: List[float],
    ) -> Tuple[List[EqualHighLow], List[EqualHighLow]]:
        """
        Detect equal highs and equal lows.

        Swing points within EQUAL_THRESHOLD_PCT of each other are grouped.
        More touches = stronger level.
        """
        swing_highs = LiquidityDetector._find_swing_highs(highs)
        swing_lows = LiquidityDetector._find_swing_lows(lows)

        equal_highs = LiquidityDetector._cluster_points(swing_highs, "equal_high")
        equal_lows = LiquidityDetector._cluster_points(swing_lows, "equal_low")

        return equal_highs, equal_lows

    @staticmethod
    def detect_liquidity_pools(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        avg_volume: float,
    ) -> Tuple[List[LiquidityLevel], List[LiquidityLevel]]:
        """
        Detect buy-side and sell-side liquidity pools.

        Buy-side liquidity: Above current price (where shorts have stops)
        Sell-side liquidity: Below current price (where longs have stops)

        High-volume nodes above/below price are liquidity pools.
        """
        current_price = closes[-1] if closes else 0.0
        bullish: List[LiquidityLevel] = []
        bearish: List[LiquidityLevel] = []

        if len(highs) < 10:
            return bullish, bearish

        # Find high-volume price clusters
        price_buckets: dict = {}
        vol_buckets: dict = {}
        touch_buckets: dict = {}

        bucket_size = current_price * 0.002  # 0.2% buckets

        for i in range(len(highs)):
            bucket = round(highs[i] / max(bucket_size, 0.01)) * bucket_size
            price_buckets[bucket] = price_buckets.get(bucket, 0) + 1
            touch_buckets[bucket] = touch_buckets.get(bucket, 0) + 1
            vol_buckets[bucket] = vol_buckets.get(bucket, 0) + volumes[i]

            bucket_l = round(lows[i] / max(bucket_size, 0.01)) * bucket_size
            price_buckets[bucket_l] = price_buckets.get(bucket_l, 0) + 1
            touch_buckets[bucket_l] = touch_buckets.get(bucket_l, 0) + 1
            vol_buckets[bucket_l] = vol_buckets.get(bucket_l, 0) + volumes[i]

        for price, touches in sorted(price_buckets.items()):
            if price == 0:
                continue
            vol_ratio = vol_buckets.get(price, 0) / max(avg_volume * touches, 0.001)

            # Only consider significant levels
            if vol_ratio < 0.5 or touches < 2:
                continue

            strength = min(10, max(1, int(touches * 2 + vol_ratio * 3)))

            if price > current_price * 1.001:
                bullish.append(LiquidityLevel(
                    price=round(price, 2),
                    strength=strength,
                    touches=touches,
                    type="resistance",
                    direction="sell",
                ))
            elif price < current_price * 0.999:
                bearish.append(LiquidityLevel(
                    price=round(price, 2),
                    strength=strength,
                    touches=touches,
                    type="support",
                    direction="buy",
                ))

        # Sort by strength descending, take top 10 each
        bullish.sort(key=lambda x: x.strength, reverse=True)
        bearish.sort(key=lambda x: x.strength, reverse=True)

        return bullish[:10], bearish[:10]

    @staticmethod
    def detect_liquidity_sweeps(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        opens: List[float],
        volumes: List[float],
        avg_volume: float,
    ) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps and stop hunts.

        A liquidity sweep occurs when price briefly breaks above a
        previous high (or below a previous low) then reverses sharply.
        A stop hunt is an aggressive version with extra-long wicks.
        """
        sweeps: List[LiquiditySweep] = []

        if len(highs) < 10:
            return sweeps

        # Look for candle formations where price extends beyond
        # recent range and reverses with above-average volume
        lookback = 5

        for i in range(lookback, len(highs)):
            # Recent range
            recent_high = max(highs[i - lookback : i])
            recent_low = min(lows[i - lookback : i])
            candle_high = highs[i]
            candle_low = lows[i]
            candle_close = closes[i]
            candle_open = opens[i]
            candle_vol = volumes[i]

            vol_ratio = candle_vol / max(avg_volume, 0.001)

            # ---- Sell-side sweep: price breaks above recent high then closes back down
            if candle_high > recent_high * 1.001:
                wick_above = candle_high - max(candle_close, candle_open)
                body_size = abs(candle_close - candle_open)
                wick_ratio = wick_above / max(body_size, 0.001)

                # Must have a wick above and close back near open
                if wick_ratio > 0.5 and candle_close < recent_high:
                    reversal_strength = LiquidityDetector._sweep_strength(
                        vol_ratio, wick_ratio
                    )
                    sweeps.append(LiquiditySweep(
                        direction="sell",
                        price=round(candle_high, 2),
                        wick_size=round(wick_above, 2),
                        volume_ratio=round(vol_ratio, 2),
                        reversal_strength=reversal_strength,
                        timestamp=int(i),
                        type="stop_hunt" if (wick_ratio > 2.0 or vol_ratio > 2.0) else "sweep",
                    ))

            # ---- Buy-side sweep: price breaks below recent low then closes back up
            if candle_low < recent_low * 0.999:
                wick_below = max(candle_close, candle_open) - candle_low
                body_size = abs(candle_close - candle_open)
                wick_ratio = wick_below / max(body_size, 0.001)

                if wick_ratio > 0.5 and candle_close > recent_low:
                    reversal_strength = LiquidityDetector._sweep_strength(
                        vol_ratio, wick_ratio
                    )
                    sweeps.append(LiquiditySweep(
                        direction="buy",
                        price=round(candle_low, 2),
                        wick_size=round(wick_below, 2),
                        volume_ratio=round(vol_ratio, 2),
                        reversal_strength=reversal_strength,
                        timestamp=int(i),
                        type="stop_hunt" if (wick_ratio > 2.0 or vol_ratio > 2.0) else "sweep",
                    ))

        return sweeps

    @staticmethod
    def _find_swing_highs(highs: List[float]) -> List[float]:
        """Find swing high points (local maxima)."""
        swings: List[float] = []
        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                swings.append(highs[i])
        return swings

    @staticmethod
    def _find_swing_lows(lows: List[float]) -> List[float]:
        """Find swing low points (local minima)."""
        swings: List[float] = []
        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                swings.append(lows[i])
        return swings

    @staticmethod
    def _cluster_points(
        points: List[float],
        level_type: str,
    ) -> List[EqualHighLow]:
        """Group nearby swing points into liquidity clusters."""
        if not points:
            return []

        sorted_pts = sorted(points)
        clusters: List[EqualHighLow] = []
        current_cluster = [sorted_pts[0]]

        for pt in sorted_pts[1:]:
            avg_current = sum(current_cluster) / len(current_cluster)
            if abs(pt - avg_current) / max(avg_current, 1) <= LiquidityDetector.EQUAL_THRESHOLD_PCT:
                current_cluster.append(pt)
            else:
                avg_price = round(sum(current_cluster) / len(current_cluster), 2)
                strength = min(10, max(1, int(len(current_cluster) * 2.5)))
                clusters.append(EqualHighLow(
                    price=avg_price,
                    count=len(current_cluster),
                    strength=strength,
                    type=level_type,
                    timestamps=[],
                ))
                current_cluster = [pt]

        # Don't forget the last cluster
        if current_cluster:
            avg_price = round(sum(current_cluster) / len(current_cluster), 2)
            strength = min(10, max(1, int(len(current_cluster) * 2.5)))
            clusters.append(EqualHighLow(
                price=avg_price,
                count=len(current_cluster),
                strength=strength,
                type=level_type,
                timestamps=[],
            ))

        return clusters

    @staticmethod
    def _sweep_strength(vol_ratio: float, wick_ratio: float) -> int:
        """Compute sweep/stop-hunt strength 1-10."""
        raw = min(vol_ratio, 3.0) / 3.0 * 5 + min(wick_ratio, 3.0) / 3.0 * 5
        return max(1, min(10, int(round(raw))))
