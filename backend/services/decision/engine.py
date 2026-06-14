
"""
Master AI Decision Engine.

Combines all deterministic engines with Gemma Vision analysis.

Rules:
- AI never calculates indicators, BOS, or liquidity
- AI only interprets results from deterministic engines
- If deterministic and vision disagree → NO TRADE
- Returns JSON decision output only
"""

import math
from typing import Optional

from services.decision.models import (
    DecisionDirection,
    DecisionInput,
    DecisionLevel,
    DecisionOutput,
    DeterministicAssessment,
    VisionInterpretation,
)


class MasterDecisionEngine:
    """
    Combines all engine outputs into a single trading decision.

    The engine:
    1. Runs deterministic assessment via confluence scorer
    2. Incorporates vision analysis if provided
    3. Detects conflicts between deterministic and vision
    4. Generates entry/SL/TP levels
    5. Returns structured JSON decision
    """

    @staticmethod
    def decide(input_data: DecisionInput) -> DecisionOutput:
        """
        Produce a final trading decision from all available inputs.

        This is the only AI-authorized function — it interprets
        deterministic engine results and vision analysis. It does
        NOT calculate any raw indicator, BOS, or liquidity value.
        """
        # 1. Run deterministic assessment
        det = MasterDecisionEngine._assess_deterministic(input_data)

        # 2. Process vision interpretation (if provided)
        vision = input_data.vision_analysis

        # 3. Conflict detection
        conflict = MasterDecisionEngine._detect_conflict(det, vision)

        # 4. Generate decision
        if conflict or not det or det.direction == "neutral":
            return MasterDecisionEngine._no_trade(det, vision, conflict)

        # Check minimum confidence thresholds
        if det.confidence < 30:
            return MasterDecisionEngine._no_trade(
                det, vision, "Low Confidence"
            )

        # 5. Generate levels
        levels = MasterDecisionEngine._generate_levels(
            input_data.price or 0,
            det.direction,
            input_data,
        )

        # 6. Build reasoning
        reasoning_parts = []
        if det:
            reasoning_parts.append(
                f"Confluence: {det.confluence_grade} ({det.confluence_score}/100)"
            )
            if det.reasons:
                reasoning_parts.extend(det.reasons[:3])
        if vision:
            reasoning_parts.append(f"Vision: {vision.trend}")

        reasoning = " | ".join(reasoning_parts)

        # 7. Build output
        return DecisionOutput(
            direction=(
                DecisionDirection.LONG
                if det.direction == "bullish"
                else DecisionDirection.SHORT
            ),
            confidence=det.confidence,
            levels=levels,
            reasoning=reasoning,
            reasons=det.reasons[:5],
            risks=det.risks[:3],
            deterministic=det,
            vision=vision,
            is_tradeable=det.confidence >= 50,
        )

    @staticmethod
    def _assess_deterministic(
        input_data: DecisionInput,
    ) -> Optional[DeterministicAssessment]:
        """
        Run the deterministic engine ensemble.

        AI does NOT calculate any raw indicator, BOS, or liquidity.
        This method ONLY reads pre-computed values and interprets them
        through the confluence scorer.
        """
        # Use deterministic override if provided (from integration orchestrator)
        if input_data.deterministic_override:
            return input_data.deterministic_override

        try:
            from services.confluence import score_confluence, ConfluenceInput
            from services.confluence.models import MarketStructureInput
        except ImportError:
            return None

        ci = ConfluenceInput(
            symbol=input_data.symbol,
            timeframe=input_data.timeframe,
        )

        result = score_confluence(ci)

        direction = result.direction

        return DeterministicAssessment(
            direction=direction,
            confidence=result.score,
            confluence_score=result.score,
            confluence_grade=result.grade,
            reasons=result.reasons[:5],
            risks=result.risks[:3],
            source="deterministic",
        )

    @staticmethod
    def _detect_conflict(
        det: Optional[DeterministicAssessment],
        vision: Optional[VisionInterpretation],
    ) -> Optional[str]:
        """
        Detect conflicts between deterministic and vision analysis.

        If they disagree on direction, return a conflict reason.
        AI only interprets — it never calculates.
        """
        if not det or not vision:
            return None

        if not vision.trend:
            return None

        # Interpret vision trend as direction
        vision_dir = MasterDecisionEngine._interpret_trend(vision.trend)
        det_dir = det.direction

        if vision_dir == "neutral" or det_dir == "neutral":
            return None

        if vision_dir != det_dir:
            return "Analysis Conflict"

        # Check confidence disagreement
        if vision.confidence > 0 and det.confidence > 0:
            conf_diff = abs(vision.confidence - det.confidence)
            if conf_diff > 50:
                return "Low Confidence"

        return None

    @staticmethod
    def _interpret_trend(trend_text: str) -> str:
        """
        Interpret a vision trend description as a direction.

        AI only reads the text — it does not calculate the trend.
        """
        lower = trend_text.lower()
        if any(w in lower for w in ["uptrend", "bullish", "higher high", "buying"]):
            return "bullish"
        if any(w in lower for w in ["downtrend", "bearish", "lower low", "selling"]):
            return "bearish"
        return "neutral"

    @staticmethod
    def _generate_levels(
        price: float,
        direction: str,
        input_data: DecisionInput,
    ) -> DecisionLevel:
        """
        Generate entry, stop loss, and take profit levels.

        SL and TP are calculated as fixed percentages of price.
        These are pure math estimates — AI does not predict levels.
        """
        if price <= 0:
            return DecisionLevel()

        # Default offsets (can be overridden by configuration)
        sl_pct = 0.008  # 0.8%
        tp1_pct = 0.012  # 1.2%
        tp2_pct = 0.020  # 2.0%

        if direction == "bullish":
            entry = price
            sl = entry * (1 - sl_pct)
            tp1 = entry * (1 + tp1_pct)
            tp2 = entry * (1 + tp2_pct)
        elif direction == "bearish":
            entry = price
            sl = entry * (1 + sl_pct)
            tp1 = entry * (1 - tp1_pct)
            tp2 = entry * (1 - tp2_pct)
        else:
            return DecisionLevel()

        risk = abs(entry - sl)
        rr1 = round(abs(tp1 - entry) / max(risk, 0.01), 2) if risk > 0 else 0.0
        rr2 = round(abs(tp2 - entry) / max(risk, 0.01), 2) if risk > 0 else 0.0

        return DecisionLevel(
            entry=round(entry, 2),
            stop_loss=round(sl, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            risk_reward_1=rr1,
            risk_reward_2=rr2,
        )

    @staticmethod
    def _no_trade(
        det: Optional[DeterministicAssessment],
        vision: Optional[VisionInterpretation],
        conflict: Optional[str] = None,
    ) -> DecisionOutput:
        """Return a NO TRADE decision."""
        parts = []
        if conflict:
            parts.append(f"No Trade: {conflict}")
            if conflict == "Analysis Conflict":
                parts.append("Deterministic and vision analysis disagree")
        else:
            parts.append("No Trade: insufficient alignment")

        return DecisionOutput(
            direction=DecisionDirection.NO_TRADE,
            confidence=0,
            reasoning=" | ".join(parts),
            reasons=parts,
            deterministic=det,
            vision=vision,
            conflict=conflict,
            is_tradeable=False,
        )
