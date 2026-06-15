from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ChartAnalysisResult(BaseModel):
    direction: str = "NO_TRADE"
    confidence: int = Field(default=0, ge=0, le=100)
    entry_zone: str = ""
    invalidation: str = ""
    target_1: str = ""
    target_2: str = ""
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


class VisionAnalysisRequest(BaseModel):
    model: str = "google/gemma-3-27b-it"
    prompt: str = ""
    image_base64: str = ""


class VisionAnalysisResponse(BaseModel):
    success: bool
    data: Optional[ChartAnalysisResult] = None
    raw: Optional[str] = None
    model: str = ""
    error: Optional[str] = None


DEFAULT_SYSTEM_PROMPT = """You are a professional crypto scalper with 15+ years of experience. Analyze this chart with surgical precision and return ONLY valid JSON — no preamble, no markdown.

Return this exact JSON structure:
{
  "direction": "LONG" or "SHORT" or "NO_TRADE",
  "confidence": 75,
  "entry_zone": "67250-67300",
  "invalidation": "67180",
  "target_1": "67450",
  "target_2": "67600",
  "risk_reward": "1:2.5",
  "reasons": ["Higher low formed above prior swing low", "Price swept buy-side liquidity at 67800"],
  "warnings": ["Low volume on breakout", "Resistance cluster above"],
  "trend": "Uptrend on 1m — higher highs and higher lows",
  "marketStructure": "HH above prior HH, HL above prior HL — bullish micro-trend",
  "liquidity": "Buy-side liquidity above 67800 was swept. Sell-side liquidity below 67100 untapped.",
  "fvg": "Bullish FVG at 67250-67300 from the impulse move",
  "orderBlocks": "Bullish OB at 67180-67220 — prior resistance turned support",
  "bos": "BOS confirmed above 67400 — prior structure high broken",
  "choch": "No CHoCH detected — trend intact",
  "rsi": "RSI at 58 — room to run, not overbought",
  "ema": "Price above EMA9 and EMA20 — bullish alignment",
  "trendStrength": "Moderate — momentum increasing",
  "entryIdeas": ["Entry on retest of 67250-67300 FVG", "Aggressive entry at market with tight SL"],
  "riskZones": ["Below 67180 — structure invalidation", "Rejection at 67600 resistance"]
}

Analysis requirements:
1. Market Structure: Identify HH/HL/LH/LL and trend direction
2. Liquidity: Identify liquidity pools, equal highs/lows, sweeps
3. Smart Money Concepts: FVG, Order Blocks, Break of Structure, Change of Character
4. Indicators: RSI level, EMA alignment, trend strength
5. Trade Setup: Direction (LONG/SHORT/NO_TRADE), Confidence 0-100, Entry zone, Stop loss, TP1, TP2, Risk/Reward, Reasons, Warnings

Rules:
- Be decisive. NO_TRADE only if truly unclear.
- Confidence reflects chart clarity. 80+ = textbook.
- Price levels must be exact from the chart.
- Do NOT add any commentary outside JSON.
- Use double quotes only.
- If image is unreadable or quality is too low, set direction to "NO_TRADE" and confidence to 0."""  # noqa: E501
