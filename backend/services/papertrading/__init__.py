"""
Paper Trading System — Phase 12.

Simulates live trading with virtual balance for testing strategies
without real money. Tracks positions, PnL, risk, and performance.

Features:
- Virtual accounts with configurable balance
- Position opening/closing at market prices
- Automatic SL/TP execution
- Full PnL and risk tracking
- Performance dashboard stats
- Daily/monthly PnL aggregation
- Leaderboard across accounts
- Trade journal integration
"""

from services.papertrading.models import (
    VirtualAccount,
    Position,
    PositionStatus,
    PositionExitReason,
    TradeFill,
    PerformanceStats,
    LeaderboardEntry,
    CreateAccountRequest,
    OpenPositionRequest,
    ClosePositionRequest,
)
from services.papertrading.engine import PaperEngine
from services.papertrading.db import (
    create_account, get_account, list_accounts, update_account_balance, delete_account,
    create_position, get_position, list_positions, count_positions,
    close_position, cancel_position, get_open_positions,
    create_fill, get_fills_for_position,
    compute_stats, get_leaderboard,
)

__all__ = [
    "VirtualAccount",
    "Position",
    "PositionStatus",
    "PositionExitReason",
    "TradeFill",
    "PerformanceStats",
    "LeaderboardEntry",
    "CreateAccountRequest",
    "OpenPositionRequest",
    "ClosePositionRequest",
    "PaperEngine",
]
