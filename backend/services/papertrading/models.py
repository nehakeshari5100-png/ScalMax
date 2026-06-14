from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
import uuid
import time


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PositionExitReason(str, Enum):
    TAKE_PROFIT_1 = "tp1"
    TAKE_PROFIT_2 = "tp2"
    STOP_LOSS = "sl"
    MANUAL = "manual"
    CANCELLED = "cancelled"


class VirtualAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default"
    initial_balance: float = 10_000.0
    current_balance: float = 10_000.0
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))

    @property
    def total_pnl(self) -> float:
        return self.current_balance - self.initial_balance

    @property
    def total_pnl_pct(self) -> float:
        if self.initial_balance <= 0:
            return 0.0
        return (self.total_pnl / self.initial_balance) * 100


class TradeFill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    position_id: str = ""
    fill_type: str = ""  # entry / exit
    price: float = 0.0
    quantity: float = 0.0
    fee: float = 0.0
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


class Position(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    signal_id: Optional[str] = None
    symbol: str = ""
    timeframe: str = ""
    exchange: str = "binance"
    direction: str = ""  # long / short
    entry_price: float = 0.0
    quantity: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: Optional[float] = None
    status: PositionStatus = PositionStatus.OPEN
    opened_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    closed_at: Optional[int] = None
    close_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: Optional[PositionExitReason] = None
    fees: float = 0.0
    risk_amount: float = 0.0
    risk_pct: float = 0.0

    @property
    def rr_ratio(self) -> float:
        if self.risk_amount <= 0:
            return 0.0
        if self.pnl is None:
            return 0.0
        return abs(self.pnl) / self.risk_amount

    @property
    def holding_time_hours(self) -> float:
        end = self.closed_at or int(time.time() * 1000)
        return (end - self.opened_at) / 3_600_000


class CreateAccountRequest(BaseModel):
    name: str = "Default"
    initial_balance: float = 10_000.0


class OpenPositionRequest(BaseModel):
    account_id: str
    symbol: str
    timeframe: str = "5m"
    exchange: str = "binance"
    direction: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float] = None
    signal_id: Optional[str] = None
    risk_pct: float = 1.0  # % of balance to risk


class ClosePositionRequest(BaseModel):
    position_id: str
    close_price: float
    exit_reason: PositionExitReason = PositionExitReason.MANUAL


class AccountResponse(BaseModel):
    success: bool
    data: Optional[VirtualAccount] = None
    error: Optional[str] = None


class PositionResponse(BaseModel):
    success: bool
    data: Optional[Position] = None
    error: Optional[str] = None


class PositionListResponse(BaseModel):
    success: bool
    data: List[Position] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


class AccountListResponse(BaseModel):
    success: bool
    data: List[VirtualAccount] = Field(default_factory=list)
    error: Optional[str] = None


class PerformanceStats(BaseModel):
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    breakeven: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    avg_rr: float = 0.0
    avg_holding_time_hours: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    sharpe_ratio: float = 0.0
    daily_pnl: Dict[str, float] = Field(default_factory=dict)
    monthly_pnl: Dict[str, float] = Field(default_factory=dict)
    by_symbol: Dict[str, dict] = Field(default_factory=dict)


class StatsResponse(BaseModel):
    success: bool
    data: Optional[PerformanceStats] = None
    error: Optional[str] = None


class LeaderboardEntry(BaseModel):
    account_id: str
    account_name: str
    total_pnl: float
    total_pnl_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    current_balance: float


class LeaderboardResponse(BaseModel):
    success: bool
    data: List[LeaderboardEntry] = Field(default_factory=list)
    error: Optional[str] = None


class PeekPriceRequest(BaseModel):
    symbol: str = "BTCUSDT"
    exchange: str = "binance"


class PeekPriceResponse(BaseModel):
    success: bool
    price: Optional[float] = None
    error: Optional[str] = None
