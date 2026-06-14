
"""
Confluence Scoring Engine.

Combines signals from:
  - Indicator Engine (trend, momentum, volume, volatility)
  - Market Structure Engine (swing points, regime)
  - Liquidity Engine (FVG, OBs, sweeps, pools)

Produces a 0-100 score with grade, reasons, and risks.
"""

from typing import List, Tuple

from services.confluence.models import (
    CategoryScore,
    ConfluenceInput,
    ConfluenceOutput,
    MarketStructureInput,
)

# Weights as defined in Phase 7 spec
WEIGHTS = {
    "market_structure": 0.30,
    "liquidity": 0.25,
    "trend": 0.15,
    "momentum": 0.15,
    "volume": 0.10,
    "volatility": 0.05,
}

# Grade thresholds
GRADES: List[Tuple[int, str]] = [
    (90, "Elite Setup"),
    (80, "High Probability"),
    (70, "Tradable"),
    (0, "No Trade"),
]


class ConfluenceScorer:
    """
    Pure-math confluence scorer.

    Each category generates a 0-100 raw score, then applies the
    configured weight. The sum produces the final 0-100 score.
    """

    @staticmethod
    def score(data: ConfluenceInput) -> ConfluenceOutput:
        """
        Compute the full confluence score from all inputs.
        """
        categories: List[CategoryScore] = []
        all_reasons: List[str] = []
        all_risks: List[str] = []

        # --- 1. Market Structure (30%) ---
        ms_score, ms_reason, ms_risks = ConfluenceScorer._score_market_structure(
            data.market_structure
        )
        categories.append(CategoryScore(
            name="Market Structure",
            weight=WEIGHTS["market_structure"],
            raw_score=ms_score,
            weighted_score=round(ms_score * WEIGHTS["market_structure"], 1),
            reason=ms_reason,
        ))
        all_reasons.append(ms_reason)
        all_risks.extend(ms_risks)

        # --- 2. Liquidity (25%) ---
        liq_score, liq_reason, liq_risks = ConfluenceScorer._score_liquidity(data)
        categories.append(CategoryScore(
            name="Liquidity",
            weight=WEIGHTS["liquidity"],
            raw_score=liq_score,
            weighted_score=round(liq_score * WEIGHTS["liquidity"], 1),
            reason=liq_reason,
        ))
        all_reasons.append(liq_reason)
        all_risks.extend(liq_risks)

        # --- 3. Trend (15%) ---
        trend_score, trend_reason, trend_risks = ConfluenceScorer._score_trend(data)
        categories.append(CategoryScore(
            name="Trend",
            weight=WEIGHTS["trend"],
            raw_score=trend_score,
            weighted_score=round(trend_score * WEIGHTS["trend"], 1),
            reason=trend_reason,
        ))
        all_reasons.append(trend_reason)
        all_risks.extend(trend_risks)

        # --- 4. Momentum (15%) ---
        momo_score, momo_reason, momo_risks = ConfluenceScorer._score_momentum(data)
        categories.append(CategoryScore(
            name="Momentum",
            weight=WEIGHTS["momentum"],
            raw_score=momo_score,
            weighted_score=round(momo_score * WEIGHTS["momentum"], 1),
            reason=momo_reason,
        ))
        all_reasons.append(momo_reason)
        all_risks.extend(momo_risks)

        # --- 5. Volume (10%) ---
        vol_score, vol_reason, vol_risks = ConfluenceScorer._score_volume(data)
        categories.append(CategoryScore(
            name="Volume",
            weight=WEIGHTS["volume"],
            raw_score=vol_score,
            weighted_score=round(vol_score * WEIGHTS["volume"], 1),
            reason=vol_reason,
        ))
        all_reasons.append(vol_reason)
        all_risks.extend(vol_risks)

        # --- 6. Volatility (5%) ---
        volty_score, volty_reason, volty_risks = ConfluenceScorer._score_volatility(data)
        categories.append(CategoryScore(
            name="Volatility",
            weight=WEIGHTS["volatility"],
            raw_score=volty_score,
            weighted_score=round(volty_score * WEIGHTS["volatility"], 1),
            reason=volty_reason,
        ))
        all_reasons.append(volty_reason)
        all_risks.extend(volty_risks)

        # --- Compute Negative Penalties for Contradictory Signals ---
        penalty_total, penalty_reasons, penalty_risks = ConfluenceScorer._compute_penalties(data)
        all_reasons.extend(penalty_reasons)
        all_risks.extend(penalty_risks)

        # --- Final Score (apply penalties) ---
        base_score = sum(c.weighted_score for c in categories)
        final_score = round(max(0, base_score - penalty_total))
        grade = ConfluenceScorer._grade(final_score)
        direction = ConfluenceScorer._determine_direction(data)

        # Deduplicate reasons/risks
        seen_reasons = set()
        unique_reasons = []
        for r in all_reasons:
            if r and r not in seen_reasons:
                seen_reasons.add(r)
                unique_reasons.append(r)

        seen_risks = set()
        unique_risks = []
        for r in all_risks:
            if r and r not in seen_risks:
                seen_risks.add(r)
                unique_risks.append(r)

        return ConfluenceOutput(
            score=final_score,
            grade=grade,
            direction=direction,
            reasons=unique_reasons[:8],
            risks=unique_risks[:6],
            category_scores=categories,
        )

    @staticmethod
    def _score_market_structure(ms: MarketStructureInput) -> Tuple[float, str, List[str]]:
        """Rate the market structure quality 0-100."""
        score = ms.structure_score  # Use pre-computed if available
        reasons: List[str] = []
        risks: List[str] = []

        if score == 0.0 and not any([ms.higher_highs, ms.higher_lows, ms.lower_highs, ms.lower_lows]):
            # Compute inline
            score = 50.0

        # Adjust based on regime
        if ms.market_regime == "trending":
            score += 15
            reasons.append("Trending market regime — clear directional bias")
        elif ms.market_regime == "volatile":
            score -= 10
            reasons.append("Volatile regime — wider stops required")
            risks.append("Volatile market structure may produce false breakouts")
        else:
            reasons.append("Ranging regime — mean-reversion strategies preferred")
            risks.append("Ranging market may lack directional conviction")

        # Swing structure quality
        if ms.higher_highs and ms.higher_lows:
            score += 10
            reasons.append("Higher highs + higher lows — strong uptrend structure")
        elif ms.lower_highs and ms.lower_lows:
            score += 10
            reasons.append("Lower highs + lower lows — strong downtrend structure")
        elif ms.higher_highs and ms.lower_highs:
            score -= 5
            risks.append("Divergent swing structure — trend weakening")
        elif ms.lower_lows and ms.higher_lows:
            score -= 5
            risks.append("Mixed swing lows — unclear structure")

        score = max(0, min(100, score))
        reason = reasons[0] if reasons else "Neutral market structure"
        return score, reason, risks

    @staticmethod
    def _score_liquidity(data: ConfluenceInput) -> Tuple[float, str, List[str]]:
        """Rate liquidity setup quality 0-100."""
        score = data.liquidity_confidence
        risks: List[str] = []

        # FVG quality
        bullish_fvg = 0
        bearish_fvg = 0
        if data.fvg_count > 0 and data.fvg_count <= 3:
            score += 10
        elif data.fvg_count > 3:
            score += 5

        # Order blocks
        if data.order_block_count > 0:
            score += 10
        if data.breaker_block_count > 0:
            score -= 5
            risks.append("Breaker blocks present — previous order blocks invalidated")

        # Liquidity sweeps
        if data.sweep_count > 0 and data.sweep_count <= 2:
            score += 15
        elif data.sweep_count > 2:
            score += 8

        # Equal highs/lows
        if data.equal_high_count >= 2:
            score += 8
        if data.equal_low_count >= 2:
            score += 8

        # Buy-side liquidity pools above = resistance
        if data.bullish_liquidity_pools > 0 and data.bearish_liquidity_pools > 0:
            score += 5

        if data.bullish_liquidity_pools > 3:
            risks.append("Heavy sell-side liquidity above — strong resistance cluster")
        if data.bearish_liquidity_pools > 3:
            risks.append("Heavy buy-side liquidity below — strong support cluster")

        score = max(0, min(100, score))
        reason = f"Liquidity confidence: {data.liquidity_confidence:.0f}/100"
        return score, reason, risks

    @staticmethod
    def _score_trend(data: ConfluenceInput) -> Tuple[float, str, List[str]]:
        """Rate trend quality 0-100."""
        score = data.trend_score
        risks: List[str] = []

        # EMA alignment check
        if all(v is not None for v in [data.ema9, data.ema20, data.ema50, data.price]):
            if data.ema9 > data.ema20 > data.ema50 and data.price > data.ema9:
                score += 15
            elif data.ema9 < data.ema20 < data.ema50 and data.price < data.ema9:
                score += 15
            else:
                # Partially aligned
                if (data.price > data.ema20 and data.price > data.ema50):
                    score += 5
                elif (data.price < data.ema20 and data.price < data.ema50):
                    score += 5
                else:
                    score -= 5
                    risks.append("EMAs are mixed — no clear trend alignment")

        if score < 40:
            risks.append("Weak trend — avoid trend-following strategies")
        elif score > 70:
            risks.append("Trend extended — wait for pullback to enter")

        score = max(0, min(100, score))
        reason = f"Trend score: {data.trend_score:.0f}/100"
        return score, reason, risks

    @staticmethod
    def _score_momentum(data: ConfluenceInput) -> Tuple[float, str, List[str]]:
        """Rate momentum quality 0-100."""
        score = data.momentum_score
        risks: List[str] = []

        if data.rsi is not None:
            if 40 <= data.rsi <= 60:
                score += 10
            elif data.rsi > 75:
                score -= 10
                risks.append(f"RSI overbought ({data.rsi:.0f}) — reversal risk")
            elif data.rsi < 25:
                score += 5
                risks.append(f"RSI oversold ({data.rsi:.0f}) — potential bounce")

        if data.macd_histogram is not None:
            prev_hist = data.macd_histogram
            if prev_hist > 0:
                score += 10
            elif prev_hist < 0:
                score -= 5
                risks.append("MACD histogram negative — bearish momentum")
            if abs(prev_hist) > 20:
                score += 5
                risks.append("Strong momentum — confirm with volume")

        score = max(0, min(100, score))
        reason = f"Momentum score: {data.momentum_score:.0f}/100"
        return score, reason, risks

    @staticmethod
    def _score_volume(data: ConfluenceInput) -> Tuple[float, str, List[str]]:
        """Rate volume quality 0-100."""
        score = data.volume_score
        risks: List[str] = []

        if data.volume_spike_ratio is not None:
            if data.volume_spike_ratio > 2.0:
                score += 15
            elif data.volume_spike_ratio > 1.5:
                score += 10
            elif data.volume_spike_ratio < 0.5:
                score -= 10
                risks.append("Volume well below average — low conviction")

        if score < 30:
            risks.append("Low volume — avoid high-volatility setups")
        elif score > 75:
            risks.append("High volume confirms — wait for structure alignment")

        score = max(0, min(100, score))
        reason = f"Volume score: {data.volume_score:.0f}/100"
        return score, reason, risks

    @staticmethod
    def _score_volatility(data: ConfluenceInput) -> Tuple[float, str, List[str]]:
        """Rate volatility quality 0-100."""
        score = data.volatility_score
        risks: List[str] = []

        if data.atr_percent is not None:
            if 0.5 <= data.atr_percent <= 2.0:
                score += 10
            elif data.atr_percent > 3.0:
                score -= 10
                risks.append(f"High ATR ({data.atr_percent:.2f}%) — wide stops, higher risk")
            elif data.atr_percent < 0.3:
                score -= 5
                risks.append(f"Low ATR ({data.atr_percent:.2f}%) — tight ranges, low volatility")

        score = max(0, min(100, score))
        reason = f"Volatility score: {data.volatility_score:.0f}/100"
        return score, reason, risks

    @staticmethod
    def _grade(final_score: int) -> str:
        """Map a 0-100 score to a grade string."""
        for threshold, label in GRADES:
            if final_score >= threshold:
                return label
        return "No Trade"

    @staticmethod
    def _determine_direction(data: ConfluenceInput) -> str:
        """Determine the directional bias from all inputs."""
        bullish = 0
        bearish = 0

        # Trend direction
        ms = data.market_structure
        if ms.trend_direction == "bullish":
            bullish += 2
        elif ms.trend_direction == "bearish":
            bearish += 2

        # EMA alignment
        if data.ema9 and data.ema20 and data.price:
            if data.ema9 > data.ema20 and data.price > data.ema9:
                bullish += 1
            elif data.ema9 < data.ema20 and data.price < data.ema9:
                bearish += 1

        # RSI
        if data.rsi is not None:
            if data.rsi > 55:
                bullish += 1
            elif data.rsi < 45:
                bearish += 1

        # MACD
        if data.macd_histogram is not None:
            if data.macd_histogram > 0:
                bullish += 1
            elif data.macd_histogram < 0:
                bearish += 1

        # Liquidity confidence
        if data.liquidity_confidence > 60:
            bullish += 1
        elif data.liquidity_confidence > 40:
            bearish += 1

        if bullish > bearish:
            return "bullish"
        elif bearish > bullish:
            return "bearish"
        return "neutral"

    @staticmethod
    def _compute_penalties(data: ConfluenceInput) -> Tuple[int, List[str], List[str]]:
        """
        Detect contradictory signals and return (total_penalty, reasons, risks).

        When the primary direction from market structure conflicts with other
        category signals, the score is penalized to prevent high scores from
        contradictory conditions.
        """
        total = 0
        reasons: List[str] = []
        risks: List[str] = []

        ms_dir = ConfluenceScorer._ms_direction(data.market_structure)
        if ms_dir == "neutral":
            return 0, reasons, risks  # No dominant direction to contradict

        # --- Structure vs Liquidity Sweep (-15) ---
        sweep_dir = ConfluenceScorer._sweep_direction(data)
        if sweep_dir and sweep_dir != ms_dir:
            total += 15
            reasons.append(f"Contradiction: {ms_dir.title()} structure vs {sweep_dir} liquidity sweep (-15)")
            risks.append(f"{ms_dir.title()} structure invalidated by opposite {sweep_dir} liquidity sweep")

        # --- Structure vs MACD (-10) ---
        macd_dir = ConfluenceScorer._macd_direction(data)
        if macd_dir and macd_dir != ms_dir:
            total += 10
            reasons.append(f"Contradiction: {ms_dir.title()} structure vs {macd_dir} MACD (-10)")
            risks.append(f"MACD {macd_dir} diverges from {ms_dir} market structure")

        # --- Structure vs Weak Volume (-8) ---
        if ConfluenceScorer._is_weak_volume(data):
            total += 8
            reasons.append(f"Contradiction: {ms_dir.title()} structure vs weak volume (-8)")
            risks.append(f"Low volume undermines {ms_dir} structure conviction")

        # --- Structure vs High Volatility (-5) ---
        if ConfluenceScorer._is_high_volatility(data):
            total += 5
            reasons.append(f"Contradiction: {ms_dir.title()} structure vs high volatility risk (-5)")
            risks.append(f"Elevated volatility contradicts {ms_dir} directional structure")

        # --- Trend vs Momentum mismatch (-8, but only if structure is neutral) ---
        if ms_dir == "neutral":
            trend_dir = ConfluenceScorer._trend_direction(data)
            momo_dir = ConfluenceScorer._momentum_direction(data)
            if trend_dir and momo_dir and trend_dir != momo_dir:
                total += 8
                reasons.append(f"Contradiction: {trend_dir.title()} trend vs {momo_dir} momentum (-8)")
                risks.append(f"Trend ({trend_dir}) and momentum ({momo_dir}) are pulling in opposite directions")

        # --- Trend vs Liquidity confidence mismatch (-6) ---
        trend_dir = ConfluenceScorer._trend_direction(data)
        liq_dir = ConfluenceScorer._liquidity_direction(data)
        if trend_dir and liq_dir and trend_dir != liq_dir and ms_dir == "neutral":
            total += 6
            reasons.append(f"Contradiction: {trend_dir.title()} trend vs {liq_dir} liquidity bias (-6)")
            risks.append("Trend and liquidity structure disagree — wait for alignment")

        return total, reasons, risks

    @staticmethod
    def _ms_direction(ms: MarketStructureInput) -> str:
        """Determine the dominant market structure direction."""
        if ms.trend_direction in ("bullish", "bearish"):
            return ms.trend_direction
        if ms.higher_highs and ms.higher_lows:
            return "bullish"
        if ms.lower_highs and ms.lower_lows:
            return "bearish"
        return "neutral"

    @staticmethod
    def _sweep_direction(data: ConfluenceInput) -> str | None:
        """
        Infer the dominant liquidity sweep direction.

        - Bearish sweep: price spiked above resistance (bullish pools), then reversed.
        - Bullish sweep: price dipped below support (bearish pools), then reversed.
        Returns None when direction is ambiguous.
        """
        if data.sweep_count == 0:
            return None
        if data.bullish_liquidity_pools > data.bearish_liquidity_pools:
            return "bearish"
        if data.bearish_liquidity_pools > data.bullish_liquidity_pools:
            return "bullish"
        return None

    @staticmethod
    def _macd_direction(data: ConfluenceInput) -> str | None:
        """Determine MACD directional bias."""
        if data.macd_histogram is None:
            return None
        return "bullish" if data.macd_histogram > 0 else "bearish" if data.macd_histogram < 0 else "neutral"

    @staticmethod
    def _is_weak_volume(data: ConfluenceInput) -> bool:
        """Check if volume is weak relative to average."""
        if data.volume_spike_ratio is not None and data.volume_spike_ratio < 0.7:
            return True
        if data.volume_score < 30:
            return True
        return False

    @staticmethod
    def _is_high_volatility(data: ConfluenceInput) -> bool:
        """Check if volatility is dangerously high."""
        if data.atr_percent is not None and data.atr_percent > 3.0:
            return True
        if data.volatility_score < 30:
            return True
        return False

    @staticmethod
    def _trend_direction(data: ConfluenceInput) -> str | None:
        """Determine trend directional bias from EMA alignment."""
        if data.ema9 is not None and data.ema20 is not None and data.price is not None:
            if data.ema9 > data.ema20 and data.price > data.ema9:
                return "bullish"
            if data.ema9 < data.ema20 and data.price < data.ema9:
                return "bearish"
        return None

    @staticmethod
    def _momentum_direction(data: ConfluenceInput) -> str | None:
        """Determine momentum directional bias."""
        votes = 0
        if data.rsi is not None:
            votes += 1 if data.rsi > 55 else -1 if data.rsi < 45 else 0
        if data.macd_histogram is not None:
            votes += 1 if data.macd_histogram > 0 else -1 if data.macd_histogram < 0 else 0
        if votes > 0:
            return "bullish"
        if votes < 0:
            return "bearish"
        return None

    @staticmethod
    def _liquidity_direction(data: ConfluenceInput) -> str | None:
        """Determine directional bias from liquidity data."""
        if data.liquidity_confidence > 60:
            return "bullish"
        if data.liquidity_confidence > 40:
            return "bearish"
        return None
