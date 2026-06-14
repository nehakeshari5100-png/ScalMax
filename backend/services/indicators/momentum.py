from typing import List, Tuple
from services.indicators.calculator import (
    rsi_last,
    macd_last,
    stochastic_rsi_last,
    momentum_strength_score,
)
from services.indicators.models import MACDResult, RSIData, StochRSIData, MomentumStrengthResult


class MomentumIndicators:
    """All momentum-based indicator calculations."""

    @staticmethod
    def calculate_rsi(closes: List[float], period: int = 14) -> RSIData:
        """Calculate RSI value with overbought/oversold flags."""
        rsi_val = rsi_last(closes, period)
        return RSIData(
            rsi=round(rsi_val, 2),
            oversold=rsi_val <= 30,
            overbought=rsi_val >= 70,
        )

    @staticmethod
    def calculate_macd(
        closes: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACDResult:
        """Calculate MACD with signal and histogram."""
        if len(closes) < slow_period + signal_period:
            return MACDResult()

        macd_line, signal_line, histogram = macd_last(
            closes, fast_period, slow_period, signal_period
        )
        return MACDResult(
            macd_line=round(macd_line, 2),
            signal_line=round(signal_line, 2),
            histogram=round(histogram, 2),
        )

    @staticmethod
    def calculate_stoch_rsi(
        closes: List[float],
        rsi_period: int = 14,
        stoch_period: int = 14,
        k_smoothing: int = 3,
        d_smoothing: int = 3,
    ) -> StochRSIData:
        """Calculate Stochastic RSI."""
        if len(closes) < rsi_period + stoch_period + d_smoothing:
            return StochRSIData()

        k, d = stochastic_rsi_last(
            closes, rsi_period, stoch_period, k_smoothing, d_smoothing
        )
        return StochRSIData(
            k=round(k, 2),
            d=round(d, 2),
            oversold=k <= 20 and d <= 20,
            overbought=k >= 80 and d >= 80,
        )

    @staticmethod
    def calculate_momentum_strength(
        rsi_val: float,
        macd_histogram: float,
        stoch_k: float,
    ) -> MomentumStrengthResult:
        """Calculate composite momentum strength score."""
        score, direction, desc = momentum_strength_score(
            rsi_val, macd_histogram, stoch_k
        )
        return MomentumStrengthResult(
            score=score,
            direction=direction,
            description=desc,
        )

    @staticmethod
    def get_all(
        closes: List[float],
    ) -> Tuple[RSIData, MACDResult, StochRSIData, MomentumStrengthResult, float]:
        """Calculate all momentum indicators at once."""
        rsi_data = MomentumIndicators.calculate_rsi(closes)
        macd_result = MomentumIndicators.calculate_macd(closes)
        stoch_data = MomentumIndicators.calculate_stoch_rsi(closes)

        momentum_strength = MomentumIndicators.calculate_momentum_strength(
            rsi_data.rsi, macd_result.histogram, stoch_data.k
        )

        return (rsi_data, macd_result, stoch_data, momentum_strength, momentum_strength.score)


momentum = MomentumIndicators()
