export interface ScoringDetail {
  marketStructure: number
  liquidity: number
  momentum: number
  trend: number
  volume: number
  confluence: number
  bullScore: number
  bearScore: number
  overall: number
}

export interface ScoredTrade {
  signal: string
  confidence: number
  bullScore: number
  bearScore: number
  entry_zone: string
  stop_loss: string
  take_profit_1: string
  take_profit_2: string
  risk_reward: string
  scoring: ScoringDetail
}

export interface VisionObservation {
  quality: string
  trend: string
  marketStructure: string
  momentum: string
  liquidity: string
  volume: string
  confidence: number
  entry_zone: string
  invalidation: string
  target_1: string
  target_2: string
}

export interface VisionAnalysisResponse {
  success: boolean
  data: null
  trade: ScoredTrade | null
  observation: VisionObservation | null
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

// Legacy — kept for backward compat
export type ChartAnalysisResult = ScoredTrade
