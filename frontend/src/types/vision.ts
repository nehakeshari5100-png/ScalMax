export interface ChartDetection {
  exchange: string
  symbol: string
  timeframe: string
  currentPrice: string
  sessionType: string
  chartType: string
  exchangeConfidence: number
  symbolConfidence: number
  timeframeConfidence: number
  priceConfidence: number
}

export interface MarketStructure {
  higherHighs: boolean
  higherLows: boolean
  lowerHighs: boolean
  lowerLows: boolean
  classification: string
  swingHighs: string
  swingLows: string
}

export interface LiquidityAnalysis {
  buySideLiquidity: string
  sellSideLiquidity: string
  equalHighs: boolean
  equalLows: boolean
  stopClusters: string
  liquidityPools: string
  internalLiquidity: string
  externalLiquidity: string
  swept: boolean
  sweepType: string
}

export interface SMCData {
  bos: string
  choch: string
  mss: string
  bosConfidence: number
  chochConfidence: number
  mssConfidence: number
}

export interface FVG {
  type: string
  top: string
  midpoint: string
  bottom: string
  status: string
  strength: number
}

export interface OrderBlock {
  type: string
  zone: string
  status: string
}

export interface PremiumDiscount {
  dealingRange: string
  equilibrium: string
  premiumZone: string
  discountZone: string
  currentPosition: string
}

export interface VolumeAnalysis {
  spikes: string
  absorption: string
  exhaustion: string
  breakoutVolume: string
  weakVolume: string
  climaxVolume: string
}

export interface MomentumAnalysis {
  impulsive: string
  corrective: string
  consolidation: string
  compression: string
  score: number
}

export interface TradePlan {
  bias: string
  confidence: number
  entry: string
  stop: string
  tp1: string
  tp2: string
  tp3: string
  riskReward: string
  probabilityScore: string
  reasoning: string[]
}

export interface ScoringBreakdown {
  marketStructure: number
  liquidity: number
  fvg: number
  orderBlocks: number
  volume: number
  momentum: number
  total: number
}

export interface MarketExtraction {
  chartDetection: ChartDetection
  marketStructure: MarketStructure
  liquidity: LiquidityAnalysis
  smc: SMCData
  fvgs: FVG[]
  orderBlocks: OrderBlock[]
  premiumDiscount: PremiumDiscount
  volume: VolumeAnalysis
  momentum: MomentumAnalysis
  trade: TradePlan
  scoring: ScoringBreakdown
}

export interface VisionAnalysisResponse {
  success: boolean
  extraction: MarketExtraction | null
  raw: string | null
  model: string
  error: string | null
}
