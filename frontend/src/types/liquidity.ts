// TypeScript types for Liquidity Engine

export interface LiquidityLevel {
  price: number
  strength: number // 1-10
  touches: number
  type: 'support' | 'resistance'
  direction: 'buy' | 'sell'
}

export interface EqualHighLow {
  price: number
  count: number
  strength: number // 1-10
  type: 'equal_high' | 'equal_low'
  timestamps: number[]
}

export interface FVG {
  direction: 'bullish' | 'bearish'
  gap_high: number
  gap_low: number
  gap_size: number
  start_index: number
  end_index: number
  strength: number // 1-10
  mitigated: boolean
  mitigation_price: number | null
}

export interface OrderBlock {
  direction: 'bullish' | 'bearish'
  start_price: number
  end_price: number
  start_index: number
  strength: number // 1-10
  mitigated: boolean
  mitigation_index: number | null
  type: 'order_block' | 'breaker'
}

export interface LiquiditySweep {
  direction: 'buy' | 'sell'
  price: number
  wick_size: number
  volume_ratio: number
  reversal_strength: number // 1-10
  timestamp: number
  type: 'sweep' | 'stop_hunt'
}

export interface Imbalance {
  direction: 'bullish' | 'bearish'
  high: number
  low: number
  size: number
  strength: number // 1-10
}

export interface LiquidityMap {
  symbol: string
  timeframe: string
  timestamp: number
  bullish_liquidity: LiquidityLevel[]
  bearish_liquidity: LiquidityLevel[]
  equal_highs: EqualHighLow[]
  equal_lows: EqualHighLow[]
  fvg: FVG[]
  order_blocks: OrderBlock[]
  breaker_blocks: OrderBlock[]
  liquidity_sweeps: LiquiditySweep[]
  imbalances: Imbalance[]
  overall_confidence: number // 0-100
  bullish_volume: number
  bearish_volume: number
}

export interface LiquidityRequest {
  symbol: string
  timeframe: string
  exchange?: string
  lookback?: number
}

export interface LiquidityResponse {
  success: boolean
  data: LiquidityMap | null
  error: string | null
  cached: boolean
}
