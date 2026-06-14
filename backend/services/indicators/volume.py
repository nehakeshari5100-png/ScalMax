from typing import List, Tuple
from services.indicators.calculator import vwap_last, volume_spike_ratio
from services.indicators.models import VWAPResult, VolumeSpikeResult


class VolumeIndicators:
    """All volume-based indicator calculations."""

    @staticmethod
    def calculate_vwap(
        closes: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
    ) -> VWAPResult:
        """Calculate Volume-Weighted Average Price."""
        if not closes or not volumes:
            return VWAPResult()

        vwap_val = vwap_last(closes, highs, lows, volumes)
        current_price = closes[-1] if closes else 0.0

        return VWAPResult(
            vwap=round(vwap_val, 2),
            price_above_vwap=current_price > vwap_val if vwap_val > 0 else None,
        )

    @staticmethod
    def calculate_volume_delta(
        volumes: List[float],
        closes: List[float],
        lookback: int = 20,
    ) -> float:
        """
        Estimate volume delta from price direction.
        Positive delta = buying pressure, Negative = selling pressure.
        """
        if len(volumes) < lookback:
            return 0.0

        delta = 0.0
        start = max(0, len(volumes) - lookback)

        for i in range(start, len(volumes)):
            if i == 0:
                continue
            price_up = closes[i] > closes[i - 1]
            vol = volumes[i]

            if price_up:
                delta += vol
            else:
                delta -= vol

        return round(delta, 2)

    @staticmethod
    def detect_volume_spike(
        volumes: List[float],
        multiplier: float = 2.0,
    ) -> VolumeSpikeResult:
        """Detect if the most recent candle has a volume spike."""
        if len(volumes) < 21:
            return VolumeSpikeResult()

        current_vol = volumes[-1]
        recent_volumes = volumes[-21:-1]  # Last 20 excluding current

        is_spike, ratio = volume_spike_ratio(
            current_vol, recent_volumes, multiplier
        )

        direction = "bullish" if is_spike else "neutral"

        return VolumeSpikeResult(
            is_spike=is_spike,
            ratio=round(ratio, 2),
            direction=direction,
        )

    @staticmethod
    def get_all(
        closes: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
    ) -> Tuple[VWAPResult, float, VolumeSpikeResult]:
        """Calculate all volume indicators at once."""
        vwap_result = VolumeIndicators.calculate_vwap(closes, highs, lows, volumes)
        delta = VolumeIndicators.calculate_volume_delta(volumes, closes)
        spike = VolumeIndicators.detect_volume_spike(volumes)

        return (vwap_result, delta, spike)


volume = VolumeIndicators()
