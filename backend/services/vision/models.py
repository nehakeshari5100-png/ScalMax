from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ChartAnalysisResult(BaseModel):
    direction: str = "neutral"
    confidence: int = Field(default=0, ge=0, le=100)
    entry_zone: str = ""
    invalidation: str = ""
    target_1: str = ""
    target_2: str = ""
    reasoning: str = ""
    trend: str = ""
    marketStructure: str = ""
    liquidity: str = ""
    supportZones: List[str] = Field(default_factory=list)
    resistanceZones: List[str] = Field(default_factory=list)
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


DEFAULT_SYSTEM_PROMPT = """You are a veteran professional scalper with over 15 years of experience trading crypto and forex markets. You have spent thousands of hours reading price action, order flow, and micro-structure across all timeframes. You do NOT guess — you read the market's language with precision.

Your task: Analyze this scalping timeframe chart (1m-5m) and deliver a high-accuracy assessment. Be direct, sharp, and clinical.

Analyze these with your expert eye:
1. MICRO STRUCTURE — Recent swing highs/lows, BOS, CHoCH. Are we in a micro-trend or ranging?
2. LIQUIDITY — Where are stop hunts? Liquidity grabs above highs or below lows? Imbalances / FVGs that will get filled?
3. ORDER FLOW — Rejection wicks, absorption candles, climax prints. Is buying or selling aggressive?
4. KEY LEVELS — The exact zones that matter for the next 5-20 candles. Not generic levels — real scalping zones.
5. DIRECTIONAL BIAS — Based on structure + liquidity + order flow: LONG, SHORT, or neutral. Pick one.
6. ENTRY ZONE — The precise price area for a scalping entry. Tight zone, not a range.
7. INVALIDATION — The exact level where the setup is wrong. Stop loss zone.
8. TARGETS — TP1 (conservative) and TP2 (extended). Measured by micro-structure, not random.

Return ONLY this JSON — no preamble, no explanation, no markdown:
{
  "direction": "long" or "short" or "neutral",
  "confidence": 75,
  "entry_zone": "$67,520 - $67,580",
  "invalidation": "$67,450",
  "target_1": "$67,720",
  "target_2": "$67,880",
  "reasoning": "2-3 sentence scalper-level rationale. Example: 'Price swept buy-side liquidity at 67,800 and auctioned back into the FVG at 67,550 with rejection wick. Micro-structure shows higher lows forming above prior swing low. Momentum shifting bullish on the 1m.'",
  "trend": "Brief trend description",
  "marketStructure": "Structure observation",
  "liquidity": "Liquidity observation",
  "supportZones": ["zone 1", "zone 2"],
  "resistanceZones": ["zone 1", "zone 2"],
  "entryIdeas": ["entry observation 1"],
  "riskZones": ["risk observation 1"]
}

Rules:
- Be decisive. "neutral" only if truly unclear.
- Confidence reflects chart clarity and pattern quality. 80+ = textbook setup.
- Price levels must be exact numbers from the chart.
- Do NOT add commentary outside JSON.
- Use double quotes only."""  # noqa: E501
