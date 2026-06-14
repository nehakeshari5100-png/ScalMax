-- Supabase Migration: Initial Schema
-- Run this in Supabase SQL Editor

-- 1. Backtest Results
CREATE TABLE IF NOT EXISTS backtest_results (
  id TEXT PRIMARY KEY,
  config JSONB NOT NULL DEFAULT '{}',
  result JSONB,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  strategy_version TEXT,
  net_profit REAL DEFAULT 0,
  win_rate REAL DEFAULT 0,
  sharpe_ratio REAL DEFAULT 0,
  max_drawdown_pct REAL DEFAULT 0,
  total_trades INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_results_symbol ON backtest_results(symbol, timeframe);

-- 2. Paper Trading Accounts
CREATE TABLE IF NOT EXISTS accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL DEFAULT 'Default',
  initial_balance REAL NOT NULL DEFAULT 10000,
  current_balance REAL NOT NULL DEFAULT 10000,
  total_pnl REAL DEFAULT 0,
  total_pnl_pct REAL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Paper Trading Positions
CREATE TABLE IF NOT EXISTS positions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  signal_id TEXT,
  symbol TEXT NOT NULL,
  timeframe TEXT,
  exchange TEXT DEFAULT 'binance',
  direction TEXT NOT NULL CHECK (direction IN ('long', 'short')),
  entry_price REAL NOT NULL,
  quantity REAL NOT NULL,
  stop_loss REAL NOT NULL,
  take_profit_1 REAL,
  take_profit_2 REAL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
  opened_at TIMESTAMPTZ DEFAULT NOW(),
  closed_at TIMESTAMPTZ,
  close_price REAL,
  pnl REAL,
  pnl_pct REAL,
  exit_reason TEXT CHECK (exit_reason IN ('tp1', 'tp2', 'sl', 'manual', 'cancelled')),
  fees REAL DEFAULT 0,
  risk_amount REAL DEFAULT 0,
  risk_pct REAL DEFAULT 0,
  rr_ratio REAL DEFAULT 0,
  holding_time_hours REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);

-- 4. Trade Fills
CREATE TABLE IF NOT EXISTS fills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  position_id UUID NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
  fill_type TEXT NOT NULL,
  price REAL NOT NULL,
  quantity REAL NOT NULL,
  fee REAL DEFAULT 0,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fills_position ON fills(position_id);

-- 5. Signals
CREATE TABLE IF NOT EXISTS signals (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  timeframe TEXT,
  exchange TEXT DEFAULT 'binance',
  signal_type TEXT NOT NULL,
  direction TEXT,
  entry REAL,
  stop_loss REAL,
  take_profit_1 REAL,
  take_profit_2 REAL,
  risk_reward_1 REAL,
  risk_reward_2 REAL,
  confidence REAL DEFAULT 0,
  confluence_score REAL DEFAULT 0,
  reasoning TEXT,
  reasons JSONB DEFAULT '[]',
  risks JSONB DEFAULT '[]',
  status TEXT DEFAULT 'active',
  validation_status TEXT DEFAULT 'pending',
  strategy_version TEXT,
  session TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  triggered_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  pnl REAL,
  pnl_pct REAL,
  outcome TEXT
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);

-- 6. Calibration Trades
CREATE TABLE IF NOT EXISTS calibration_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trade_id TEXT,
  symbol TEXT,
  raw_score REAL NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN ('win', 'loss', 'break_even')),
  profit_loss REAL DEFAULT 0,
  fees REAL DEFAULT 0,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  direction TEXT,
  bucket TEXT
);

CREATE INDEX IF NOT EXISTS idx_calibration_trades_outcome ON calibration_trades(outcome);
CREATE INDEX IF NOT EXISTS idx_calibration_trades_bucket ON calibration_trades(bucket);

-- Enable Row Level Security (disabled by default, configure per-table as needed)
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fills ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibration_trades ENABLE ROW LEVEL SECURITY;
