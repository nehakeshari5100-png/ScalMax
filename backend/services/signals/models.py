from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import datetime


class SignalType(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class SignalStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class SignalRecord(BaseModel):
    id: str = ""
    symbol: str = ""
    timeframe: str = ""
    exchange: str = "binance"
    signal_type: SignalType = SignalType.NEUTRAL
    direction: str = "neutral"
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    risk_reward_1: Optional[float] = None
    risk_reward_2: Optional[float] = None
    confidence: int = Field(default=0, ge=0, le=100)
    confluence_score: int = Field(default=0, ge=0, le=100)
    reasoning: str = ""
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    status: SignalStatus = SignalStatus.ACTIVE
    validation_status: ValidationStatus = ValidationStatus.PENDING
    strategy_version: str = "v1"
    session: str = ""
    created_at: int = 0
    updated_at: int = 0
    triggered_at: Optional[int] = None
    completed_at: Optional[int] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    outcome: Optional[str] = None  # 'win' | 'loss' | 'breakeven'


class SignalCreateRequest(BaseModel):
    symbol: str
    timeframe: str = "5m"
    exchange: str = "binance"
    direction: str = "neutral"
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    confidence: int = 0
    confluence_score: int = 0
    reasoning: str = ""
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    strategy_version: str = "v1"
    session: str = ""


class SignalListResponse(BaseModel):
    success: bool
    data: List[SignalRecord] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    error: Optional[str] = None


class SignalResponse(BaseModel):
    success: bool
    data: Optional[SignalRecord] = None
    error: Optional[str] = None


class SignalUpdateRequest(BaseModel):
    status: Optional[SignalStatus] = None
    validation_status: Optional[ValidationStatus] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    outcome: Optional[str] = None


class SignalPerformance(BaseModel):
    total_signals: int = 0
    active: int = 0
    completed: int = 0
    cancelled: int = 0
    expired: int = 0
    triggered: int = 0
    wins: int = 0
    losses: int = 0
    breakeven: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    avg_confidence: float = 0.0
    by_type: dict = Field(default_factory=dict)
    by_symbol: dict = Field(default_factory=dict)


class SignalPerformanceResponse(BaseModel):
    success: bool
    data: Optional[SignalPerformance] = None
    error: Optional[str] = None
