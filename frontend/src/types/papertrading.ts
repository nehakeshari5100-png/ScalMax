export type PositionStatus = 'open' | 'closed' | 'cancelled'
export type PositionDirection = 'long' | 'short'
export type ExitReason = 'tp1' | 'tp2' | 'sl' | 'manual' | 'cancelled'

export interface VirtualAccount {
  id: string
  name: string
  initial_balance: number
  current_balance: number
  created_at: number
  updated_at: number
  total_pnl: number
  total_pnl_pct: number
}

export interface TradeFill {
  id: string
  position_id: string
  fill_type: string
  price: number
  quantity: number
  fee: number
  timestamp: number
}

export interface Position {
  id: string
  account_id: string
  signal_id: string | null
  symbol: string
  timeframe: string
  exchange: string
  direction: PositionDirection
  entry_price: number
  quantity: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number | null
  status: PositionStatus
  opened_at: number
  closed_at: number | null
  close_price: number | null
  pnl: number | null
  pnl_pct: number | null
  exit_reason: ExitReason | null
  fees: number
  risk_amount: number
  risk_pct: number
  rr_ratio: number
  holding_time_hours: number
}

export interface PerformanceStats {
  total_trades: number
  wins: number
  losses: number
  breakeven: number
  win_rate: number
  total_pnl: number
  avg_pnl: number
  profit_factor: number
  max_drawdown: number
  current_drawdown: number
  avg_rr: number
  avg_holding_time_hours: number
  best_trade: number
  worst_trade: number
  sharpe_ratio: number
  daily_pnl: Record<string, number>
  monthly_pnl: Record<string, number>
  by_symbol: Record<string, { trades: number; wins: number; losses: number; pnl: number; win_rate: number }>
}

export interface LeaderboardEntry {
  account_id: string
  account_name: string
  total_pnl: number
  total_pnl_pct: number
  win_rate: number
  profit_factor: number
  total_trades: number
  current_balance: number
}

export interface CreateAccountRequest {
  name?: string
  initial_balance?: number
}

export interface OpenPositionRequest {
  account_id: string
  symbol: string
  timeframe?: string
  exchange?: string
  direction: PositionDirection
  entry_price: number
  quantity: number
  stop_loss: number
  take_profit_1: number
  take_profit_2?: number | null
  signal_id?: string | null
  risk_pct?: number
}

export interface ClosePositionRequest {
  position_id: string
  close_price: number
  exit_reason?: ExitReason
}

export interface AccountResponse {
  success: boolean
  data: VirtualAccount | null
  error: string | null
}

export interface AccountListResponse {
  success: boolean
  data: VirtualAccount[]
  error: string | null
}

export interface PositionResponse {
  success: boolean
  data: Position | null
  error: string | null
}

export interface PositionListResponse {
  success: boolean
  data: Position[]
  total: number
  error: string | null
}

export interface StatsResponse {
  success: boolean
  data: PerformanceStats | null
  error: string | null
}

export interface LeaderboardResponse {
  success: boolean
  data: LeaderboardEntry[]
  error: string | null
}
