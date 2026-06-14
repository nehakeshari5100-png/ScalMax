export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed'
export type TradeDirection = 'long' | 'short'
export type TradeOutcome = 'win' | 'loss' | 'break_even'
export type OrderType = 'market' | 'limit' | 'stop' | 'stop_loss' | 'take_profit'

export interface BacktestConfig {
  symbol: string
  timeframe: string
  start_date: string | null
  end_date: string | null
  initial_capital: number
  position_size_pct: number
  max_open_positions: number
  slippage_pct: number
  fee_pct: number
  risk_per_trade_pct: number
  sl_pct: number | null
  tp_pct: number | null
  use_trailing_sl: boolean
  strategy_version: string
}

export interface BacktestTrade {
  id: number
  direction: TradeDirection
  entry_time: number
  entry_price: number
  exit_time: number
  exit_price: number
  size: number
  quantity: number
  pnl: number
  pnl_pct: number
  fees_paid: number
  r_multiple: number
  sl_price: number | null
  tp_price: number | null
  bars_held: number
  entry_reason: string
  exit_reason: string
  outcome: TradeOutcome
}

export interface EquityPoint {
  timestamp: number
  equity: number
  drawdown: number
  drawdown_pct: number
}

export interface MonthlyPerformance {
  year: number
  month: number
  trades: number
  wins: number
  losses: number
  net_pnl: number
  win_rate: number
  profit_factor: number
  avg_trade: number
}

export interface BacktestMetrics {
  total_trades: number
  wins: number
  losses: number
  break_even: number
  win_rate: number
  loss_rate: number
  avg_r_multiple: number
  avg_win_r: number
  avg_loss_r: number
  profit_factor: number
  gross_profit: number
  gross_loss: number
  net_profit: number
  net_profit_pct: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  max_drawdown_pct: number
  avg_trade_duration_bars: number
  avg_trade_duration_seconds: number
  expectancy: number
  expectancy_percent: number
  avg_win_pct: number
  avg_loss_pct: number
  largest_win: number
  largest_loss: number
  largest_win_pct: number
  largest_loss_pct: number
  avg_volume: number
  total_fees: number
  final_equity: number
  return_pct: number
}

export interface BacktestResult {
  id: string | null
  config: BacktestConfig
  status: BacktestStatus
  metrics: BacktestMetrics
  trades: BacktestTrade[]
  equity_curve: EquityPoint[]
  monthly: MonthlyPerformance[]
  signals_generated: number
  candles_processed: number
  start_time: number
  end_time: number
  duration_ms: number
  error: string | null
  report_path: string | null
}

export interface BacktestRunRequest {
  symbol: string
  timeframe: string
  start_date?: string | null
  end_date?: string | null
  initial_capital?: number
  position_size_pct?: number
  max_open_positions?: number
  slippage_pct?: number
  fee_pct?: number
  risk_per_trade_pct?: number
  sl_pct?: number | null
  tp_pct?: number | null
  use_trailing_sl?: boolean
  strategy_version?: string
}

export interface BacktestRunResponse {
  success: boolean
  data: BacktestResult | null
  error: string | null
}

export interface BacktestListResponse {
  success: boolean
  data: BacktestResult[]
  total: number
  error: string | null
}

export interface SupportedOptions {
  assets: string[]
  timeframes: string[]
}
