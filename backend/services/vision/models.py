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


class ConfidenceScores(BaseModel):
    structure: int = 0
    liquidity: int = 0
    smc: int = 0
    volume: int = 0
    momentum: int = 0
    rr: int = 0
    total: int = 0


class ConflictReport(BaseModel):
    bullishFactors: List[str] = Field(default_factory=list)
    bearishFactors: List[str] = Field(default_factory=list)
    highConflict: bool = False


class LiquidityTarget(BaseModel):
    nearest: str = ""
    major: str = ""
    final: str = ""


class ExecutionPlan(BaseModel):
    entryTrigger: str = ""
    invalidation: str = ""
    targetLogic: str = ""


class InstitutionalDecision(BaseModel):
    marketState: str = ""
    bias: str = "NO_TRADE"
    tradeGrade: str = ""
    confidence: ConfidenceScores = Field(default_factory=ConfidenceScores)
    tradePlan: TradePlan = Field(default_factory=TradePlan)
    riskReward: str = ""
    probabilityScore: str = ""
    conflictReport: ConflictReport = Field(default_factory=ConflictReport)
    liquidityTarget: LiquidityTarget = Field(default_factory=LiquidityTarget)
    executionPlan: ExecutionPlan = Field(default_factory=ExecutionPlan)
    reasoning: List[str] = Field(default_factory=list)


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
    institutionalDecision: Optional[InstitutionalDecision] = None


class VisionAnalysisResponse(BaseModel):
    success: bool
    extraction: Optional[MarketExtraction] = None
    validation: Optional[ValidationReport] = None
    raw: Optional[str] = None
    model: str = ""
    error: Optional[str] = None
    detail: Optional[dict] = None
    engine: str = "institutional"


INSTITUTIONAL_PROMPT = """You are an institutional-grade scalper. Do not predict. React to evidence. Follow these 10 steps in strict order.

STEP 1 — MARKET STATE
Determine market state. Choose exactly one:
- TRENDING: price making clear HH+HL or LH+LL
- RANGING: price oscillating between clear levels, no direction
- BREAKOUT: price breaking a key level with conviction
- RETEST: price returning to a broken level to confirm
- LIQUIDITY_SWEEP: price swept a stop cluster then reversed
- REVERSAL: clear shift in structure character

STEP 2 — DIRECTIONAL BIAS
Choose exactly one:
- STRONG_LONG: multiple confluent bullish factors
- LONG: bullish bias with minor conflicting signals
- NEUTRAL: no clear directional edge
- SHORT: bearish bias with minor conflicting signals
- STRONG_SHORT: multiple confluent bearish factors
HARD RULE: If market state is RANGING, bias MUST be NEUTRAL.

STEP 3 — TRADE PLAN
Only if bias is LONG, STRONG_LONG, SHORT, or STRONG_SHORT:
- entry: Specific entry price or zone
- stop: Stop loss price (must be below entry for LONG, above for SHORT)
- tp1: First take profit (minimum 1:2 risk-reward)
- tp2: Second take profit
- tp3: Third take profit

STEP 4 — RISK METRICS
- riskReward: Risk-to-reward ratio (e.g. "1:2.5")
- probabilityScore: Estimated probability of success 0-100

STEP 5 — TRADE QUALITY GRADE
Grade the trade:
- A+: all 7 validation layers pass, RR >= 1:3, confidence >= 85
- A: 6+ layers pass, RR >= 1:2, confidence >= 75
- B: 5+ layers pass, RR >= 1:2, confidence >= 65
- C: 4+ layers pass, RR >= 1:1.5
- D: weak evidence, reject this trade
HARD RULE: If grade is D, the final decision MUST be NO_TRADE.

STEP 6 — CONFLICT DETECTION
List all bullish factors and all bearish factors visible on the chart.
If the number of bullish factors and bearish factors are within 1 of each other, set highConflict to true.
If highConflict is true, bias MUST be NEUTRAL.

STEP 7 — LIQUIDITY TARGETS
- nearest: Closest liquidity pool to current price
- major: The most significant liquidity zone
- final: The ultimate liquidity target that would complete the move

STEP 8 — EXECUTION PLAN
If bias is LONG or STRONG_LONG:
- entryTrigger: What specific price action confirms entry
- invalidation: Exact level that invalidates the trade
- targetLogic: Why each TP level was chosen
If bias is SHORT or STRONG_SHORT:
- entryTrigger: What specific price action confirms entry
- invalidation: Exact level that invalidates the trade
- targetLogic: Why each TP level was chosen
If NEUTRAL: explain why no trade.

STEP 9 — FINAL DECISION
Return exactly one: "LONG", "SHORT", or "NO_TRADE"
NEVER return STRONG_LONG or STRONG_SHORT here. Use the bias field for direction strength.
NO_TRADE if: confidence < 70, grade is D, highConflict is true, or bias is NEUTRAL.

STEP 10 — CONFIDENCE ENGINE
Score each component 0-100. Total is weighted average:
- structure: 25% weight — market state clarity and trend alignment with bias
- liquidity: 20% weight — liquidity target identification and sweep status
- smc: 20% weight — BOS/CHOCH/MSS confirmation strength
- volume: 15% weight — volume confirmation on key moves
- momentum: 10% weight — momentum strength and impulse quality
- rr: 10% weight — risk-reward ratio quality

Return ONLY valid JSON. No markdown fences. Exact structure:

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
  "institutionalDecision": {
    "marketState": "TRENDING",
    "bias": "STRONG_LONG",
    "tradeGrade": "A",
    "confidence": {
      "structure": 85,
      "liquidity": 75,
      "smc": 80,
      "volume": 70,
      "momentum": 65,
      "rr": 80
    },
    "tradePlan": {
      "bias": "LONG",
      "confidence": 78,
      "entry": "4260-4280",
      "stop": "4180",
      "tp1": "4350",
      "tp2": "4400",
      "tp3": "4450",
      "riskReward": "1:2.5",
      "probabilityScore": "72",
      "reasoning": []
    },
    "riskReward": "1:2.5",
    "probabilityScore": "72",
    "conflictReport": {
      "bullishFactors": ["HH+HL structure", "Price in discount zone", "Unmitigated bullish OB", "Bullish FVG at 4260-4280", "High volume on breakout"],
      "bearishFactors": ["Resistance at 4400"],
      "highConflict": false
    },
    "liquidityTarget": {
      "nearest": "Buy-side above 4400",
      "major": "Weekly high at 4500",
      "final": "4500+ zone"
    },
    "executionPlan": {
      "entryTrigger": "Reaction at 4260-4280 with bullish confirmation candle",
      "invalidation": "Close below 4180",
      "targetLogic": "TP1 at 4350 (recent high), TP2 at 4400 (liquidity grab), TP3 at 4450 (extension)"
    },
    "reasoning": [
      "Bullish structure with clear HH+HL pattern over 12 candles",
      "Price in discount zone at 4260-4280 with equilibrium at 4300",
      "Unmitigated bullish order block at 4240-4260 providing support",
      "Untouched bullish FVG at 4260-4280 acting as magnet for price",
      "High volume breakout above 4350 confirms bullish momentum"
    ]
  }
}
"""  # noqa: E501
