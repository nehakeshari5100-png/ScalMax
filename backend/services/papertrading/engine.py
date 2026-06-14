import logging
import uuid
import time
from typing import Optional, List

from services.papertrading.models import (
    VirtualAccount,
    Position,
    PositionStatus,
    PositionExitReason,
    TradeFill,
    OpenPositionRequest,
    ClosePositionRequest,
    PerformanceStats,
    LeaderboardEntry,
)
from services.papertrading.db import (
    create_account as db_create_account,
    get_account as db_get_account,
    list_accounts as db_list_accounts,
    update_account_balance,
    delete_account as db_delete_account,
    create_position as db_create_position,
    get_position as db_get_position,
    list_positions as db_list_positions,
    count_positions as db_count_positions,
    close_position as db_close_position,
    cancel_position as db_cancel_position,
    get_open_positions as db_get_open_positions,
    create_fill as db_create_fill,
    get_fills_for_position as db_get_fills,
    compute_stats as db_compute_stats,
    get_leaderboard as db_get_leaderboard,
)

FEE_RATE = 0.0004  # 0.04% per side (maker)

logger = logging.getLogger(__name__)


class PaperEngine:
    """
    Paper trading simulation engine.

    Simulates position opening/closing with virtual balance,
    automatic SL/TP execution, fee calculation, and full PnL tracking.
    No real exchange execution.
    """

    @staticmethod
    def create_account(name: str = "Default", initial_balance: float = 10_000.0) -> VirtualAccount:
        account = VirtualAccount(name=name, initial_balance=initial_balance, current_balance=initial_balance)
        return db_create_account(account)

    @staticmethod
    def get_account(account_id: str) -> Optional[VirtualAccount]:
        return db_get_account(account_id)

    @staticmethod
    def list_accounts() -> List[VirtualAccount]:
        return db_list_accounts()

    @staticmethod
    def delete_account(account_id: str) -> bool:
        account = db_get_account(account_id)
        if not account:
            return False
        db_delete_account(account_id)
        return True

    @staticmethod
    def open_position(request: OpenPositionRequest) -> Optional[Position]:
        """
        Open a new paper position.

        Deducts risk amount from balance, saves position, records entry fill.
        """
        account = db_get_account(request.account_id)
        if not account:
            logger.error(f"Account {request.account_id} not found")
            return None

        if account.current_balance <= 0:
            logger.error("Account balance is zero or negative")
            return None

        # Calculate position size based on risk %
        risk_amount = account.current_balance * (request.risk_pct / 100)
        entry_price = request.entry_price
        stop_loss = request.stop_loss

        if entry_price <= 0:
            logger.error("Invalid entry price")
            return None

        # Calculate quantity based on risk
        if request.direction == "long":
            price_risk = entry_price - stop_loss
        else:
            price_risk = stop_loss - entry_price

        if price_risk <= 0:
            logger.error("Stop loss must be below entry for longs, above for shorts")
            return None

        quantity = risk_amount / price_risk
        entry_fee = (quantity * entry_price) * FEE_RATE

        # Use explicit quantity if provided (overrides risk-based calc)
        if request.quantity > 0:
            quantity = request.quantity
            risk_amount = quantity * abs(price_risk)

        pos = Position(
            account_id=request.account_id,
            signal_id=request.signal_id,
            symbol=request.symbol.upper(),
            timeframe=request.timeframe,
            exchange=request.exchange,
            direction=request.direction,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit_1=request.take_profit_1,
            take_profit_2=request.take_profit_2,
            fees=entry_fee,
            risk_amount=risk_amount,
            risk_pct=request.risk_pct,
        )

        db_create_position(pos)

        # Record entry fill
        fill = TradeFill(
            position_id=pos.id,
            fill_type="entry",
            price=entry_price,
            quantity=quantity,
            fee=entry_fee,
        )
        db_create_fill(fill)

        logger.info(f"Opened {request.direction} {quantity:.4f} {pos.symbol} @ {entry_price} (risk ${risk_amount:.2f})")
        return pos

    @staticmethod
    def close_position(request: ClosePositionRequest) -> Optional[Position]:
        """
        Close an open position and update account balance.

        Calculates realized PnL and credits/debits account.
        """
        position = db_get_position(request.position_id)
        if not position:
            logger.error(f"Position {request.position_id} not found")
            return None

        if position.status != PositionStatus.OPEN:
            logger.error(f"Position {request.position_id} is not open (status={position.status.value})")
            return None

        account = db_get_account(position.account_id)
        if not account:
            logger.error(f"Account {position.account_id} not found")
            return None

        close_price = request.close_price
        entry_fee = position.fees
        exit_fee = (position.quantity * close_price) * FEE_RATE
        total_fees = entry_fee + exit_fee

        # Calculate PnL
        if position.direction == "long":
            pnl = (close_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - close_price) * position.quantity

        pnl -= total_fees
        pnl_pct = (pnl / (position.entry_price * position.quantity)) * 100 if position.entry_price * position.quantity > 0 else 0

        # Update position
        db_close_position(
            position_id=position.id,
            close_price=close_price,
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 2),
            exit_reason=request.exit_reason.value,
            fees=exit_fee,
        )

        # Record exit fill
        fill = TradeFill(
            position_id=position.id,
            fill_type="exit",
            price=close_price,
            quantity=position.quantity,
            fee=exit_fee,
        )
        db_create_fill(fill)

        # Update account balance
        new_balance = account.current_balance + pnl
        update_account_balance(account.id, round(new_balance, 2))

        logger.info(f"Closed {position.direction} {position.symbol} @ {close_price} PnL=${pnl:.2f} ({pnl_pct:.2f}%)")
        return db_get_position(position.id)

    @staticmethod
    def cancel_position(position_id: str) -> Optional[Position]:
        """Cancel an open position (no PnL impact)."""
        position = db_get_position(position_id)
        if not position or position.status != PositionStatus.OPEN:
            return None
        db_cancel_position(position_id)
        return db_get_position(position_id)

    @staticmethod
    def check_stop_loss_take_profit(position: Position, current_price: float) -> Optional[ClosePositionRequest]:
        """
        Check if price has hit SL or TP for a position.

        Returns a ClosePositionRequest if triggered, None otherwise.
        """
        if position.status != PositionStatus.OPEN:
            return None

        if position.direction == "long":
            if current_price <= position.stop_loss:
                return ClosePositionRequest(position_id=position.id, close_price=position.stop_loss, exit_reason=PositionExitReason.STOP_LOSS)
            if position.take_profit_1 > 0 and current_price >= position.take_profit_1:
                return ClosePositionRequest(position_id=position.id, close_price=position.take_profit_1, exit_reason=PositionExitReason.TAKE_PROFIT_1)
            if position.take_profit_2 and position.take_profit_2 > 0 and current_price >= position.take_profit_2:
                return ClosePositionRequest(position_id=position.id, close_price=position.take_profit_2, exit_reason=PositionExitReason.TAKE_PROFIT_2)
        else:
            if current_price >= position.stop_loss:
                return ClosePositionRequest(position_id=position.id, close_price=position.stop_loss, exit_reason=PositionExitReason.STOP_LOSS)
            if position.take_profit_1 > 0 and current_price <= position.take_profit_1:
                return ClosePositionRequest(position_id=position.id, close_price=position.take_profit_1, exit_reason=PositionExitReason.TAKE_PROFIT_1)
            if position.take_profit_2 and position.take_profit_2 > 0 and current_price <= position.take_profit_2:
                return ClosePositionRequest(position_id=position.id, close_price=position.take_profit_2, exit_reason=PositionExitReason.TAKE_PROFIT_2)

        return None

    @staticmethod
    def get_position(position_id: str) -> Optional[Position]:
        return db_get_position(position_id)

    @staticmethod
    def list_positions(
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        signal_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Position]:
        pos_status = PositionStatus(status) if status else None
        return db_list_positions(
            account_id=account_id,
            status=pos_status,
            symbol=symbol,
            direction=direction,
            signal_id=signal_id,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def count_positions(account_id: Optional[str] = None, status: Optional[str] = None) -> int:
        pos_status = PositionStatus(status) if status else None
        return db_count_positions(account_id=account_id, status=pos_status)

    @staticmethod
    def get_open_positions(account_id: str) -> List[Position]:
        return db_get_open_positions(account_id)

    @staticmethod
    def get_fills(position_id: str) -> List[TradeFill]:
        return db_get_fills(position_id)

    @staticmethod
    def get_stats(account_id: str) -> PerformanceStats:
        return db_compute_stats(account_id)

    @staticmethod
    def get_leaderboard(limit: int = 20) -> List[LeaderboardEntry]:
        return db_get_leaderboard(limit)
