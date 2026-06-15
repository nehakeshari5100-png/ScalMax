from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class VisionObservation(BaseModel):
    """AI extracts only observations — no trade decision."""
    quality: str = "READABLE"  # READABLE or UNREADABLE_CHART
    trend: str = "neutral"  # bullish, bearish, neutral
    marketStructure: str = "ranging"  # HH_HL, LH_LL, HH_LL, LH_HL, ranging
    momentum: str = "moderate"  # strong, moderate, weak
    liquidity: str = "none"  # above_highs, below_lows, both, none
    volume: str = "medium"  # high, medium, low
    confidence: int = Field(default=0, ge=0, le=100)
    entry_zone: str = ""
    invalidation: str = ""
    target_1: str = ""
    target_2: str = ""


class ScoringDetail(BaseModel):
    marketStructure: int = 0
    liquidity: int = 0
    momentum: int = 0
    trend: int = 0
    volume: int = 0
    confluence: int = 0
    bullScore: int = 0
    bearScore: int = 0
    overall: int = 0


class ScoredTrade(BaseModel):
    """Engine output — computed from observations, not from AI directly."""
    signal: str = "NEUTRAL"  # STRONG_LONG, LONG, NEUTRAL, SHORT, STRONG_SHORT
    confidence: int = Field(default=0, ge=0, le=100)
    bullScore: int = 0
    bearScore: int = 0
    entry_zone: str = ""
    stop_loss: str = ""
    take_profit_1: str = ""
    take_profit_2: str = ""
    risk_reward: str = ""
    scoring: ScoringDetail = Field(default_factory=ScoringDetail)


class ChartAnalysisResult(BaseModel):
    """Legacy — kept for backward compat. New code uses ScoredTrade."""
    direction: str = "NO_TRADE"
    confidence: int = Field(default=0, ge=0, le=100)
    entry_zone: str = ""
    invalidation: str = ""
    target_1: str = ""
    target_2: str = ""
    target_3: str = ""
    risk_reward: str = ""
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    trend: str = ""
    marketStructure: str = ""
    liquidity: str = ""
    fvg: str = ""
    orderBlocks: str = ""
    bos: str = ""
    choch: str = ""
    rsi: str = ""
    ema: str = ""
    trendStrength: str = ""
    entryIdeas: List[str] = Field(default_factory=list)
    riskZones: List[str] = Field(default_factory=list)
    detectedPlatform: str = ""
    timeframe: str = ""
    symbol: str = ""
    liquiditySweeps: str = ""
    equalHighsLows: str = ""
    premiumDiscountZone: str = ""
    expectedProfitLoss: str = ""
    scoring: "ScoringDetail" = Field(default_factory=ScoringDetail)


class VisionAnalysisResponse(BaseModel):
    success: bool
    data: Optional[ChartAnalysisResult] = None
    trade: Optional[ScoredTrade] = None
    observation: Optional[VisionObservation] = None
    raw: Optional[str] = None
    model: str = ""
    error: Optional[str] = None


OBSERVATION_PROMPT = """Analyze this chart. Return ONLY this exact JSON — no explanations, no markdown:
{
  "quality": "READABLE" or "UNREADABLE_CHART",
  "trend": "bullish" or "bearish" or "neutral",
  "marketStructure": "HH_HL" or "LH_LL" or "HH_LL" or "LH_HL" or "ranging",
  "momentum": "strong" or "moderate" or "weak",
  "liquidity": "above_highs" or "below_lows" or "both" or "none",
  "volume": "high" or "medium" or "low",
  "confidence": 75,
  "entry_zone": "67250-67300",
  "invalidation": "67180",
  "target_1": "67450",
  "target_2": "67600"
}
Respond with ONLY the JSON. If chart is unreadable, set quality to "UNREADABLE_CHART"."""  # noqa: E501
