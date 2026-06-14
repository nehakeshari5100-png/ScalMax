from typing import List, Tuple
from services.indicators.calculator import atr_last, bollinger_bands_last, volatility_score
from services.indicators.models import ATRResult, BollingerBandsResult, VolatilityResult


class VolatilityIndicators:
    """All volatility-based indicator calculations."""

    @staticmethod
    def calculate_atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> ATRResult:
        """Calculate Average True Range."""
        if len(highs) < period + 1:
            return ATRResult()

        atr_val = atr_last(highs, lows, closes, period)
        current_price = closes[-1] if closes else 1.0

        return ATRResult(
            atr=round(atr_val, 2),
            atr_percent=round((atr_val / current_price) * 100.0, 4) if current_price > 0 else 0.0,
        )

    @staticmethod
    def calculate_bollinger_bands(
        closes: List[float],
        period: int = 20,
        num_std: float = 2.0,
    ) -> BollingerBandsResult:
        """Calculate Bollinger Bands with bandwidth and %b."""
        if len(closes) < period:
            return BollingerBandsResult()

        upper, middle, lower, bandwidth, percent_b = bollinger_bands_last(
            closes, period, num_std
        )

        return BollingerBandsResult(
            upper=round(upper, 2),
            middle=round(middle, 2),
            lower=round(lower, 2),
            bandwidth=round(bandwidth, 4),
            percent_b=round(percent_b, 4),
        )

    @staticmethod
    def calculate_volatility_score(
        atr_percent: float,
        bb_bandwidth: float,
    ) -> VolatilityResult:
        """Calculate composite volatility score."""
        score, desc = volatility_score(atr_percent, bb_bandwidth)
        return VolatilityResult(score=score, description=desc)

    @staticmethod
    def get_all(
        highs: List[float],
        lows: List[float],
        closes: List[float],
    ) -> Tuple[ATRResult, BollingerBandsResult, VolatilityResult, float]:
        """Calculate all volatility indicators at once."""
        atr_result = VolatilityIndicators.calculate_atr(highs, lows, closes)
        bb_result = VolatilityIndicators.calculate_bollinger_bands(closes)
        vol_score = VolatilityIndicators.calculate_volatility_score(
            atr_result.atr_percent, bb_result.bandwidth
        )

        return (atr_result, bb_result, vol_score, vol_score.score)


volatility = VolatilityIndicators()
