from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class LiquidityDetails(BaseModel):
    equalHighs: bool = False
    equalLows: bool = False
    liquiditySweeps: bool = False
    stopHunts: bool = False


class VisionObservation(BaseModel):
    quality: str = "READABLE"
    trend: str = "neutral"
    marketStructure: str = "ranging"
    momentum: str = "moderate"
    liquidity: str = "none"
    volume: str = "medium"
    confluence: str = "none"
    liquidityDetails: LiquidityDetails = Field(default_factory=LiquidityDetails)
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


class RiskAssessment(BaseModel):
    accountSize: float = 0
    riskPercent: float = 0
    riskAmount: float = 0
    positionSize: float = 0
    maxLoss: float = 0
    expectedProfit: float = 0
    riskRewardRatio: str = ""


class ScoredTrade(BaseModel):
    signal: str = "NEUTRAL"
    confidence: int = Field(default=0, ge=0, le=100)
    bullScore: int = 0
    bearScore: int = 0
    entry_zone: str = ""
    stop_loss: str = ""
    take_profit_1: str = ""
    take_profit_2: str = ""
    risk_reward: str = ""
    marketStructureSummary: str = ""
    liquiditySummary: str = ""
    riskSummary: str = ""
    riskAssessment: RiskAssessment = Field(default_factory=RiskAssessment)
    scoring: ScoringDetail = Field(default_factory=ScoringDetail)


class ChartAnalysisResult(BaseModel):
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


OBSERVATION_PROMPT = """You are a professional chart analyst. Analyze this chart image and return ONLY valid JSON with these exact fields — no explanations, no markdown, no code fences:

{
  "quality": "READABLE",
  "trend": "bullish",
  "marketStructure": "HH_HL",
  "momentum": "strong",
  "liquidity": "below_lows",
  "volume": "high",
  "confluence": "support",
  "liquidityDetails": {
    "equalHighs": false,
    "equalLows": true,
    "liquiditySweeps": true,
    "stopHunts": false
  },
  "confidence": 75,
  "entry_zone": "67250-67300",
  "invalidation": "67180",
  "target_1": "67450",
  "target_2": "67600"
}

Rules:
- quality: "READABLE" or "UNREADABLE_CHART"
- trend: "bullish", "bearish", or "neutral"
- marketStructure: "HH_HL" (higher highs + higher lows = bullish), "LH_LL" (lower highs + lower lows = bearish), "HH_LL" (higher highs + lower lows = bullish bias), "LH_HL" (lower highs + higher lows = bearish bias), or "ranging"
- momentum: "strong", "moderate", or "weak"
- liquidity: "above_highs" (sell-side), "below_lows" (buy-side), "both", or "none"
- volume: "high", "medium", or "low"
- confluence: "support" (bounce at support), "resistance" (reject at resistance), "breakout" (breaking a level), "rejection" (wick rejection), or "none"
- liquidityDetails: detect equal highs, equal lows, liquidity sweeps (price spiked beyond a level then reversed), stop hunts (sharp moves hitting obvious stops)
- confidence: 0-100 — how confident you are in your observation
- entry_zone: best entry price range or level
- invalidation: price level where the setup is invalid
- target_1: first profit target
- target_2: second profit target

If chart is unreadable (blurry, cropped, no candles/bars visible), set quality to "UNREADABLE_CHART" and all other fields to null/empty defaults.

Respond with ONLY the JSON object. No other text."""  # noqa: E501
