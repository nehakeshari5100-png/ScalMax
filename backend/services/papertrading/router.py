from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from services.papertrading.models import (
    CreateAccountRequest,
    OpenPositionRequest,
    ClosePositionRequest,
    AccountResponse,
    AccountListResponse,
    PositionResponse,
    PositionListResponse,
    StatsResponse,
    LeaderboardResponse,
    PeekPriceRequest,
    PeekPriceResponse,
)
from services.papertrading.engine import PaperEngine

router = APIRouter(tags=["Paper Trading"])


# ── Accounts ──

@router.post("/accounts", response_model=AccountResponse)
async def create_account(req: CreateAccountRequest):
    account = PaperEngine.create_account(name=req.name, initial_balance=req.initial_balance)
    return AccountResponse(success=True, data=account)


@router.get("/accounts", response_model=AccountListResponse)
async def list_accounts():
    accounts = PaperEngine.list_accounts()
    return AccountListResponse(success=True, data=accounts)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str):
    account = PaperEngine.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse(success=True, data=account)


@router.delete("/accounts/{account_id}", response_model=AccountResponse)
async def delete_account(account_id: str):
    ok = PaperEngine.delete_account(account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse(success=True, data=None)


# ── Positions ──

@router.post("/positions", response_model=PositionResponse)
async def open_position(req: OpenPositionRequest):
    position = PaperEngine.open_position(req)
    if not position:
        raise HTTPException(status_code=400, detail="Failed to open position")
    return PositionResponse(success=True, data=position)


@router.get("/positions", response_model=PositionListResponse)
async def list_positions(
    account_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    signal_id: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    positions = PaperEngine.list_positions(
        account_id=account_id, status=status, symbol=symbol,
        direction=direction, signal_id=signal_id, limit=limit, offset=offset,
    )
    total = PaperEngine.count_positions(account_id=account_id, status=status)
    return PositionListResponse(success=True, data=positions, total=total)


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str):
    position = PaperEngine.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return PositionResponse(success=True, data=position)


@router.post("/positions/{position_id}/close", response_model=PositionResponse)
async def close_position(position_id: str, req: ClosePositionRequest):
    req.position_id = position_id
    position = PaperEngine.close_position(req)
    if not position:
        raise HTTPException(status_code=400, detail="Failed to close position")
    return PositionResponse(success=True, data=position)


@router.post("/positions/{position_id}/cancel", response_model=PositionResponse)
async def cancel_position(position_id: str):
    position = PaperEngine.cancel_position(position_id)
    if not position:
        raise HTTPException(status_code=400, detail="Failed to cancel position")
    return PositionResponse(success=True, data=position)


@router.get("/positions/{position_id}/fills")
async def get_position_fills(position_id: str):
    fills = PaperEngine.get_fills(position_id)
    return {"success": True, "data": [f.model_dump() for f in fills]}


# ── Stats ──

@router.get("/stats/{account_id}", response_model=StatsResponse)
async def get_stats(account_id: str):
    account = PaperEngine.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    stats = PaperEngine.get_stats(account_id)
    return StatsResponse(success=True, data=stats)


# ── Leaderboard ──

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(limit: int = Query(20)):
    entries = PaperEngine.get_leaderboard(limit)
    return LeaderboardResponse(success=True, data=entries)


# ── Price peek (for SL/TP checking) ──

@router.post("/peek-price", response_model=PeekPriceResponse)
async def peek_price(req: PeekPriceRequest):
    """
    Get a current price for a symbol from the market data engine.
    Used by the frontend to check SL/TP triggers and update positions.
    """
    try:
        from services.market_data.exchange_manager import ExchangeManager
        manager = ExchangeManager.get_instance()
        response = await manager.get_candles(req.symbol, "1m", req.exchange, 1)
        if response and response.candles:
            price = response.candles[-1].close
            return PeekPriceResponse(success=True, price=price)
    except Exception as e:
        pass
    return PeekPriceResponse(success=False, error="Could not fetch price")


# ── Check all open positions for SL/TP (batch) ──

@router.post("/check-positions")
async def check_positions(account_id: str, current_price: float, symbol: Optional[str] = None):
    """
    Check all open positions for SL/TP triggers at the given price.
    Returns list of positions that were closed.
    """
    closed = []
    positions = PaperEngine.list_positions(account_id=account_id, status="open", symbol=symbol)
    for pos in positions:
        req = PaperEngine.check_stop_loss_take_profit(pos, current_price)
        if req:
            result = PaperEngine.close_position(req)
            if result:
                closed.append(result.model_dump())
    return {"success": True, "closed": closed}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "paper-trading"}
