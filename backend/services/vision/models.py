from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class LiquidityDetails(BaseModel):
    equalHighs: bool = False
    equalLows: bool = False
    liquiditySweeps: bool = False
    stopHunts: bool = False


class VisionObservation(BaseModel):
    quality: str = "READABLE"
    detectedSymbol: str = ""
    detectedTimeframe: str = ""
    detectedExchange: str = ""
    detectedCurrentPrice: str = ""
    detectedIndicatorNames: str = ""
    isHigherHighs: Optional[bool] = None
    isHigherLows: Optional[bool] = None
    isLowerHighs: Optional[bool] = None
    isLowerLows: Optional[bool] = None
    ocrConfidence: int = Field(default=0, ge=0, le=100)
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
    reason: str = ""
    observedTrend: str = ""
    observedStructure: str = ""
    observedMomentum: str = ""
    observedSupport: str = ""
    observedResistance: str = ""


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
    reason: str = ""
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


OBSERVATION_PROMPT = """You are a professional chart analyst. You MUST follow these phases in order. Never skip phases. Never guess.

PHASE 1 — CHART OCR (extract these before any analysis)
Extract from the chart image:
- detectedSymbol: The trading pair or stock symbol (e.g. ETHUSDT, BTCUSD, AAPL, SPY). Look for labels at top-left or top-right.
- detectedTimeframe: The timeframe shown (e.g. 1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W, 1M). Look for timeframe labels.
- detectedExchange: The exchange or platform (e.g. Binance, Bybit, TradingView, MT4). Look for logos/watermarks.
- detectedCurrentPrice: The most recent visible price on the chart. Be precise.
- detectedIndicatorNames: Any visible indicator names (e.g. EMA 20, SMA 50, RSI, MACD, VWAP). Empty if none visible.
- ocrConfidence: 0-100. 90+ = all labels clearly readable. 80-89 = mostly readable with minor doubt. <80 = blurry, unreadable, or missing labels.

PHASE 2 — STRUCTURE EXTRACTION
Examine the chart's swing points. Answer each as true or false:
- isHigherHighs: Is price clearly making higher swing highs compared to previous swing highs? Look at 3+ recent swings.
- isHigherLows: Is price clearly making higher swing lows compared to previous swing lows?
- isLowerHighs: Is price clearly making lower swing highs?
- isLowerLows: Is price clearly making lower swing lows?
If you cannot see clear swing points, set all to false and marketStructure to "unclear".

PHASE 3 — MARKET CLASSIFICATION (apply these rules strictly)
- trend: "bullish" if isHigherHighs AND isHigherLows. "bearish" if isLowerHighs AND isLowerLows. "neutral" otherwise.
- marketStructure: "HH_HL" (higher highs + higher lows = uptrend), "LH_LL" (lower highs + lower lows = downtrend), "HH_LL" (higher highs + lower lows = volatile, bullish bias), "LH_HL" (lower highs + higher lows = compressing, bearish bias), "ranging" (no clear HH/HL/LH/LL pattern), "unclear" (cannot determine).

HARD RULES — These are mandatory. Violating them will cause incorrect analysis.
- isHigherHighs=true AND isHigherLows=true → SHORT is FORBIDDEN. You must classify as bullish/LONG.
- isLowerHighs=true AND isLowerLows=true → LONG is FORBIDDEN. You must classify as bearish/SHORT.
- isHigherHighs=isHigherLows=isLowerHighs=isLowerLows=false OR marketStructure="ranging" → NO TRADE. No directional bias.
- Never set a direction when structure is ranging or unclear.

PHASE 4 — PRICE VALIDATION
- entry_zone must be within 5% of detectedCurrentPrice
- invalidation (stop loss) must be within 10% of detectedCurrentPrice
- target_1 and target_2 must be within 30% of detectedCurrentPrice
- If a price is outside these ranges, leave it as empty string ""
- Example: current price 4250, valid entry 4200-4300, valid SL 4000-4500, valid TP up to 5500

PHASE 5 — REASONING (derive signal from evidence, never bias)
- reason: Step-by-step explanation of what was observed and why it leads to the signal. Include specific price levels and swing points.
- observedTrend: Describe the trend direction with specific price references
- observedStructure: Describe the specific swing highs and lows visible (e.g. "Swing low at 4200 on June 10, swing high at 4350 on June 12")
- observedMomentum: Describe momentum with evidence (e.g. "Consecutive bullish candles, high volume on breakouts")
- observedSupport: List specific support levels visible on the chart
- observedResistance: List specific resistance levels visible on the chart

HALLUCINATION PREVENTION:
- If you cannot clearly see symbol, price, and timeframe labels → set ocrConfidence below 80
- If you cannot see clear swing highs and lows → set all isHigher/isLower fields to false and marketStructure to "unclear"
- Never invent patterns, indicators, liquidity sweeps, or stop hunts that are not clearly visible
- Never invent indicator values (RSI numbers, EMA prices) unless explicitly shown
- Do not guess. If unsure, set low confidence.

Return ONLY valid JSON. No explanations, no markdown, no code fences. Example:

{
  "quality": "READABLE",
  "detectedSymbol": "ETHUSDT",
  "detectedTimeframe": "15m",
  "detectedExchange": "Binance",
  "detectedCurrentPrice": "4250",
  "detectedIndicatorNames": "EMA 20, EMA 50",
  "isHigherHighs": true,
  "isHigherLows": true,
  "isLowerHighs": false,
  "isLowerLows": false,
  "ocrConfidence": 92,
  "trend": "bullish",
  "marketStructure": "HH_HL",
  "momentum": "strong",
  "liquidity": "below_lows",
  "volume": "high",
  "confluence": "support",
  "liquidityDetails": {
    "equalHighs": false,
    "equalLows": true,
    "liquiditySweeps": false,
    "stopHunts": false
  },
  "confidence": 80,
  "entry_zone": "4240-4260",
  "invalidation": "4180",
  "target_1": "4320",
  "target_2": "4380",
  "reason": "PHASE 1: Detected ETHUSDT on Binance 15m chart at 4250. PHASE 2: Clear higher highs and higher lows over last 12 candles. PHASE 3: HH_HL bullish structure. HARD RULE: HH+HL → SHORT forbidden. PHASE 5: Price in uptrend with strong momentum. Support at 4200 holding. Signal: LONG.",
  "observedTrend": "Bullish — higher swing lows at 4200, 4230, higher swing highs at 4300, 4350",
  "observedStructure": "Higher low at 4200 on candle 1, higher high at 4300 on candle 4, higher low at 4230 on candle 7, higher high at 4350 on candle 10",
  "observedMomentum": "Strong — bullish candles with higher closes, volume increasing on breakouts",
  "observedSupport": "4200 (previous resistance turned support), 4230 (most recent swing low)",
  "observedResistance": "4350 (current swing high), 4400 (psychological level)"
}

Rules recap:
- quality: "READABLE" or "UNREADABLE_CHART". UNREADABLE if chart is too blurry/cropped/dark to see anything.
- ocrConfidence: 0-100. Your confidence in reading symbol, timeframe, price, and exchange labels.
- trend: "bullish", "bearish", or "neutral"
- marketStructure: "HH_HL", "LH_LL", "HH_LL", "LH_HL", "ranging", or "unclear"
- momentum: "strong", "moderate", or "weak"
- liquidity: "above_highs", "below_lows", "both", or "none"
- volume: "high", "medium", or "low"
- confluence: "support", "resistance", "breakout", "rejection", or "none"
- liquidityDetails: only set to true if clearly visible. Never invent sweeps/hunts.
- confidence: 0-100. 80+ only if structure is crystal clear.

For unreadable charts, return:
{"quality": "UNREADABLE_CHART", "detectedSymbol": "", "detectedTimeframe": "", "detectedExchange": "", "detectedCurrentPrice": "", "detectedIndicatorNames": "", "isHigherHighs": false, "isHigherLows": false, "isLowerHighs": false, "isLowerLows": false, "ocrConfidence": 0, "trend": "neutral", "marketStructure": "unclear", "momentum": "weak", "liquidity": "none", "volume": "medium", "confluence": "none", "liquidityDetails": {"equalHighs": false, "equalLows": false, "liquiditySweeps": false, "stopHunts": false}, "confidence": 0, "entry_zone": "", "invalidation": "", "target_1": "", "target_2": "", "reason": "Cannot read chart", "observedTrend": "", "observedStructure": "", "observedMomentum": "", "observedSupport": "", "observedResistance": ""}

Respond with ONLY the JSON object."""  # noqa: E501
