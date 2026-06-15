export interface ChartAnalysisResult {
  direction: string
  confidence: number
  entry_zone: string
  invalidation: string
  target_1: string
  target_2: string
  risk_reward: string
  reasons: string[]
  warnings: string[]
  trend: string
  marketStructure: string
  liquidity: string
  fvg: string
  orderBlocks: string
  bos: string
  choch: string
  rsi: string
  ema: string
  trendStrength: string
  entryIdeas: string[]
  riskZones: string[]
}

export interface VisionAnalysisResponse {
  success: boolean
  data: ChartAnalysisResult | null
  raw: string | null
  model: string
  error: string | null
}

export interface VisionModel {
  id: string
  name: string
  description: string
  default: boolean
}

export interface VisionModelsResponse {
  models: VisionModel[]
}
