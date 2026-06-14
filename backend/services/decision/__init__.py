
"""
Master AI Decision Engine.

Combines all deterministic engines (market data, indicators, market structure,
liquidity, confluence) with Gemma Vision analysis into a single
trading decision.

Rules:
- AI never calculates indicators, BOS, or liquidity
- AI only interprets results from deterministic engines
- If deterministic and vision disagree → NO TRADE with "Analysis Conflict"
- Outputs structured JSON only

Usage:
    from services.decision import MasterDecisionEngine, DecisionInput

    result = MasterDecisionEngine.decide(DecisionInput(symbol="BTCUSDT"))
    print(result.direction, result.confidence)
"""

from services.decision.engine import MasterDecisionEngine
from services.decision.models import (
    DecisionInput,
    DecisionOutput,
    DecisionDirection,
    DecisionLevel,
    DeterministicAssessment,
    VisionInterpretation,
)

__all__ = [
    "MasterDecisionEngine",
    "DecisionInput",
    "DecisionOutput",
    "DecisionDirection",
    "DecisionLevel",
    "DeterministicAssessment",
    "VisionInterpretation",
]
