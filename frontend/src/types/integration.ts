import type { DecisionLevel, DecisionOutput } from './decision'
import type { SignalRecord } from './signals'

export type PipelineStage =
  | 'fetch_candles'
  | 'calculate_indicators'
  | 'detect_liquidity'
  | 'analyze_structure'
  | 'score_confluence'
  | 'analyze_vision'
  | 'make_decision'
  | 'generate_signal'

export interface PipelineStageResult {
  stage: PipelineStage
  status: string
  duration_ms: number
  data: Record<string, unknown> | null
  error: string | null
}

export interface PipelineRequest {
  symbol?: string
  timeframe?: string
  exchange?: string
  lookback?: number
  include_vision?: boolean
  vision_model?: string
  api_key?: string | null
  chart_image_base64?: string | null
  auto_generate_signal?: boolean
}

export interface PipelineResponse {
  success: boolean
  execution_id: string
  total_duration_ms: number
  stages: PipelineStageResult[]
  symbol: string
  timeframe: string
  exchange: string
  decision: DecisionOutput | null
  signal: SignalRecord | null
  error: string | null
}
