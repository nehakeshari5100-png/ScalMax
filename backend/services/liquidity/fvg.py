import math
from typing import List, Tuple
from services.liquidity.models import FVG, Imbalance


class FVGDetector:
    """
    Pure-math detector for Fair Value Gaps (FVG) and Imbalances.

    FVG: A gap between the high of candle i+1 and the low of candle i-1
    (bullish), or between the low of candle i+1 and the high of candle i-1
    (bearish). This represents an area where price moved too fast and
    left untraded space.

    Imbalance: A body gap between consecutive candles where the open of
    candle i+1 is outside the body range of candle i.
    """

    @staticmethod
    def detect_fvg(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        opens: List[float],
        volumes: List[float],
        avg_volume: float,
    ) -> Tuple[List[FVG], List[Imbalance]]:
        """
        Detect Fair Value Gaps and Imbalances from OHLC data.

        A bullish FVG occurs when:
            low[i+1] > high[i-1]  (gap between candle i-1 and i+1)

        A bearish FVG occurs when:
            high[i+1] < low[i-1]

        Confidence is based on:
        - Gap size relative to average candle range (bigger = stronger)
        - Volume at formation (higher = stronger)
        """
        fvg_list: List[FVG] = []
        imbalance_list: List[Imbalance] = []

        if len(highs) < 3:
            return fvg_list, imbalance_list

        # Calculate average candle range for normalization
        avg_range = sum(highs[i] - lows[i] for i in range(len(highs))) / max(len(highs), 1)

        for i in range(1, len(highs) - 1):
            prev_high = highs[i - 1]
            prev_low = lows[i - 1]
            curr_high = highs[i]
            curr_low = lows[i]
            next_high = highs[i + 1]
            next_low = lows[i + 1]

            # ---- FVG Detection ----

            # Bullish FVG: next candle's low > previous candle's high
            if next_low > prev_high:
                gap_high = next_low
                gap_low = prev_high
                gap_size = gap_high - gap_low

                # Strength based on gap size vs avg range and volume
                gap_ratio = gap_size / max(avg_range, 0.001)
                vol_factor = min(volumes[i] / max(avg_volume, 0.001), 3.0) / 3.0
                strength = FVGDetector._compute_strength(gap_ratio, vol_factor)

                # Check if mitigated (price has since returned into the gap)
                mitigated = False
                mitigation_price = None
                for j in range(i + 2, len(highs)):
                    if highs[j] >= gap_low and lows[j] <= gap_high:
                        mitigated = True
                        mitigation_price = (lows[j] + highs[j]) / 2
                        break

                fvg_list.append(FVG(
                    direction="bullish",
                    gap_high=round(gap_high, 2),
                    gap_low=round(gap_low, 2),
                    gap_size=round(gap_size, 2),
                    start_index=i - 1,
                    end_index=i + 1,
                    strength=strength,
                    mitigated=mitigated,
                    mitigation_price=round(mitigation_price, 2) if mitigation_price else None,
                ))

            # Bearish FVG: next candle's high < previous candle's low
            if next_high < prev_low:
                gap_high = prev_low
                gap_low = next_high
                gap_size = gap_high - gap_low

                gap_ratio = gap_size / max(avg_range, 0.001)
                vol_factor = min(volumes[i] / max(avg_volume, 0.001), 3.0) / 3.0
                strength = FVGDetector._compute_strength(gap_ratio, vol_factor)

                mitigated = False
                mitigation_price = None
                for j in range(i + 2, len(highs)):
                    if highs[j] >= gap_low and lows[j] <= gap_high:
                        mitigated = True
                        mitigation_price = (lows[j] + highs[j]) / 2
                        break

                fvg_list.append(FVG(
                    direction="bearish",
                    gap_high=round(gap_high, 2),
                    gap_low=round(gap_low, 2),
                    gap_size=round(gap_size, 2),
                    start_index=i - 1,
                    end_index=i + 1,
                    strength=strength,
                    mitigated=mitigated,
                    mitigation_price=round(mitigation_price, 2) if mitigation_price else None,
                ))

            # ---- Imbalance Detection ----
            # Body gap: open of next candle above high of current (bullish)
            # or open of next below low of current (bearish)
            body_high = max(closes[i], opens[i]) if i < len(closes) else max(closes[i], opens[i])
            body_low = min(closes[i], opens[i]) if i < len(closes) else min(closes[i], opens[i])
            next_open = closes[i + 1] if i + 1 < len(closes) else closes[i]
            next_body_low = min(closes[i + 1], next_open)

            if next_body_low > body_high:
                imb_size = next_body_low - body_high
                strength = min(10, max(1, int(imb_size / max(avg_range, 0.001) * 5)))
                imbalance_list.append(Imbalance(
                    direction="bullish",
                    high=round(next_body_low, 2),
                    low=round(body_high, 2),
                    size=round(imb_size, 2),
                    strength=strength,
                ))

            if max(closes[i + 1], next_open) < body_low:
                imb_size = body_low - max(closes[i + 1], next_open)
                strength = min(10, max(1, int(imb_size / max(avg_range, 0.001) * 5)))
                imbalance_list.append(Imbalance(
                    direction="bearish",
                    high=round(body_low, 2),
                    low=round(max(closes[i + 1], next_open), 2),
                    size=round(imb_size, 2),
                    strength=strength,
                ))

        return fvg_list, imbalance_list

    @staticmethod
    def _compute_strength(gap_ratio: float, vol_factor: float) -> int:
        """Compute FVG strength 1-10."""
        raw = gap_ratio * 4 + vol_factor * 6
        return max(1, min(10, int(round(raw))))
