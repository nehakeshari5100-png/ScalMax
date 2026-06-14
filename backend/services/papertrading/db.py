from typing import List, Optional, Dict
from datetime import datetime, timezone

from app.database import get_supabase
from services.papertrading.models import (
    VirtualAccount,
    Position,
    PositionStatus,
    TradeFill,
    PerformanceStats,
    LeaderboardEntry,
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_from_int(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def _int_from_ts(val) -> int:
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    return int(datetime.fromisoformat(val).timestamp() * 1000)


# ── Accounts ──

def create_account(account: VirtualAccount) -> VirtualAccount:
    supabase = get_supabase()
    supabase.table("accounts").insert({
        "id": account.id,
        "name": account.name,
        "initial_balance": account.initial_balance,
        "current_balance": account.current_balance,
        "total_pnl": account.current_balance - account.initial_balance,
        "total_pnl_pct": ((account.current_balance - account.initial_balance) / account.initial_balance * 100) if account.initial_balance > 0 else 0,
        "created_at": _ts_from_int(account.created_at),
        "updated_at": _ts_from_int(account.updated_at),
    }).execute()
    return account


def get_account(account_id: str) -> Optional[VirtualAccount]:
    supabase = get_supabase()
    resp = supabase.table("accounts").select("*").eq("id", account_id).maybe_single().execute()
    if resp.data:
        d = dict(resp.data)
        d["created_at"] = _int_from_ts(d.get("created_at"))
        d["updated_at"] = _int_from_ts(d.get("updated_at"))
        return VirtualAccount(**d)
    return None


def list_accounts() -> List[VirtualAccount]:
    supabase = get_supabase()
    resp = supabase.table("accounts").select("*").order("created_at", desc=True).execute()
    results = []
    for r in (resp.data or []):
        d = dict(r)
        d["created_at"] = _int_from_ts(d.get("created_at"))
        d["updated_at"] = _int_from_ts(d.get("updated_at"))
        results.append(VirtualAccount(**d))
    return results


def update_account_balance(account_id: str, new_balance: float):
    supabase = get_supabase()
    acct = get_account(account_id)
    initial = acct.initial_balance if acct else 10000
    total_pnl = new_balance - initial
    total_pnl_pct = (total_pnl / initial * 100) if initial > 0 else 0
    supabase.table("accounts").update({
        "current_balance": new_balance,
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "updated_at": _ts(),
    }).eq("id", account_id).execute()


def delete_account(account_id: str):
    supabase = get_supabase()
    # delete fills for this account's positions, then positions, then account
    pos_ids = supabase.table("positions").select("id").eq("account_id", account_id).execute()
    ids = [p["id"] for p in (pos_ids.data or [])]
    for pid in ids:
        supabase.table("fills").delete().eq("position_id", pid).execute()
    supabase.table("positions").delete().eq("account_id", account_id).execute()
    supabase.table("accounts").delete().eq("id", account_id).execute()


# ── Positions ──

def create_position(pos: Position) -> Position:
    supabase = get_supabase()
    supabase.table("positions").insert({
        "id": pos.id,
        "account_id": pos.account_id,
        "signal_id": pos.signal_id,
        "symbol": pos.symbol,
        "timeframe": pos.timeframe,
        "exchange": pos.exchange,
        "direction": pos.direction,
        "entry_price": pos.entry_price,
        "quantity": pos.quantity,
        "stop_loss": pos.stop_loss,
        "take_profit_1": pos.take_profit_1,
        "take_profit_2": pos.take_profit_2,
        "status": pos.status.value,
        "opened_at": _ts_from_int(pos.opened_at),
        "fees": pos.fees,
        "risk_amount": pos.risk_amount,
        "risk_pct": pos.risk_pct,
    }).execute()
    return pos


def get_position(position_id: str) -> Optional[Position]:
    supabase = get_supabase()
    resp = supabase.table("positions").select("*").eq("id", position_id).maybe_single().execute()
    if resp.data:
        return _row_to_position(resp.data)
    return None


def list_positions(
    account_id: Optional[str] = None,
    status: Optional[PositionStatus] = None,
    symbol: Optional[str] = None,
    direction: Optional[str] = None,
    signal_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Position]:
    supabase = get_supabase()
    query = supabase.table("positions").select("*")
    if account_id:
        query = query.eq("account_id", account_id)
    if status:
        query = query.eq("status", status.value)
    if symbol:
        query = query.eq("symbol", symbol.upper())
    if direction:
        query = query.eq("direction", direction)
    if signal_id:
        query = query.eq("signal_id", signal_id)
    resp = query.order("opened_at", desc=True).range(offset, offset + limit - 1).execute()
    return [_row_to_position(r) for r in (resp.data or [])]


def count_positions(
    account_id: Optional[str] = None,
    status: Optional[PositionStatus] = None,
) -> int:
    supabase = get_supabase()
    query = supabase.table("positions").select("*", count="exact", head=True)
    if account_id:
        query = query.eq("account_id", account_id)
    if status:
        query = query.eq("status", status.value)
    resp = query.execute()
    return resp.count or 0


def close_position(
    position_id: str,
    close_price: float,
    pnl: float,
    pnl_pct: float,
    exit_reason: str,
    fees: float = 0,
):
    supabase = get_supabase()
    supabase.table("positions").update({
        "status": "closed",
        "closed_at": _ts(),
        "close_price": close_price,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "exit_reason": exit_reason,
    }).eq("id", position_id).execute()


def cancel_position(position_id: str):
    supabase = get_supabase()
    supabase.table("positions").update({
        "status": "cancelled",
        "closed_at": _ts(),
        "exit_reason": "cancelled",
    }).eq("id", position_id).execute()


def get_open_positions(account_id: str) -> List[Position]:
    return list_positions(account_id=account_id, status=PositionStatus.OPEN)


# ── Fills ──

def create_fill(fill: TradeFill) -> TradeFill:
    supabase = get_supabase()
    supabase.table("fills").insert({
        "id": fill.id,
        "position_id": fill.position_id,
        "fill_type": fill.fill_type,
        "price": fill.price,
        "quantity": fill.quantity,
        "fee": fill.fee,
        "timestamp": _ts_from_int(fill.timestamp),
    }).execute()
    return fill


def get_fills_for_position(position_id: str) -> List[TradeFill]:
    supabase = get_supabase()
    resp = supabase.table("fills").select("*").eq("position_id", position_id).order("timestamp").execute()
    results = []
    for r in (resp.data or []):
        d = dict(r)
        d["timestamp"] = _int_from_ts(d.get("timestamp"))
        results.append(TradeFill(**d))
    return results


# ── Helpers ──

def _row_to_position(row: dict) -> Position:
    d = dict(row)
    d["status"] = PositionStatus(d["status"])
    d["opened_at"] = _int_from_ts(d.get("opened_at"))
    d["closed_at"] = _int_from_ts(d.get("closed_at"))
    return Position(**d)


# ── Performance Stats ──

def compute_stats(account_id: str) -> PerformanceStats:
    positions = list_positions(account_id=account_id, status=PositionStatus.CLOSED)
    account = get_account(account_id)

    total = len(positions)
    if total == 0:
        return PerformanceStats()

    wins = [p for p in positions if p.pnl and p.pnl > 0]
    losses = [p for p in positions if p.pnl and p.pnl < 0]
    breakeven = [p for p in positions if p.pnl and p.pnl == 0]

    total_pnl = sum(p.pnl or 0 for p in positions)
    gross_profit = sum(p.pnl for p in wins) if wins else 0
    gross_loss = abs(sum(p.pnl for p in losses)) if losses else 0

    win_rate = (len(wins) / total) * 100 if total > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
    avg_pnl = total_pnl / total if total > 0 else 0
    avg_rr = sum(p.rr_ratio for p in positions) / total if total > 0 else 0
    avg_holding = sum(p.holding_time_hours for p in positions) / total if total > 0 else 0
    best_trade = max((p.pnl for p in positions if p.pnl is not None), default=0)
    worst_trade = min((p.pnl for p in positions if p.pnl is not None), default=0)

    balance = account.initial_balance if account else 10000
    peak = balance
    max_dd = 0.0
    current_dd = 0.0
    for p in sorted(positions, key=lambda x: x.closed_at or 0):
        balance += p.pnl or 0
        if balance > peak:
            peak = balance
        dd = ((peak - balance) / peak) * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
        if p.status == PositionStatus.CLOSED and p.exit_reason in ("sl", "manual"):
            current_dd = dd

    pnl_values = [p.pnl or 0 for p in positions]
    avg = sum(pnl_values) / len(pnl_values)
    variance = sum((x - avg) ** 2 for x in pnl_values) / len(pnl_values)
    std_dev = variance ** 0.5
    sharpe = (avg / std_dev) * (365 ** 0.5) if std_dev > 0 else 0

    from datetime import datetime as dt
    daily_pnl: Dict[str, float] = {}
    monthly_pnl: Dict[str, float] = {}
    for p in positions:
        if p.closed_at:
            ts = p.closed_at / 1000 if p.closed_at > 1e12 else p.closed_at
            d = dt.fromtimestamp(ts, tz=timezone.utc)
            day_key = d.strftime("%Y-%m-%d")
            month_key = d.strftime("%Y-%m")
            daily_pnl[day_key] = daily_pnl.get(day_key, 0) + (p.pnl or 0)
            monthly_pnl[month_key] = monthly_pnl.get(month_key, 0) + (p.pnl or 0)

    by_symbol: Dict[str, dict] = {}
    for p in positions:
        if p.symbol not in by_symbol:
            by_symbol[p.symbol] = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        by_symbol[p.symbol]["trades"] += 1
        by_symbol[p.symbol]["wins"] += 1 if p.pnl and p.pnl > 0 else 0
        by_symbol[p.symbol]["losses"] += 1 if p.pnl and p.pnl < 0 else 0
        by_symbol[p.symbol]["pnl"] += p.pnl or 0
        by_symbol[p.symbol]["win_rate"] = (by_symbol[p.symbol]["wins"] / by_symbol[p.symbol]["trades"]) * 100

    return PerformanceStats(
        total_trades=total,
        wins=len(wins),
        losses=len(losses),
        breakeven=len(breakeven),
        win_rate=round(win_rate, 2),
        total_pnl=round(total_pnl, 2),
        avg_pnl=round(avg_pnl, 2),
        profit_factor=round(profit_factor, 2),
        max_drawdown=round(max_dd, 2),
        current_drawdown=round(current_dd, 2),
        avg_rr=round(avg_rr, 2),
        avg_holding_time_hours=round(avg_holding, 2),
        best_trade=round(best_trade, 2),
        worst_trade=round(worst_trade, 2),
        sharpe_ratio=round(sharpe, 2),
        daily_pnl=daily_pnl,
        monthly_pnl=monthly_pnl,
        by_symbol=by_symbol,
    )


# ── Leaderboard ──

def get_leaderboard(limit: int = 20) -> List[LeaderboardEntry]:
    accounts = list_accounts()
    entries = []
    for acct in accounts:
        stats = compute_stats(acct.id)
        entries.append(LeaderboardEntry(
            account_id=acct.id,
            account_name=acct.name,
            total_pnl=round(acct.total_pnl, 2),
            total_pnl_pct=round(acct.total_pnl_pct, 2),
            win_rate=stats.win_rate,
            profit_factor=stats.profit_factor,
            total_trades=stats.total_trades,
            current_balance=round(acct.current_balance, 2),
        ))
    entries.sort(key=lambda e: e.total_pnl, reverse=True)
    return entries[:limit]
