// TypeScript types for Confluence Scoring Engine

export type ConfluenceGrade =
  | 'Elite Setup'
  | 'High Probability'
  | 'Tradable'
  | 'No Trade'

export type ConfluenceDirection = 'bullish' | 'bearish' | 'neutral'

export interface MarketStructureInput {
  trend_direction: ConfluenceDirection
  swing_highs: number
  swing_lows: number
  higher_highs: boolean
  higher_lows: boolean
  lower_highs: boolean
  lower_lows: boolean
  market_regime: 'trending' | 'ranging' | 'volatile'
  structure_score: number
}

export interface ConfluenceInput {
  symbol: string
  timeframe: string
  trend_score: number
  momentum_score: number
  volume_score: number
  volatility_score: number
  rsi: number | null
  macd_histogram: number | null
  ema9: number | null
  ema20: number | null
  ema50: number | null
  price: number | null
  atr_percent: number | null
  volume_spike_ratio: number | null
  market_structure: MarketStructureInput
  liquidity_confidence: number
  fvg_count: number
  order_block_count: number
  breaker_block_count: number
  sweep_count: number
  equal_high_count: number
  equal_low_count: number
  bullish_liquidity_pools: number
  bearish_liquidity_pools: number
}

export interface CategoryScore {
  name: string
  weight: number
  raw_score: number
  weighted_score: number
  reason: string
}

export interface ConfluenceOutput {
  score: number
  grade: ConfluenceGrade
  direction: ConfluenceDirection
  reasons: string[]
  risks: string[]
  category_scores: CategoryScore[]
}

export interface ScoreRequest {
  symbol: string
  timeframe: string
  exchange?: string
  data: ConfluenceInput
}

export interface ScoreResponse {
  success: boolean
  data: ConfluenceOutput | null
  error: string | null
  cached: boolean
}
