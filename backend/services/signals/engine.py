
"""
Signal Generator Engine.

Takes Master AI Decision Engine output and generates Signal Records.

Signal type mapping:
- Score >= 80, bullish  → Strong Buy
- Score >= 70, bullish  → Buy
- Score >= 80, bearish  → Strong Sell
- Score >= 70, bearish  → Sell
- Score < 70            → No signal (No Trade)
- Neutral direction     → Neutral (only if above threshold)
"""

import uuid
import time
from typing import Optional

from services.signals.models import (
    SignalCreateRequest,
    SignalRecord,
    SignalStatus,
    SignalType,
    ValidationStatus,
)


class SignalGenerator:
    """
    Generates validated signal records from decision engine output.

    Rules:
    - Confidence < 70: No signal generated
    - Confidence >= 80 + bullish: Strong Buy
    - Confidence >= 70 + bullish: Buy
    - Confidence >= 80 + bearish: Strong Sell
    - Confidence >= 70 + bearish: Sell
    """

    NO_TRADE_THRESHOLD = 70

    @staticmethod
    def from_decision(
        symbol: str,
        timeframe: str,
        direction: str,
        confidence: int,
        confluence_score: int,
        entry: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        take_profit_2: Optional[float] = None,
        risk_reward_1: Optional[float] = None,
        risk_reward_2: Optional[float] = None,
        reasoning: str = "",
        reasons: Optional[list] = None,
        risks: Optional[list] = None,
        strategy_version: str = "v1",
        session: str = "",
    ) -> Optional[SignalRecord]:
        """
        Generate a signal record from decision engine parameters.

        Returns None if confidence is below the NO_TRADE threshold.
        """
        if confidence < SignalGenerator.NO_TRADE_THRESHOLD:
            return None

        signal_type = SignalGenerator._classify(direction, confidence)
        if signal_type == SignalType.NEUTRAL:
            return None

        now = int(time.time() * 1000)

        return SignalRecord(
            id=str(uuid.uuid4()),
            symbol=symbol.upper(),
            timeframe=timeframe,
            direction=direction,
            signal_type=signal_type,
            entry=round(entry, 2) if entry else None,
            stop_loss=round(stop_loss, 2) if stop_loss else None,
            take_profit_1=round(take_profit_1, 2) if take_profit_1 else None,
            take_profit_2=round(take_profit_2, 2) if take_profit_2 else None,
            risk_reward_1=round(risk_reward_1, 2) if risk_reward_1 else None,
            risk_reward_2=round(risk_reward_2, 2) if risk_reward_2 else None,
            confidence=confidence,
            confluence_score=confluence_score,
            reasoning=reasoning,
            reasons=reasons or [],
            risks=risks or [],
            status=SignalStatus.ACTIVE,
            validation_status=ValidationStatus.PENDING,
            strategy_version=strategy_version,
            session=session,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _classify(direction: str, confidence: int) -> SignalType:
        """Classify signal type based on direction and confidence."""
        if direction == "bullish":
            return SignalType.STRONG_BUY if confidence >= 80 else SignalType.BUY
        elif direction == "bearish":
            return SignalType.STRONG_SELL if confidence >= 80 else SignalType.SELL
        return SignalType.NEUTRAL
