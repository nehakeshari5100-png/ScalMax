from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DecisionDirection(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"
    NO_TRADE = "no_trade"


class VisionInterpretation(BaseModel):
    trend: str = ""
    market_structure: str = ""
    liquidity: str = ""
    support_zones: List[str] = Field(default_factory=list)
    resistance_zones: List[str] = Field(default_factory=list)
    entry_ideas: List[str] = Field(default_factory=list)
    risk_zones: List[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)
    source: str = "vision"


class DeterministicAssessment(BaseModel):
    direction: str = "neutral"
    confidence: int = Field(default=0, ge=0, le=100)
    confluence_score: int = Field(default=0, ge=0, le=100)
    confluence_grade: str = "No Trade"
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    volatility_score: float = 0.0
    liquidity_confidence: float = 0.0
    market_structure_score: float = 0.0
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    source: str = "deterministic"


class DecisionLevel(BaseModel):
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    risk_reward_1: Optional[float] = None
    risk_reward_2: Optional[float] = None


class DecisionOutput(BaseModel):
    direction: DecisionDirection = DecisionDirection.NO_TRADE
    confidence: int = Field(default=0, ge=0, le=100)
    levels: DecisionLevel = Field(default_factory=DecisionLevel)
    reasoning: str = ""
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    deterministic: Optional[DeterministicAssessment] = None
    vision: Optional[VisionInterpretation] = None
    conflict: Optional[str] = None
    is_tradeable: bool = False


class DecisionInput(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"
    exchange: str = "binance"
    price: Optional[float] = None
    include_vision: bool = False
    vision_analysis: Optional[VisionInterpretation] = None
    api_key: Optional[str] = None
    vision_model: str = "google/gemma-3-27b-it"
    deterministic_override: Optional[DeterministicAssessment] = None


class DecisionResponse(BaseModel):
    success: bool
    data: Optional[DecisionOutput] = None
    error: Optional[str] = None
