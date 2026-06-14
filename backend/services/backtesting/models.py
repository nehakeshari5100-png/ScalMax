from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TradeDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


class TradeOutcome(str, Enum):
    WIN = "win"
    LOSS = "loss"
    BREAK_EVEN = "break_even"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    SL = "stop_loss"
    TP = "take_profit"


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


SUPPORTED_ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
SUPPORTED_TIMEFRAMES = ["1m", "3m", "5m", "15m", "1h"]


class BacktestConfig(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"
    start_date: Optional[str] = None  # ISO format or empty for max available
    end_date: Optional[str] = None
    initial_capital: float = 10_000.0
    position_size_pct: float = Field(default=100.0, ge=1.0, le=100.0)
    max_open_positions: int = Field(default=1, ge=1, le=10)
    slippage_pct: float = Field(default=0.05, ge=0.0, le=1.0)
    fee_pct: float = Field(default=0.04, ge=0.0, le=1.0)
    risk_per_trade_pct: float = Field(default=1.0, ge=0.1, le=10.0)
    sl_pct: Optional[float] = None
    tp_pct: Optional[float] = None
    use_trailing_sl: bool = False
    trailing_sl_activation_pct: float = Field(default=0.5, ge=0.0)
    trailing_sl_distance_pct: float = Field(default=0.3, ge=0.0)
    strategy_version: str = "v1"


class BacktestCandle(BaseModel):
    timestamp: int = 0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


class BacktestSignal(BaseModel):
    direction: TradeDirection = TradeDirection.LONG
    price: float = 0.0
    timestamp: int = 0
    confidence: float = 0.0
    reason: str = ""


class BacktestOrder(BaseModel):
    timestamp: int = 0
    type: OrderType = OrderType.MARKET
    price: float = 0.0
    filled_price: float = 0.0
    size: float = 0.0
    direction: TradeDirection = TradeDirection.LONG
    fees: float = 0.0


class BacktestTrade(BaseModel):
    id: int = 0
    direction: TradeDirection = TradeDirection.LONG
    entry_time: int = 0
    entry_price: float = 0.0
    exit_time: int = 0
    exit_price: float = 0.0
    size: float = 0.0
    quantity: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    fees_paid: float = 0.0
    r_multiple: float = 0.0
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    bars_held: int = 0
    entry_reason: str = ""
    exit_reason: str = ""
    outcome: TradeOutcome = TradeOutcome.BREAK_EVEN


class EquityPoint(BaseModel):
    timestamp: int = 0
    equity: float = 0.0
    drawdown: float = 0.0
    drawdown_pct: float = 0.0


class MonthlyPerformance(BaseModel):
    year: int = 0
    month: int = 0
    trades: int = 0
    wins: int = 0
    losses: int = 0
    net_pnl: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade: float = 0.0


class BacktestMetrics(BaseModel):
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    break_even: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    avg_r_multiple: float = 0.0
    avg_win_r: float = 0.0
    avg_loss_r: float = 0.0
    profit_factor: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    net_profit_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    avg_trade_duration_bars: float = 0.0
    avg_trade_duration_seconds: int = 0
    expectancy: float = 0.0
    expectancy_percent: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    largest_win_pct: float = 0.0
    largest_loss_pct: float = 0.0
    avg_volume: float = 0.0
    total_fees: float = 0.0
    final_equity: float = 0.0
    return_pct: float = 0.0


class BacktestResult(BaseModel):
    id: Optional[str] = None
    config: BacktestConfig = Field(default_factory=BacktestConfig)
    status: BacktestStatus = BacktestStatus.PENDING
    metrics: BacktestMetrics = Field(default_factory=BacktestMetrics)
    trades: List[BacktestTrade] = Field(default_factory=list)
    equity_curve: List[EquityPoint] = Field(default_factory=list)
    monthly: List[MonthlyPerformance] = Field(default_factory=list)
    signals_generated: int = 0
    candles_processed: int = 0
    start_time: int = 0
    end_time: int = 0
    duration_ms: int = 0
    error: Optional[str] = None
    report_path: Optional[str] = None


class BacktestRunRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 10_000.0
    position_size_pct: float = 100.0
    max_open_positions: int = 1
    slippage_pct: float = 0.05
    fee_pct: float = 0.04
    risk_per_trade_pct: float = 1.0
    sl_pct: Optional[float] = None
    tp_pct: Optional[float] = None
    use_trailing_sl: bool = False
    strategy_version: str = "v1"


class BacktestRunResponse(BaseModel):
    success: bool
    data: Optional[BacktestResult] = None
    error: Optional[str] = None


class BacktestListResponse(BaseModel):
    success: bool
    data: List[BacktestResult] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None
