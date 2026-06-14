import logging
from typing import List, Tuple
from services.confluence.models import MarketStructureInput

logger = logging.getLogger(__name__)


def analyze_market_structure(
    closes: List[float],
    highs: List[float],
    lows: List[float],
) -> MarketStructureInput:
    """
    Pure-math market structure analysis.

    Detects swing highs/lows, trend direction, and market regime
    using numerical comparisons only — no AI.
    """
    if len(closes) < 10:
        return MarketStructureInput()

    swing_highs = _detect_swing_highs(highs)
    swing_lows = _detect_swing_lows(lows)

    higher_highs, lower_highs = _analyze_swing_trend(swing_highs)
    higher_lows, lower_lows = _analyze_swing_trend(swing_lows)

    trend_direction = _determine_trend_direction(
        higher_highs, lower_highs, higher_lows, lower_lows
    )
    regime = _determine_regime(closes, highs, lows)
    structure_score = _compute_structure_score(
        trend_direction, regime, len(swing_highs), len(swing_lows)
    )

    return MarketStructureInput(
        trend_direction=trend_direction,
        swing_highs=len(swing_highs),
        swing_lows=len(swing_lows),
        higher_highs=higher_highs,
        higher_lows=higher_lows,
        lower_highs=lower_highs,
        lower_lows=lower_lows,
        market_regime=regime,
        structure_score=structure_score,
    )


def _detect_swing_highs(highs: List[float], window: int = 5) -> List[Tuple[int, float]]:
    swings = []
    for i in range(window, len(highs) - window):
        if all(highs[i] > highs[j] for j in range(i - window, i)) and \
           all(highs[i] >= highs[j] for j in range(i + 1, i + window + 1)):
            swings.append((i, highs[i]))
    return swings


def _detect_swing_lows(lows: List[float], window: int = 5) -> List[Tuple[int, float]]:
    swings = []
    for i in range(window, len(lows) - window):
        if all(lows[i] < lows[j] for j in range(i - window, i)) and \
           all(lows[i] <= lows[j] for j in range(i + 1, i + window + 1)):
            swings.append((i, lows[i]))
    return swings


def _analyze_swing_trend(swings: List[Tuple[int, float]]) -> Tuple[bool, bool]:
    if len(swings) < 3:
        return False, False
    values = [s[1] for s in swings[-5:]]
    if len(values) < 2:
        return False, False
    higher = all(values[i] > values[i-1] for i in range(1, len(values)))
    lower = all(values[i] < values[i-1] for i in range(1, len(values)))
    return higher, lower


def _determine_trend_direction(
    higher_highs: bool, lower_highs: bool,
    higher_lows: bool, lower_lows: bool,
) -> str:
    if higher_highs and higher_lows:
        return "bullish"
    if lower_highs and lower_lows:
        return "bearish"
    if higher_highs:
        return "bullish"
    if lower_lows:
        return "bearish"
    return "neutral"


def _determine_regime(
    closes: List[float], highs: List[float], lows: List[float]
) -> str:
    recent = closes[-20:] if len(closes) >= 20 else closes
    if len(recent) < 5:
        return "ranging"
    high = max(highs[-len(recent):])
    low = min(lows[-len(recent):])
    range_pct = ((high - low) / max(low, 1)) * 100
    if range_pct > 8:
        return "volatile"
    closes_range = max(recent) - min(recent)
    avg_move = sum(abs(closes[i] - closes[i-1]) for i in range(1, len(recent))) / len(recent)
    if avg_move > closes_range * 0.3:
        return "trending"
    return "ranging"


def _compute_structure_score(
    trend_direction: str, regime: str, swing_highs: int, swing_lows: int
) -> float:
    score = 50.0
    if trend_direction != "neutral":
        score += 15
    if regime == "trending":
        score += 10
    elif regime == "volatile":
        score -= 5
    total_swings = swing_highs + swing_lows
    if total_swings >= 6:
        score += 10
    elif total_swings >= 3:
        score += 5
    return max(0, min(100, score))
