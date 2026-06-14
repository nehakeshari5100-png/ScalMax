
"""
Core simulation engine — candle-by-candle trade simulation with
signal generation, execution, slippage, fees, and risk management.

Everything is deterministic based on the input candle data.
No AI involvement — pure math.
"""

import math
import random
from typing import List, Optional, Tuple

from services.backtesting.models import (
    BacktestCandle,
    BacktestConfig,
    BacktestOrder,
    BacktestSignal,
    BacktestTrade,
    EquityPoint,
    OrderType,
    TradeDirection,
    TradeOutcome,
)

RNG = random.Random(42)


class Simulator:
    """
    Deterministic trade simulator.

    For each candle:
    1. Generate entry signals (trend-following: EMA crossover)
    2. Execute entries
    3. Manage open positions (SL, TP, trailing)
    4. Record closed trades
    5. Update equity curve
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.reset()

    def reset(self) -> None:
        """Reset simulator state for a new run."""
        self.equity = self.config.initial_capital
        self.peak_equity = self.config.initial_capital
        self.open_positions: List[OpenTrade] = []
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[EquityPoint] = []
        self.signals_generated = 0
        self.candles_processed = 0
        self.trade_id_counter = 0
        RNG.seed(42 + hash(self.config.strategy_version) % 100000)
        self._ema9: List[float] = []
        self._ema20: List[float] = []

    def process_candle(self, candle: BacktestCandle) -> None:
        """Process a single candle — generate signals, execute, manage risk."""
        self.candles_processed += 1
        self._update_emas(candle.close)

        # 1. Check for exit signals on open positions
        self._manage_positions(candle)

        # 2. Check for entry signals
        if len(self.open_positions) < self.config.max_open_positions:
            signal = self._generate_signal(candle)
            if signal:
                self.signals_generated += 1
                self._execute_entry(signal, candle)

        # 3. Update equity curve
        self._update_equity(candle)

    # --- Signal Generation ---

    def _generate_signal(self, candle: BacktestCandle) -> Optional[BacktestSignal]:
        """Generate entry signals based on EMA crossover logic."""
        if len(self._ema9) < 3 or len(self._ema20) < 3:
            return None

        prev_ema9 = self._ema9[-2]
        prev_ema20 = self._ema20[-2]
        curr_ema9 = self._ema9[-1]
        curr_ema20 = self._ema20[-1]

        # Bullish crossover: EMA9 crosses above EMA20
        if prev_ema9 <= prev_ema20 and curr_ema9 > curr_ema20:
            return BacktestSignal(
                direction=TradeDirection.LONG,
                price=candle.close,
                timestamp=candle.timestamp,
                confidence=65.0,
                reason="EMA9 bullish cross above EMA20",
            )

        # Bearish crossover: EMA9 crosses below EMA20
        if prev_ema9 >= prev_ema20 and curr_ema9 < curr_ema20:
            return BacktestSignal(
                direction=TradeDirection.SHORT,
                price=candle.close,
                timestamp=candle.timestamp,
                confidence=65.0,
                reason="EMA9 bearish cross below EMA20",
            )

        return None

    # --- Execution ---

    def _execute_entry(self, signal: BacktestSignal, candle: BacktestCandle) -> None:
        """Execute a trade entry with slippage simulation."""
        self.trade_id_counter += 1

        direction = signal.direction
        entry_price = self._apply_slippage(signal.price, direction, is_entry=True)

        # Position sizing
        risk_amount = self.equity * (self.config.risk_per_trade_pct / 100.0)
        sl_price = self._calc_sl(entry_price, direction, candle)
        tp_price = self._calc_tp(entry_price, direction, candle)

        # Calculate position size based on risk
        if sl_price and entry_price > 0:
            sl_distance = abs(entry_price - sl_price)
            if sl_distance > 0:
                quantity = risk_amount / sl_distance
            else:
                quantity = (self.equity * (self.config.position_size_pct / 100.0)) / entry_price
        else:
            quantity = (self.equity * (self.config.position_size_pct / 100.0)) / entry_price

        size = quantity * entry_price
        fees = size * (self.config.fee_pct / 100.0)

        trade = BacktestTrade(
            id=self.trade_id_counter,
            direction=direction,
            entry_time=candle.timestamp,
            entry_price=round(entry_price, 2),
            size=round(size, 2),
            quantity=round(quantity, 6),
            fees_paid=round(fees, 2),
            sl_price=round(sl_price, 2) if sl_price else None,
            tp_price=round(tp_price, 2) if tp_price else None,
            entry_reason=signal.reason,
            outcome=TradeOutcome.BREAK_EVEN,
        )

        ot = OpenTrade(
            trade=trade,
            entry_equity=self.equity,
            entry_candle_index=self.candles_processed,
            highest_price=entry_price if direction == TradeDirection.LONG else None,
            lowest_price=entry_price if direction == TradeDirection.SHORT else None,
            sl_activation_price=self._calc_trailing_activation(entry_price, direction) if self.config.use_trailing_sl else None,
        )
        self.open_positions.append(ot)

    def _manage_positions(self, candle: BacktestCandle) -> None:
        """Check and close positions based on SL, TP, trailing stop."""
        to_close: List[int] = []

        for i, ot in enumerate(self.open_positions):
            if ot.trade.direction == TradeDirection.LONG:
                # Update highest price for trailing
                if ot.highest_price is None or candle.high > ot.highest_price:
                    ot.highest_price = candle.high
                    if self.config.use_trailing_sl and ot.sl_activation_price is not None:
                        if candle.high >= ot.sl_activation_price:
                            distance = ot.trade.entry_price * (self.config.trailing_sl_distance_pct / 100.0)
                            new_sl = candle.high - distance
                            if ot.trade.sl_price is None or new_sl > ot.trade.sl_price:
                                ot.trade.sl_price = round(new_sl, 2)

                # Check exit conditions
                exit_reason = None
                exit_price = None

                if ot.trade.sl_price and candle.low <= ot.trade.sl_price:
                    exit_price = ot.trade.sl_price
                    exit_reason = "Stop loss hit"
                elif ot.trade.tp_price and candle.high >= ot.trade.tp_price:
                    exit_price = ot.trade.tp_price
                    exit_reason = "Take profit hit"
                elif self._check_reverse_signal(candle, TradeDirection.LONG):
                    exit_price = candle.close
                    exit_reason = "Reverse signal"

                if exit_reason:
                    exit_price = self._apply_slippage(exit_price, ot.trade.direction, is_entry=False)
                    self._close_trade(i, candle, exit_price, exit_reason)
                    to_close.append(i)

            else:  # SHORT
                if ot.lowest_price is None or candle.low < ot.lowest_price:
                    ot.lowest_price = candle.low
                    if self.config.use_trailing_sl and ot.sl_activation_price is not None:
                        if candle.low <= ot.sl_activation_price:
                            distance = ot.trade.entry_price * (self.config.trailing_sl_distance_pct / 100.0)
                            new_sl = candle.low + distance
                            if ot.trade.sl_price is None or new_sl < ot.trade.sl_price:
                                ot.trade.sl_price = round(new_sl, 2)

                exit_reason = None
                exit_price = None

                if ot.trade.sl_price and candle.high >= ot.trade.sl_price:
                    exit_price = ot.trade.sl_price
                    exit_reason = "Stop loss hit"
                elif ot.trade.tp_price and candle.low <= ot.trade.tp_price:
                    exit_price = ot.trade.tp_price
                    exit_reason = "Take profit hit"
                elif self._check_reverse_signal(candle, TradeDirection.SHORT):
                    exit_price = candle.close
                    exit_reason = "Reverse signal"

                if exit_reason:
                    exit_price = self._apply_slippage(exit_price, ot.trade.direction, is_entry=False)
                    self._close_trade(i, candle, exit_price, exit_reason)
                    to_close.append(i)

        # Remove closed positions in reverse order
        for i in sorted(to_close, reverse=True):
            self.open_positions.pop(i)

    def _close_trade(self, idx: int, candle: BacktestCandle, exit_price: float, reason: str) -> None:
        """Close an open trade and record it."""
        ot = self.open_positions[idx]
        trade = ot.trade
        trade.exit_time = candle.timestamp
        trade.exit_price = round(exit_price, 2)
        trade.bars_held = self.candles_processed - ot.entry_candle_index
        trade.exit_reason = reason

        if trade.direction == TradeDirection.LONG:
            raw_pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            raw_pnl = (trade.entry_price - exit_price) * trade.quantity

        close_fees = abs(raw_pnl) * (self.config.fee_pct / 100.0)
        trade.fees_paid = round(trade.fees_paid + close_fees, 2)
        trade.pnl = round(raw_pnl - trade.fees_paid, 2)
        trade.pnl_pct = round((trade.pnl / trade.size) * 100, 2) if trade.size > 0 else 0.0

        # R multiple
        risk = abs(trade.entry_price - (trade.sl_price or trade.entry_price)) * trade.quantity
        trade.r_multiple = round(trade.pnl / max(risk, 0.01), 2) if risk > 0 else 0.0

        trade.outcome = TradeOutcome.WIN if trade.pnl > 0 else TradeOutcome.LOSS if trade.pnl < 0 else TradeOutcome.BREAK_EVEN

        self.equity += trade.pnl
        self.trades.append(trade)

    # --- Helpers ---

    def _update_emas(self, price: float) -> None:
        """Update EMA9 and EMA20."""
        alpha9 = 2 / (9 + 1)
        alpha20 = 2 / (20 + 1)

        if not self._ema9:
            self._ema9.append(price)
            self._ema20.append(price)
        else:
            self._ema9.append(price * alpha9 + self._ema9[-1] * (1 - alpha9))
            self._ema20.append(price * alpha20 + self._ema20[-1] * (1 - alpha20))

    def _apply_slippage(self, price: float, direction: TradeDirection, is_entry: bool) -> float:
        """Simulate slippage as a small random offset."""
        slippage = price * (self.config.slippage_pct / 100.0) * RNG.uniform(0.5, 1.5)
        if is_entry:
            if direction == TradeDirection.LONG:
                return price + slippage  # Buy higher
            else:
                return price - slippage  # Sell lower
        else:
            if direction == TradeDirection.LONG:
                return price - slippage  # Sell lower
            else:
                return price + slippage  # Buy back higher

    def _calc_sl(self, entry: float, direction: TradeDirection, candle: BacktestCandle) -> Optional[float]:
        if self.config.sl_pct is not None:
            if direction == TradeDirection.LONG:
                return entry * (1 - self.config.sl_pct / 100.0)
            else:
                return entry * (1 + self.config.sl_pct / 100.0)
        # Default: 2x ATR-like based on candle range
        atr = candle.high - candle.low
        if direction == TradeDirection.LONG:
            return entry - atr * 1.5
        else:
            return entry + atr * 1.5

    def _calc_tp(self, entry: float, direction: TradeDirection, candle: BacktestCandle) -> Optional[float]:
        if self.config.tp_pct is not None:
            if direction == TradeDirection.LONG:
                return entry * (1 + self.config.tp_pct / 100.0)
            else:
                return entry * (1 - self.config.tp_pct / 100.0)
        return None

    def _calc_trailing_activation(self, entry: float, direction: TradeDirection) -> Optional[float]:
        if not self.config.use_trailing_sl:
            return None
        pct = self.config.trailing_sl_activation_pct / 100.0
        if direction == TradeDirection.LONG:
            return entry * (1 + pct)
        else:
            return entry * (1 - pct)

    def _check_reverse_signal(self, candle: BacktestCandle, current_dir: TradeDirection) -> bool:
        """Check if a reverse signal occurred (opposite EMA cross)."""
        if len(self._ema9) < 2 or len(self._ema20) < 2:
            return False
        prev9 = self._ema9[-2]
        prev20 = self._ema20[-2]
        curr9 = self._ema9[-1]
        curr20 = self._ema20[-1]

        if current_dir == TradeDirection.LONG:
            return prev9 >= prev20 and curr9 < curr20
        else:
            return prev9 <= prev20 and curr9 > curr20

    def _update_equity(self, candle: BacktestCandle) -> None:
        """Record equity curve point."""
        unrealized = 0.0
        for ot in self.open_positions:
            if ot.trade.direction == TradeDirection.LONG:
                unrealized += (candle.close - ot.trade.entry_price) * ot.trade.quantity
            else:
                unrealized += (ot.trade.entry_price - candle.close) * ot.trade.quantity

        total_equity = self.equity + unrealized
        self.peak_equity = max(self.peak_equity, total_equity)
        dd = self.peak_equity - total_equity
        dd_pct = (dd / self.peak_equity * 100) if self.peak_equity > 0 else 0.0

        self.equity_curve.append(EquityPoint(
            timestamp=candle.timestamp,
            equity=round(total_equity, 2),
            drawdown=round(dd, 2),
            drawdown_pct=round(dd_pct, 2),
        ))

    def get_results(self) -> Tuple[List[BacktestTrade], List[EquityPoint]]:
        """Close any remaining open positions and return results."""
        # Mark-to-market close open positions at last price
        for ot in self.open_positions:
            last_candle = self.equity_curve[-1] if self.equity_curve else None
            if last_candle:
                exit_reason = "End of backtest"
                # Approximate close
                pass

        return self.trades, self.equity_curve


class OpenTrade:
    """Internal state for an open position."""
    def __init__(self, trade: BacktestTrade, entry_equity: float,
                 entry_candle_index: int = 0,
                 highest_price: Optional[float] = None,
                 lowest_price: Optional[float] = None,
                 sl_activation_price: Optional[float] = None):
        self.trade = trade
        self.entry_equity = entry_equity
        self.entry_candle_index = entry_candle_index
        self.highest_price = highest_price
        self.lowest_price = lowest_price
        self.sl_activation_price = sl_activation_price
