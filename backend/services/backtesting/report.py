
"""
Generates BACKTEST_REPORT.md from a BacktestResult.
"""

import datetime
from typing import List

from services.backtesting.models import (
    BacktestResult,
    BacktestTrade,
    MonthlyPerformance,
)


def generate_report(result: BacktestResult) -> str:
    """Generate a professional BACKTEST_REPORT.md from backtest results."""
    c = result.config
    m = result.metrics

    lines: List[str] = []
    _add = lambda s: lines.append(s)
    _add("")
    _add("# BACKTEST REPORT")
    _add("")
    _add(f"**Generated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _add(f"**Strategy Version**: {c.strategy_version}")
    _add(f"**Status**: {result.status.value}")
    _add("")
    _add("---")
    _add("")
    _add("## Configuration")
    _add("")
    _add(f"| Parameter | Value |")
    _add(f"|-----------|-------|")
    _add(f"| Symbol | {c.symbol} |")
    _add(f"| Timeframe | {c.timeframe} |")
    _add(f"| Date Range | {c.start_date or 'max available'} → {c.end_date or 'max available'} |")
    _add(f"| Initial Capital | ${c.initial_capital:,.2f} |")
    _add(f"| Position Size | {c.position_size_pct}% |")
    _add(f"| Max Open Positions | {c.max_open_positions} |")
    _add(f"| Risk per Trade | {c.risk_per_trade_pct}% |")
    _add(f"| Slippage | {c.slippage_pct}% |")
    _add(f"| Fee | {c.fee_pct}% |")
    _add(f"| SL | {c.sl_pct or 'ATR-based'}% |")
    _add(f"| TP | {c.tp_pct or 'None'}% |")
    _add(f"| Trailing SL | {'Yes' if c.use_trailing_sl else 'No'} |")
    _add("")
    _add("---")
    _add("")
    _add("## Summary")
    _add("")
    _add(f"| Metric | Value |")
    _add(f"|--------|-------|")
    _add(f"| Total Trades | {m.total_trades} |")
    _add(f"| Candles Processed | {result.candles_processed} |")
    _add(f"| Signals Generated | {result.signals_generated} |")
    _add(f"| Win Rate | {m.win_rate}% |")
    _add(f"| Loss Rate | {m.loss_rate}% |")
    _add(f"| Break-Even | {m.break_even} |")
    _add(f"| Net Profit | ${m.net_profit:,.2f} ({m.net_profit_pct:+.2f}%) |")
    _add(f"| Final Equity | ${m.final_equity:,.2f} |")
    _add(f"| Return | {m.return_pct:+.2f}% |")
    _add("")
    _add("---")
    _add("")
    _add("## Risk & Reward")
    _add("")
    _add(f"| Metric | Value |")
    _add(f"|--------|-------|")
    _add(f"| Profit Factor | {m.profit_factor} |")
    _add(f"| Average R Multiple | {m.avg_r_multiple} |")
    _add(f"| Average Win R | {m.avg_win_r} |")
    _add(f"| Average Loss R | {m.avg_loss_r} |")
    _add(f"| Sharpe Ratio | {m.sharpe_ratio} |")
    _add(f"| Sortino Ratio | {m.sortino_ratio} |")
    _add(f"| Max Drawdown | ${m.max_drawdown:,.2f} ({m.max_drawdown_pct:.2f}%) |")
    _add(f"| Expectancy | ${m.expectancy:,.2f} ({m.expectancy_percent:+.2f}%) |")
    _add("")
    _add("---")
    _add("")
    _add("## P&L Breakdown")
    _add("")
    _add(f"| Metric | Value |")
    _add(f"|--------|-------|")
    _add(f"| Gross Profit | ${m.gross_profit:,.2f} |")
    _add(f"| Gross Loss | -${m.gross_loss:,.2f} |")
    _add(f"| Total Fees | ${m.total_fees:,.2f} |")
    _add(f"| Average Win | ${m.gross_profit / max(m.wins, 1):,.2f} ({m.avg_win_pct:+.2f}%) |")
    _add(f"| Average Loss | -${m.gross_loss / max(m.losses, 1):,.2f} ({m.avg_loss_pct:+.2f}%) |")
    _add(f"| Largest Win | ${m.largest_win:,.2f} ({m.largest_win_pct:+.2f}%) |")
    _add(f"| Largest Loss | -${abs(m.largest_loss):,.2f} ({m.largest_loss_pct:+.2f}%) |")
    _add(f"| Avg Trade Duration | {m.avg_trade_duration_bars} bars ({_fmt_duration(m.avg_trade_duration_seconds)}) |")
    _add("")
    _add("---")
    _add("")
    _add("## Monthly Performance")
    _add("")
    _add("| Month | Trades | Wins | Losses | Win Rate | Net PnL | Profit Factor | Avg Trade |")
    _add("|-------|--------|------|--------|----------|---------|---------------|-----------|")
    for mp in result.monthly:
        _add(f"| {mp.year}-{mp.month:02d} | {mp.trades} | {mp.wins} | {mp.losses} | "
             f"{mp.win_rate}% | ${mp.net_pnl:+,.2f} | {mp.profit_factor} | ${mp.avg_trade:+,.2f} |")
    if not result.monthly:
        _add("| *No monthly data* | | | | | | |")
    _add("")
    _add("---")
    _add("")
    _add("## Trade List")
    _add("")
    _add("| # | Direction | Entry | Exit | PnL | R | Bars | Outcome |")
    _add("|---|-----------|-------|------|-----|---|------|---------|")
    for t in result.trades[-50:]:  # Show last 50 trades
        _add(f"| {t.id} | {t.direction.value} | ${t.entry_price:,.2f} | ${t.exit_price:,.2f} | "
             f"${t.pnl:+,.2f} | {t.r_multiple:+.2f}R | {t.bars_held} | {t.outcome.value} |")
    if not result.trades:
        _add("| *No trades* | | | | | | |")
    _add("")
    _add("---")
    _add("")
    _add("## Disclaimer")
    _add("")
    _add("This backtest is for informational purposes only. Past performance does not "
          "guarantee future results. All trading involves risk.")
    _add("")

    return "\n".join(lines)


def _fmt_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    else:
        return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"
