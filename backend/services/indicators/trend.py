from typing import List, Tuple
from services.indicators.calculator import ema_last, trend_strength_score
from services.indicators.models import EMAResult, TrendStrengthResult


class TrendIndicators:
    """All trend-based indicator calculations."""

    @staticmethod
    def calculate_emas(closes: List[float]) -> EMAResult:
        """Calculate all four EMA values from close prices."""
        if len(closes) < 200:
            ema9 = ema_last(closes, 9) if len(closes) >= 9 else 0.0
            ema20 = ema_last(closes, 20) if len(closes) >= 20 else 0.0
            ema50 = ema_last(closes, 50) if len(closes) >= 50 else 0.0
            ema200 = 0.0
        else:
            ema9 = ema_last(closes, 9)
            ema20 = ema_last(closes, 20)
            ema50 = ema_last(closes, 50)
            ema200 = ema_last(closes, 200)

        return EMAResult(ema9=ema9, ema20=ema20, ema50=ema50, ema200=ema200)

    @staticmethod
    def calculate_ema(closes: List[float], period: int) -> float:
        """Calculate single EMA for any period."""
        if len(closes) < period:
            return 0.0
        return ema_last(closes, period)

    @staticmethod
    def calculate_trend_strength(
        ema_result: EMAResult,
        current_price: float,
    ) -> TrendStrengthResult:
        """Calculate overall trend strength score."""
        score, direction, desc = trend_strength_score(
            ema_result.ema9,
            ema_result.ema20,
            ema_result.ema50,
            ema_result.ema200,
            current_price,
        )
        return TrendStrengthResult(
            score=score,
            direction=direction,
            description=desc,
        )

    @staticmethod
    def get_all(
        closes: List[float],
        current_price: float,
    ) -> Tuple[EMAResult, TrendStrengthResult, float]:
        """Calculate all trend indicators at once."""
        ema_result = TrendIndicators.calculate_emas(closes)
        strength = TrendIndicators.calculate_trend_strength(ema_result, current_price)
        return (ema_result, strength, strength.score)


trend = TrendIndicators()
