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


INSTITUTIONAL_PROMPT = """You are an institutional scalper. React to evidence only. Return ONLY valid JSON. No explanations.

RULES:
- If RANGING → bias=NEUTRAL
- If grade=D → NO_TRADE
- If highConflict → bias=NEUTRAL
- If confidence<70 → NO_TRADE
- Final decision: LONG/SHORT/NO_TRADE only

10 steps: 1) marketState (TRENDING/RANGING/BREAKOUT/RETEST/LIQUIDITY_SWEEP/REVERSAL) 2) bias (STRONG_LONG/LONG/NEUTRAL/SHORT/STRONG_SHORT) 3) tradePlan (entry,stop,tp1,tp2,tp3 only if bias!=NEUTRAL) 4) riskReward+probabilityScore 5) tradeGrade (A+/A/B/C/D) 6) conflictReport (bullishFactors,bearishFactors,highConflict) 7) liquidityTarget (nearest,major,final) 8) executionPlan (entryTrigger,invalidation,targetLogic) 9) finalDecision 10) confidence (structure:25%,liquidity:20%,smc:20%,volume:15%,momentum:10%,rr:10%,total weighted avg)

Return ONLY JSON. No markdown fences. Schema:
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
