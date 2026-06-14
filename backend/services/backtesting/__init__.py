
"""
Backtesting Engine — deterministic candle-by-candle simulation
with full performance metrics, report generation, and SQLite persistence.

Usage:
    from services.backtesting.engine import run_backtest
    from services.backtesting.models import BacktestRunRequest

    result = run_backtest(BacktestRunRequest(symbol="BTCUSDT", timeframe="5m"))
    print(result.metrics.sharpe_ratio)
"""

from services.backtesting.engine import run_backtest, get_result, list_results, delete_result
from services.backtesting.models import (
    BacktestRunRequest,
    BacktestRunResponse,
    BacktestResult,
    BacktestConfig,
    BacktestMetrics,
    BacktestTrade,
    MonthlyPerformance,
    EquityPoint,
    TradeDirection,
    BacktestStatus,
    SUPPORTED_ASSETS,
    SUPPORTED_TIMEFRAMES,
)

__all__ = [
    "run_backtest",
    "get_result",
    "list_results",
    "delete_result",
    "BacktestRunRequest",
    "BacktestRunResponse",
    "BacktestResult",
    "BacktestConfig",
    "BacktestMetrics",
    "BacktestTrade",
    "MonthlyPerformance",
    "EquityPoint",
    "TradeDirection",
    "BacktestStatus",
    "SUPPORTED_ASSETS",
    "SUPPORTED_TIMEFRAMES",
]
