from pydantic import BaseModel, Field
from typing import List, Optional


class ChartDetection(BaseModel):
    exchange: str = ""
    symbol: str = ""
    timeframe: str = ""
    currentPrice: str = ""
    sessionType: str = ""
    chartType: str = "candlestick"
    exchangeConfidence: int = 0
    symbolConfidence: int = 0
    timeframeConfidence: int = 0
    priceConfidence: int = 0


class MarketStructure(BaseModel):
    higherHighs: bool = False
    higherLows: bool = False
    lowerHighs: bool = False
    lowerLows: bool = False
    classification: str = "range"
    swingHighs: str = ""
    swingLows: str = ""


class LiquidityAnalysis(BaseModel):
    buySideLiquidity: str = ""
    sellSideLiquidity: str = ""
    equalHighs: bool = False
    equalLows: bool = False
    stopClusters: str = ""
    liquidityPools: str = ""
    internalLiquidity: str = ""
    externalLiquidity: str = ""
    swept: bool = False
    sweepType: str = "none"


class SMCData(BaseModel):
    bos: str = ""
    choch: str = ""
    mss: str = ""
    bosConfidence: int = 0
    chochConfidence: int = 0
    mssConfidence: int = 0


class FVG(BaseModel):
    type: str = ""
    top: str = ""
    midpoint: str = ""
    bottom: str = ""
    status: str = "untouched"
    strength: int = 0


class OrderBlock(BaseModel):
    type: str = ""
    zone: str = ""
    status: str = "unmitigated"


class PremiumDiscount(BaseModel):
    dealingRange: str = ""
    equilibrium: str = ""
    premiumZone: str = ""
    discountZone: str = ""
    currentPosition: str = "equilibrium"


class VolumeAnalysis(BaseModel):
    spikes: str = ""
    absorption: str = ""
    exhaustion: str = ""
    breakoutVolume: str = ""
    weakVolume: str = ""
    climaxVolume: str = ""


class MomentumAnalysis(BaseModel):
    impulsive: str = ""
    corrective: str = ""
    consolidation: str = ""
    compression: str = ""
    score: int = 0


class TradePlan(BaseModel):
    bias: str = "NO_TRADE"
    confidence: int = 0
    entry: str = ""
    stop: str = ""
    tp1: str = ""
    tp2: str = ""
    tp3: str = ""
    riskReward: str = ""
    probabilityScore: str = ""
    reasoning: List[str] = Field(default_factory=list)


class ScoringBreakdown(BaseModel):
    marketStructure: int = 0
    liquidity: int = 0
    fvg: int = 0
    orderBlocks: int = 0
    volume: int = 0
    momentum: int = 0
    total: int = 0


class MarketExtraction(BaseModel):
    chartDetection: ChartDetection = Field(default_factory=ChartDetection)
    marketStructure: MarketStructure = Field(default_factory=MarketStructure)
    liquidity: LiquidityAnalysis = Field(default_factory=LiquidityAnalysis)
    smc: SMCData = Field(default_factory=SMCData)
    fvgs: List[FVG] = Field(default_factory=list)
    orderBlocks: List[OrderBlock] = Field(default_factory=list)
    premiumDiscount: PremiumDiscount = Field(default_factory=PremiumDiscount)
    volume: VolumeAnalysis = Field(default_factory=VolumeAnalysis)
    momentum: MomentumAnalysis = Field(default_factory=MomentumAnalysis)
    trade: TradePlan = Field(default_factory=TradePlan)
    scoring: ScoringBreakdown = Field(default_factory=ScoringBreakdown)


class ValidationLayer(BaseModel):
    name: str
    passed: bool
    score: int
    maxScore: int
    details: str = ""


class ValidationReport(BaseModel):
    layers: List[ValidationLayer]
    passedLayers: List[str]
    failedLayers: List[str]
    finalScore: int
    signalStrength: str


class VisionAnalysisResponse(BaseModel):
    success: bool
    extraction: Optional[MarketExtraction] = None
    validation: Optional[ValidationReport] = None
    raw: Optional[str] = None
    model: str = ""
    error: Optional[str] = None


MASTER_PROMPT = """You are a professional scalping chart analyst. Follow these 12 steps in order. Never skip steps. Never generate a trade before completing all extraction steps.

STEP 1 — CHART DETECTION
Identify from the chart image:
- exchange: Exchange name if visible (e.g. Binance, Bybit, TradingView). "" if not visible.
- symbol: Trading pair or stock symbol (e.g. ETHUSDT, BTCUSD, AAPL). Look at top-left/right labels.
- timeframe: Timeframe shown (e.g. 1m, 5m, 15m, 30m, 1h, 4h, 1D).
- currentPrice: Most recent visible price. Be precise.
- sessionType: "asia", "london", "new_york", "overlap", or "" if unclear.
- chartType: "candlestick", "heikin_ashi", "line", "bar", or "renko".
For each detection, return confidence 0-100.

STEP 2 — MARKET STRUCTURE
Examine 3+ recent swing points. Determine:
- higherHighs: Are swing highs getting clearly higher? true/false
- higherLows: Are swing lows getting clearly higher? true/false
- lowerHighs: Are swing highs getting clearly lower? true/false
- lowerLows: Are swing lows getting clearly lower? true/false
- classification: "bullish_trend" (HH+HL), "bearish_trend" (LH+LL), "range" (no clear direction), "compression" (tightening), "expansion" (widening), "reversal_candidate" (possible trend change)
- swingHighs: List specific swing high prices
- swingLows: List specific swing low prices

STEP 3 — LIQUIDITY ANALYSIS
- buySideLiquidity: Where is buy-side liquidity? (above highs, specific price levels)
- sellSideLiquidity: Where is sell-side liquidity? (below lows, specific price levels)
- equalHighs: Are there two+ swing highs at the same price?
- equalLows: Are there two+ swing lows at the same price?
- stopClusters: Where are stop loss clusters likely?
- liquidityPools: Where are major liquidity pools?
- internalLiquidity: Liquidity within the range?
- externalLiquidity: Liquidity outside the range?
- swept: Has major liquidity already been swept? true/false
- sweepType: "bullish" (swept below lows then reversed), "bearish" (swept above highs then reversed), "none"

STEP 4 — SMART MONEY CONCEPTS
- bos: Break of Structure — describe the exact candle/level where structure broke
- choch: Change of Character — describe where trend character changed
- mss: Market Structure Shift — describe the shift point
- bosConfidence: 0-100
- chochConfidence: 0-100
- mssConfidence: 0-100

STEP 5 — FAIR VALUE GAPS
For each visible FVG, return:
- type: "bullish" or "bearish"
- top: Top price of the gap
- midpoint: Midpoint price
- bottom: Bottom price
- status: "filled", "partially_filled", or "untouched"
- strength: 0-100
Rank by strength (strongest first).

STEP 6 — ORDER BLOCKS
For each visible order block, return:
- type: "bullish" or "bearish"
- zone: Price zone of the order block
- status: "mitigated", "unmitigated", "fresh", or "invalidated"

STEP 7 — PREMIUM / DISCOUNT
- dealingRange: Current price range (low-high)
- equilibrium: Midpoint of the range (50% retracement)
- premiumZone: Upper half of the range (50-100%)
- discountZone: Lower half of the range (0-50%)
- currentPosition: "premium" (price in upper half), "equilibrium" (at midpoint), "discount" (in lower half)

STEP 8 — VOLUME ANALYSIS
- spikes: Describe any volume spikes and their location
- absorption: Is price absorbing at a level?
- exhaustion: Signs of volume exhaustion?
- breakoutVolume: Volume on breakouts — high or low?
- weakVolume: Areas of weak volume?
- climaxVolume: Climax volume patterns?

STEP 9 — MOMENTUM ANALYSIS
- impulsive: Describe impulsive moves and direction
- corrective: Describe corrective/retrace moves
- consolidation: Describe consolidation zones
- compression: Is price compressing (tightening range)?
- score: 0-100 momentum strength score

STEP 10 — TRADE FILTER
DO NOT FORCE A TRADE.
Return bias: "LONG", "SHORT", or "NO_TRADE"
NO_TRADE if: confidence < 70, structure unclear, liquidity target unclear, or risk reward below 1:2.

STEP 11 — TRADE PLAN
Only if bias is LONG or SHORT AND confidence >= 70:
- entry: Specific entry price or zone
- stop: Stop loss price
- tp1: First take profit
- tp2: Second take profit
- tp3: Third take profit
- riskReward: Risk-to-reward ratio (e.g. "1:2.5")
- probabilityScore: Probability of success 0-100

STEP 12 — FINAL SCORING
Calculate weighted confidence:
- marketStructure: 25% weight — clarity of HH/HL/LH/LL and classification
- liquidity: 20% weight — clarity of liquidity targets and sweep status
- fvg: 15% weight — presence and strength of FVGs
- orderBlocks: 15% weight — presence and freshness of order blocks
- volume: 15% weight — volume confirmation
- momentum: 10% weight — momentum strength
Each component score 0-100. total = weighted average.
Return total as the final confidence.

REASONING:
Provide maximum 5 concise bullet points explaining the analysis. Focus on the key evidence for the bias.

HARD RULES:
- Never force LONG or SHORT. If unclear, return NO_TRADE.
- Never set bias if structure is ranging.
- Never set bias if confidence < 70.
- HH+HL = bullish. LH+LL = bearish. Mixed = range or NO_TRADE.
- If liquidity targets are unclear, NO_TRADE.
- If risk reward < 1:2, NO_TRADE.

Return ONLY valid JSON. No markdown fences. The JSON must have this exact structure:

{
  "chartDetection": {
    "exchange": "Binance",
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "currentPrice": "4250.00",
    "sessionType": "london",
    "chartType": "candlestick",
    "exchangeConfidence": 85,
    "symbolConfidence": 95,
    "timeframeConfidence": 95,
    "priceConfidence": 90
  },
  "marketStructure": {
    "higherHighs": true,
    "higherLows": true,
    "lowerHighs": false,
    "lowerLows": false,
    "classification": "bullish_trend",
    "swingHighs": "4300, 4350, 4400",
    "swingLows": "4200, 4250, 4280"
  },
  "liquidity": {
    "buySideLiquidity": "Above 4400 (recent high)",
    "sellSideLiquidity": "Below 4200 (recent low)",
    "equalHighs": false,
    "equalLows": false,
    "stopClusters": "Above 4400 (short stops), below 4200 (long stops)",
    "liquidityPools": "4400 resistance zone, 4200 support zone",
    "internalLiquidity": "4250-4350 range liquidity",
    "externalLiquidity": "4400+ and 4180-",
    "swept": false,
    "sweepType": "none"
  },
  "smc": {
    "bos": "Break above 4350 on high volume",
    "choch": "Shift from bearish to bullish at 4200 low",
    "mss": "Market structure shifted bullish at 4350 break",
    "bosConfidence": 85,
    "chochConfidence": 80,
    "mssConfidence": 80
  },
  "fvgs": [
    {"type": "bullish", "top": "4280", "midpoint": "4270", "bottom": "4260", "status": "untouched", "strength": 75},
    {"type": "bullish", "top": "4220", "midpoint": "4210", "bottom": "4200", "status": "filled", "strength": 60}
  ],
  "orderBlocks": [
    {"type": "bullish", "zone": "4240-4260", "status": "unmitigated"},
    {"type": "bearish", "zone": "4350-4370", "status": "unmitigated"}
  ],
  "premiumDiscount": {
    "dealingRange": "4200-4400",
    "equilibrium": "4300",
    "premiumZone": "4300-4400",
    "discountZone": "4200-4300",
    "currentPosition": "discount"
  },
  "volume": {
    "spikes": "Volume spike at 4350 breakout",
    "absorption": "Volume absorbing at 4200 support",
    "exhaustion": "Declining volume on recent highs",
    "breakoutVolume": "High volume on 4350 break",
    "weakVolume": "Low volume in 4250-4300 consolidation",
    "climaxVolume": "No climax pattern detected"
  },
  "momentum": {
    "impulsive": "Bullish impulse from 4200 to 4350",
    "corrective": "Shallow correction to 4280",
    "consolidation": "Price consolidating at 4300-4350",
    "compression": "Range tightening near resistance",
    "score": 75
  },
  "trade": {
    "bias": "LONG",
    "confidence": 78,
    "entry": "4260-4280",
    "stop": "4180",
    "tp1": "4350",
    "tp2": "4400",
    "tp3": "4450",
    "riskReward": "1:2.5",
    "probabilityScore": "70",
    "reasoning": [
      "Bullish structure with clear HH+HL pattern over 12 candles",
      "Price in discount zone at 4260-4280 with equilibrium at 4300",
      "Unmitigated bullish order block at 4240-4260 providing support",
      "Untouched bullish FVG at 4260-4280 acting as magnet for price",
      "High volume breakout above 4350 confirms bullish momentum"
    ]
  },
  "scoring": {
    "marketStructure": 85,
    "liquidity": 75,
    "fvg": 70,
    "orderBlocks": 75,
    "volume": 80,
    "momentum": 75,
    "total": 78
  }
}
"""  # noqa: E501
