// TypeScript types for Confidence Calibration Engine

export type TradeOutcome = 'win' | 'loss' | 'break_even'

export type BucketLabel =
  | '90-100'
  | '80-89'
  | '70-79'
  | '60-69'
  | 'below_60'

export interface BucketStats {
  label: string
  min_score: number
  max_score: number
  trade_count: number
  wins: number
  losses: number
  break_even: number
  win_rate: number
  loss_rate: number
  total_return: number
  total_fees: number
  avg_return: number
  profit_factor: number
  expected_return: number
  adjusted_win_rate: number
  adjusted_confidence: number
}

export interface TradeRecord {
  trade_id: string
  symbol: string
  raw_score: number
  outcome: TradeOutcome
  profit_loss: number
  fees: number
  timestamp: number
  direction: string
  bucket: string
}

export interface CalibrationData {
  buckets: BucketStats[]
  total_trades: number
  overall_win_rate: number
  last_updated: number
  min_samples_required: number
}

export interface CalibrationResult {
  raw_score: number
  calibrated_score: number
  bucket_label: string
  bucket_win_rate: number
  sample_size: number
  has_sufficient_data: boolean
  calibrated_confidence: number
}

export interface CalibrateRequest {
  scores: number[]
}

export interface RecordTradeRequest {
  symbol: string
  raw_score: number
  outcome: TradeOutcome
  profit_loss?: number
  fees?: number
  direction?: string
}

export interface CalibrateResponse {
  success: boolean
  data: CalibrationResult[] | null
  error: string | null
}

export interface CalibrationStatsResponse {
  success: boolean
  data: CalibrationData | null
  error: string | null
}
