from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ConfluenceGrade(str, Enum):
    ELITE = "Elite Setup"
    HIGH_PROBABILITY = "High Probability"
    TRADABLE = "Tradable"
    NO_TRADE = "No Trade"


class MarketStructureInput(BaseModel):
    """Market structure signals from inline or external analysis."""
    trend_direction: str = "neutral"  # 'bullish' | 'bearish' | 'neutral'
    swing_highs: int = 0
    swing_lows: int = 0
    higher_highs: bool = False
    higher_lows: bool = False
    lower_highs: bool = False
    lower_lows: bool = False
    market_regime: str = "ranging"  # 'trending' | 'ranging' | 'volatile'
    structure_score: float = Field(default=0.0, ge=0.0, le=100.0)


class ConfluenceInput(BaseModel):
    """All inputs for the confluence scoring engine."""
    symbol: str = ""
    timeframe: str = ""

    # Indicator Engine outputs
    trend_score: float = Field(default=0.0, ge=0.0, le=100.0)
    momentum_score: float = Field(default=0.0, ge=0.0, le=100.0)
    volume_score: float = Field(default=0.0, ge=0.0, le=100.0)
    volatility_score: float = Field(default=0.0, ge=0.0, le=100.0)

    rsi: Optional[float] = None
    macd_histogram: Optional[float] = None
    ema9: Optional[float] = None
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    price: Optional[float] = None
    atr_percent: Optional[float] = None
    volume_spike_ratio: Optional[float] = None

    # Market Structure inputs
    market_structure: MarketStructureInput = Field(default_factory=MarketStructureInput)

    # Liquidity Engine outputs
    liquidity_confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    fvg_count: int = 0
    order_block_count: int = 0
    breaker_block_count: int = 0
    sweep_count: int = 0
    equal_high_count: int = 0
    equal_low_count: int = 0
    bullish_liquidity_pools: int = 0
    bearish_liquidity_pools: int = 0


class CategoryScore(BaseModel):
    """Score breakdown for a single category."""
    name: str = ""
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_score: float = Field(default=0.0, ge=0.0, le=100.0)
    weighted_score: float = Field(default=0.0, ge=0.0, le=100.0)
    reason: str = ""


class ConfluenceOutput(BaseModel):
    """Final confluence scoring output."""
    score: int = Field(default=0, ge=0, le=100)
    grade: str = "No Trade"
    direction: str = "neutral"  # 'bullish' | 'bearish' | 'neutral'
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    category_scores: List[CategoryScore] = Field(default_factory=list)


class ScoreRequest(BaseModel):
    """Request to compute a confluence score."""
    symbol: str
    timeframe: str = "5m"
    exchange: str = "binance"
    data: ConfluenceInput = Field(default_factory=ConfluenceInput)


class ScoreResponse(BaseModel):
    success: bool
    data: Optional[ConfluenceOutput] = None
    error: Optional[str] = None
    cached: bool = False
