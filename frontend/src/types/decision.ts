export type DecisionDirection = 'long' | 'short' | 'neutral' | 'no_trade'

export interface VisionInterpretation {
  trend: string
  market_structure: string
  liquidity: string
  support_zones: string[]
  resistance_zones: string[]
  entry_ideas: string[]
  risk_zones: string[]
  confidence: number
  source: string
}

export interface DeterministicAssessment {
  direction: string
  confidence: number
  confluence_score: number
  confluence_grade: string
  trend_score: number
  momentum_score: number
  volume_score: number
  volatility_score: number
  liquidity_confidence: number
  market_structure_score: number
  reasons: string[]
  risks: string[]
  source: string
}

export interface DecisionLevel {
  entry: number | null
  stop_loss: number | null
  take_profit_1: number | null
  take_profit_2: number | null
  risk_reward_1: number | null
  risk_reward_2: number | null
}

export interface DecisionOutput {
  direction: DecisionDirection
  confidence: number
  levels: DecisionLevel
  reasoning: string
  reasons: string[]
  risks: string[]
  deterministic: DeterministicAssessment | null
  vision: VisionInterpretation | null
  conflict: string | null
  is_tradeable: boolean
}

export interface DecisionInput {
  symbol: string
  timeframe?: string
  exchange?: string
  price?: number | null
  include_vision?: boolean
  vision_analysis?: VisionInterpretation | null
  api_key?: string | null
  vision_model?: string
}

export interface DecisionResponse {
  success: boolean
  data: DecisionOutput | null
  error: string | null
}
