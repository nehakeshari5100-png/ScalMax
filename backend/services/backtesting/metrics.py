
"""
Performance metrics calculation for backtest results.

All calculations are pure math using Python built-ins.
Computes: Win Rate, Sharpe, Sortino, Max DD, Profit Factor, Expectancy, etc.
"""
import math
from typing import List, Tuple

from services.backtesting.models import (
    BacktestMetrics,
    BacktestTrade,
    EquityPoint,
    MonthlyPerformance,
    TradeDirection,
    TradeOutcome,
)


def compute_metrics(
    trades: List[BacktestTrade],
    equity_curve: List[EquityPoint],
    initial_capital: float,
    timeframe_ms: int,
) -> BacktestMetrics:
    """Compute all performance metrics from backtest results."""
    m = BacktestMetrics()

    if not trades:
        return m

    # Basic counts
    m.total_trades = len(trades)
    m.wins = sum(1 for t in trades if t.outcome == TradeOutcome.WIN)
    m.losses = sum(1 for t in trades if t.outcome == TradeOutcome.LOSS)
    m.break_even = sum(1 for t in trades if t.outcome == TradeOutcome.BREAK_EVEN)

    m.win_rate = round((m.wins / max(m.total_trades, 1)) * 100, 2)
    m.loss_rate = round((m.losses / max(m.total_trades, 1)) * 100, 2)

    # R-multiple stats
    r_values = [t.r_multiple for t in trades]
    win_r = [t.r_multiple for t in trades if t.outcome == TradeOutcome.WIN]
    loss_r = [t.r_multiple for t in trades if t.outcome == TradeOutcome.LOSS]

    m.avg_r_multiple = round(sum(r_values) / max(len(r_values), 1), 2)
    m.avg_win_r = round(sum(win_r) / max(len(win_r), 1), 2) if win_r else 0.0
    m.avg_loss_r = round(sum(loss_r) / max(len(loss_r), 1), 2) if loss_r else 0.0

    # Profit / Loss
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = sum(t.pnl for t in trades if t.pnl < 0)
    m.gross_profit = round(gross_profit, 2)
    m.gross_loss = round(abs(gross_loss), 2)
    m.net_profit = round(sum(t.pnl for t in trades), 2)
    m.profit_factor = round(gross_profit / max(abs(gross_loss), 0.01), 2)

    # P&L percentages
    m.avg_win_pct = round(
        sum(t.pnl_pct for t in trades if t.outcome == TradeOutcome.WIN) / max(m.wins, 1), 2
    )
    m.avg_loss_pct = round(
        sum(t.pnl_pct for t in trades if t.outcome == TradeOutcome.LOSS) / max(m.losses, 1), 2
    )

    # Largest win/loss
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]
    if winning_trades:
        m.largest_win = round(max(t.pnl for t in winning_trades), 2)
        m.largest_win_pct = round(max(t.pnl_pct for t in winning_trades), 2)
    if losing_trades:
        m.largest_loss = round(min(t.pnl for t in losing_trades), 2)
        m.largest_loss_pct = round(min(t.pnl_pct for t in losing_trades), 2)

    # Trade duration
    if trades:
        avg_bars = sum(t.bars_held for t in trades) / len(trades)
        m.avg_trade_duration_bars = round(avg_bars, 1)
        m.avg_trade_duration_seconds = int(avg_bars * timeframe_ms / 1000)

    # Expectancy
    m.expectancy = round(sum(t.pnl for t in trades) / max(len(trades), 1), 2)
    m.expectancy_percent = round(
        sum(t.pnl_pct for t in trades) / max(len(trades), 1), 2
    )

    # Fees
    m.total_fees = round(sum(t.fees_paid for t in trades), 2)

    # Final equity
    m.final_equity = round(initial_capital + sum(t.pnl for t in trades), 2)
    m.net_profit_pct = round((m.final_equity - initial_capital) / initial_capital * 100, 2)
    m.return_pct = m.net_profit_pct

    # --- Equity-based metrics ---
    if equity_curve:
        equities = [p.equity for p in equity_curve]
        returns = _compute_returns(equities)

        # Max drawdown
        peak = equities[0]
        max_dd = 0.0
        max_dd_pct = 0.0
        for eq in equities:
            if eq > peak:
                peak = eq
            dd = peak - eq
            dd_pct = (dd / peak * 100) if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct
        m.max_drawdown = round(max_dd, 2)
        m.max_drawdown_pct = round(max_dd_pct, 2)

        # Sharpe Ratio (annualized, assuming 252 trading days)
        # Using daily returns if 1d timeframe, else scale by periods
        periods_per_year = _periods_per_year(timeframe_ms)
        if len(returns) > 1:
            avg_ret = sum(returns) / len(returns)
            std_ret = _std(returns)
            if std_ret > 0:
                sharpe = (avg_ret / std_ret) * math.sqrt(periods_per_year)
                m.sharpe_ratio = round(sharpe, 2)

            # Sortino Ratio (downside deviation only)
            downside = [r for r in returns if r < 0]
            if downside:
                downside_std = _std(downside)
                if downside_std > 0:
                    sortino = (avg_ret / downside_std) * math.sqrt(periods_per_year)
                    m.sortino_ratio = round(sortino, 2)

    return m


def compute_monthly(trades: List[BacktestTrade]) -> List[MonthlyPerformance]:
    """Group trades by calendar month and compute per-month stats."""
    from collections import defaultdict
    import datetime

    monthly: dict = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0})

    for t in trades:
        if t.entry_time == 0:
            continue
        dt = datetime.datetime.fromtimestamp(t.entry_time / 1000)
        key = (dt.year, dt.month)
        monthly[key]["trades"] += 1
        if t.outcome == TradeOutcome.WIN:
            monthly[key]["wins"] += 1
        elif t.outcome == TradeOutcome.LOSS:
            monthly[key]["losses"] += 1
        monthly[key]["pnl"] += t.pnl

    results = []
    for (year, month), data in sorted(monthly.items()):
        wins = data["wins"]
        total = data["trades"]
        win_rate = (wins / max(total, 1)) * 100
        gross_w = sum(t.pnl for t in trades if t.outcome == TradeOutcome.WIN
                      and datetime.datetime.fromtimestamp(t.entry_time / 1000).year == year
                      and datetime.datetime.fromtimestamp(t.entry_time / 1000).month == month)
        gross_l = sum(abs(t.pnl) for t in trades if t.outcome == TradeOutcome.LOSS
                      and datetime.datetime.fromtimestamp(t.entry_time / 1000).year == year
                      and datetime.datetime.fromtimestamp(t.entry_time / 1000).month == month)

        results.append(MonthlyPerformance(
            year=year,
            month=month,
            trades=total,
            wins=wins,
            losses=data["losses"],
            net_pnl=round(data["pnl"], 2),
            win_rate=round(win_rate, 2),
            profit_factor=round(gross_w / max(gross_l, 0.01), 2),
            avg_trade=round(data["pnl"] / max(total, 1), 2),
        ))

    return results


def _compute_returns(equities: List[float]) -> List[float]:
    """Compute period-over-period returns."""
    if len(equities) < 2:
        return []
    returns = []
    for i in range(1, len(equities)):
        prev = equities[i - 1]
        if prev > 0:
            returns.append((equities[i] - prev) / prev)
    return returns


def _std(values: List[float]) -> float:
    """Population standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _periods_per_year(timeframe_ms: int) -> int:
    """Estimate number of periods per year for annualization."""
    mapping = {
        60_000: 60 * 24 * 365,       # 1m
        180_000: 20 * 24 * 365,       # 3m
        300_000: 12 * 24 * 365,       # 5m
        900_000: 4 * 24 * 365,        # 15m
        3_600_000: 24 * 365,          # 1h
    }
    return mapping.get(timeframe_ms, 252)
