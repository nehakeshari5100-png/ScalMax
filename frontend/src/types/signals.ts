export type SignalType = 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell'
export type SignalLifecycleStatus = 'active' | 'triggered' | 'completed' | 'cancelled' | 'expired'
export type ValidationStatus = 'pending' | 'validated' | 'rejected'

export interface SignalRecord {
  id: string
  symbol: string
  timeframe: string
  exchange: string
  signal_type: SignalType
  direction: string
  entry: number | null
  stop_loss: number | null
  take_profit_1: number | null
  take_profit_2: number | null
  risk_reward_1: number | null
  risk_reward_2: number | null
  confidence: number
  confluence_score: number
  reasoning: string
  reasons: string[]
  risks: string[]
  status: SignalLifecycleStatus
  validation_status: ValidationStatus
  strategy_version: string
  session: string
  created_at: number
  updated_at: number
  triggered_at: number | null
  completed_at: number | null
  pnl: number | null
  pnl_pct: number | null
  outcome: string | null
}

export interface SignalCreateRequest {
  symbol: string
  timeframe?: string
  exchange?: string
  direction: string
  entry?: number | null
  stop_loss?: number | null
  take_profit_1?: number | null
  take_profit_2?: number | null
  confidence: number
  confluence_score?: number
  reasoning?: string
  reasons?: string[]
  risks?: string[]
  strategy_version?: string
  session?: string
}

export interface SignalUpdateRequest {
  status?: SignalLifecycleStatus | null
  validation_status?: ValidationStatus | null
  pnl?: number | null
  pnl_pct?: number | null
  outcome?: string | null
}

export interface SignalListResponse {
  success: boolean
  data: SignalRecord[]
  total: number
  page: number
  page_size: number
  error: string | null
}

export interface SignalResponse {
  success: boolean
  data: SignalRecord | null
  error: string | null
}

export interface SignalPerformance {
  total_signals: number
  active: number
  completed: number
  cancelled: number
  expired: number
  triggered: number
  wins: number
  losses: number
  breakeven: number
  win_rate: number
  total_pnl: number
  avg_pnl: number
  avg_confidence: number
  by_type: Record<string, number>
  by_symbol: Record<string, number>
}

export interface SignalPerformanceResponse {
  success: boolean
  data: SignalPerformance | null
  error: string | null
}
