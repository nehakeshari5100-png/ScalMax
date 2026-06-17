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


INSTITUTIONAL_PROMPT = """You are an institutional scalper. Return ONLY valid JSON. No markdown. No chain of thought. No explanations.

Rules:
- If ranging -> bias=NEUTRAL
- If grade=D -> NO_TRADE
- If highConflict -> bias=NEUTRAL
- If confidence<70 -> NO_TRADE

Return ONLY this JSON with values based on the chart:
{"chartDetection":{"exchange":"","symbol":"","timeframe":"","currentPrice":"","sessionType":"","chartType":"candlestick","exchangeConfidence":0,"symbolConfidence":0,"timeframeConfidence":0,"priceConfidence":0},"marketStructure":{"higherHighs":false,"higherLows":false,"lowerHighs":false,"lowerLows":false,"classification":"range","swingHighs":"","swingLows":""},"liquidity":{"buySideLiquidity":"","sellSideLiquidity":"","equalHighs":false,"equalLows":false,"stopClusters":"","liquidityPools":"","internalLiquidity":"","externalLiquidity":"","swept":false,"sweepType":"none"},"smc":{"bos":"","choch":"","mss":"","bosConfidence":0,"chochConfidence":0,"mssConfidence":0},"fvgs":[],"orderBlocks":[],"premiumDiscount":{"dealingRange":"","equilibrium":"","premiumZone":"","discountZone":"","currentPosition":"equilibrium"},"volume":{"spikes":"","absorption":"","exhaustion":"","breakoutVolume":"","weakVolume":"","climaxVolume":""},"momentum":{"impulsive":"","corrective":"","consolidation":"","compression":"","score":0},"institutionalDecision":{"marketState":"","bias":"NO_TRADE","tradeGrade":"","riskReward":"","probabilityScore":"","confidence":{"structure":0,"liquidity":0,"smc":0,"volume":0,"momentum":0,"rr":0,"total":0},"tradePlan":{"bias":"NO_TRADE","confidence":0,"entry":"","stop":"","tp1":"","tp2":"","tp3":"","riskReward":"","probabilityScore":"","reasoning":[]},"conflictReport":{"bullishFactors":[],"bearishFactors":[],"highConflict":false},"liquidityTarget":{"nearest":"","major":"","final":""},"executionPlan":{"entryTrigger":"","invalidation":"","targetLogic":""},"reasoning":[]}}
"""  # noqa: E501
