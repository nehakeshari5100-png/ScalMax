
"""
Backtest Engine orchestrator — coordinates replay, simulation,
metrics computation, report generation, and persistence.
"""

import os
import time
from typing import Optional

from services.backtesting.models import (
    BacktestConfig,
    BacktestResult,
    BacktestStatus,
    BacktestRunRequest,
)
from services.backtesting.replay import CandleReplay
from services.backtesting.simulator import Simulator
from services.backtesting.metrics import compute_metrics, compute_monthly
from services.backtesting.report import generate_report
from services.backtesting import db


def run_backtest(request: BacktestRunRequest) -> BacktestResult:
    """
    Execute a full backtest from request to report.

    Steps:
    1. Build config
    2. Load/replay candles
    3. Run simulation
    4. Compute metrics
    5. Generate report
    6. Persist result
    """
    start_wall = time.time()

    config = BacktestConfig(
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        position_size_pct=request.position_size_pct,
        max_open_positions=request.max_open_positions,
        slippage_pct=request.slippage_pct,
        fee_pct=request.fee_pct,
        risk_per_trade_pct=request.risk_per_trade_pct,
        sl_pct=request.sl_pct,
        tp_pct=request.tp_pct,
        use_trailing_sl=request.use_trailing_sl,
        strategy_version=request.strategy_version,
    )

    result = BacktestResult(
        config=config,
        status=BacktestStatus.RUNNING,
        start_time=int(time.time() * 1000),
    )

    try:
        # 1. Load candles
        replay = CandleReplay(config)
        replay.generate_sample_candles(5000)
        result.candles_processed = len(replay)

        # 2. Run simulation
        simulator = Simulator(config)
        for candle in replay:
            simulator.process_candle(candle)

        trades, equity_curve = simulator.get_results()
        result.trades = trades
        result.equity_curve = equity_curve
        result.signals_generated = simulator.signals_generated

        # 3. Compute metrics
        tf_mapping = {"1m": 60_000, "3m": 180_000, "5m": 300_000,
                       "15m": 900_000, "1h": 3_600_000}
        timeframe_ms = tf_mapping.get(config.timeframe, 300_000)

        result.metrics = compute_metrics(trades, equity_curve, config.initial_capital, timeframe_ms)
        result.monthly = compute_monthly(trades)

        # 4. Generate report
        report_md = generate_report(result)
        report_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"BACKTEST_REPORT_{config.symbol}_{config.strategy_version}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        result.report_path = report_path

        result.status = BacktestStatus.COMPLETED

        # 5. Persist
        db.save_result(result)

    except Exception as e:
        result.status = BacktestStatus.FAILED
        result.error = str(e)

    result.end_time = int(time.time() * 1000)
    result.duration_ms = result.end_time - result.start_time

    return result


def get_result(rid: str) -> Optional[BacktestResult]:
    return db.load_result(rid)


def list_results(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    strategy_version: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple:
    return db.list_results(symbol, timeframe, strategy_version, limit, offset)


def delete_result(rid: str) -> bool:
    return db.delete_result(rid)
