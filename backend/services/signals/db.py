from typing import List, Optional, Tuple
from datetime import datetime, timezone

from app.database import get_supabase
from services.signals.models import (
    SignalRecord,
    SignalType,
    SignalStatus,
    ValidationStatus,
    SignalPerformance,
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _signal_to_row(signal: SignalRecord) -> dict:
    return {
        "id": signal.id,
        "symbol": signal.symbol,
        "timeframe": signal.timeframe,
        "exchange": signal.exchange,
        "signal_type": signal.signal_type.value if isinstance(signal.signal_type, SignalType) else signal.signal_type,
        "direction": signal.direction,
        "entry": signal.entry,
        "stop_loss": signal.stop_loss,
        "take_profit_1": signal.take_profit_1,
        "take_profit_2": signal.take_profit_2,
        "risk_reward_1": signal.risk_reward_1,
        "risk_reward_2": signal.risk_reward_2,
        "confidence": signal.confidence,
        "confluence_score": signal.confluence_score,
        "reasoning": signal.reasoning,
        "reasons": signal.reasons,
        "risks": signal.risks,
        "status": signal.status.value if isinstance(signal.status, SignalStatus) else signal.status,
        "validation_status": signal.validation_status.value if isinstance(signal.validation_status, ValidationStatus) else signal.validation_status,
        "strategy_version": signal.strategy_version,
        "session": signal.session,
        "created_at": datetime.fromtimestamp(signal.created_at / 1000, tz=timezone.utc).isoformat() if signal.created_at else _ts(),
        "updated_at": datetime.fromtimestamp(signal.updated_at / 1000, tz=timezone.utc).isoformat() if signal.updated_at else _ts(),
        "triggered_at": datetime.fromtimestamp(signal.triggered_at / 1000, tz=timezone.utc).isoformat() if signal.triggered_at else None,
        "completed_at": datetime.fromtimestamp(signal.completed_at / 1000, tz=timezone.utc).isoformat() if signal.completed_at else None,
        "pnl": signal.pnl,
        "pnl_pct": signal.pnl_pct,
        "outcome": signal.outcome,
    }


def _parse_ts(val) -> int:
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    return int(datetime.fromisoformat(val).timestamp() * 1000)


def _row_to_signal(row: dict) -> SignalRecord:
    d = dict(row)
    if isinstance(d.get("status"), str):
        d["status"] = SignalStatus(d["status"])
    if isinstance(d.get("validation_status"), str):
        d["validation_status"] = ValidationStatus(d["validation_status"])
    d["created_at"] = _parse_ts(d.get("created_at"))
    d["updated_at"] = _parse_ts(d.get("updated_at"))
    d["triggered_at"] = _parse_ts(d.get("triggered_at"))
    d["completed_at"] = _parse_ts(d.get("completed_at"))
    return SignalRecord(**d)


def save_signal(signal: SignalRecord) -> SignalRecord:
    supabase = get_supabase()
    supabase.table("signals").upsert(_signal_to_row(signal)).execute()
    return signal


def get_signal(signal_id: str) -> Optional[SignalRecord]:
    supabase = get_supabase()
    resp = supabase.table("signals").select("*").eq("id", signal_id).maybe_single().execute()
    if resp.data:
        return _row_to_signal(resp.data)
    return None


def list_signals(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    min_confidence: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[SignalRecord], int]:
    supabase = get_supabase()
    query = supabase.table("signals").select("*", count="exact")

    if symbol:
        query = query.eq("symbol", symbol)
    if timeframe:
        query = query.eq("timeframe", timeframe)
    if signal_type:
        query = query.eq("signal_type", signal_type)
    if status:
        query = query.eq("status", status)
    if direction:
        query = query.eq("direction", direction)
    if min_confidence is not None:
        query = query.gte("confidence", min_confidence)
    if search:
        query = query.or_(f"symbol.ilike.%{search}%,reasoning.ilike.%{search}%")

    offset = (page - 1) * page_size
    resp = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

    signals = [_row_to_signal(r) for r in (resp.data or [])]
    return signals, resp.count or 0


def update_signal(
    signal_id: str,
    status: Optional[str] = None,
    validation_status: Optional[str] = None,
    pnl: Optional[float] = None,
    pnl_pct: Optional[float] = None,
    outcome: Optional[str] = None,
) -> None:
    supabase = get_supabase()
    updates = {"updated_at": _ts()}
    if status is not None:
        updates["status"] = status
    if validation_status is not None:
        updates["validation_status"] = validation_status
    if pnl is not None:
        updates["pnl"] = pnl
    if pnl_pct is not None:
        updates["pnl_pct"] = pnl_pct
    if outcome is not None:
        updates["outcome"] = outcome
    supabase.table("signals").update(updates).eq("id", signal_id).execute()


def delete_signal(signal_id: str) -> bool:
    supabase = get_supabase()
    resp = supabase.table("signals").delete().eq("id", signal_id).execute()
    return len(resp.data or []) > 0


def get_performance(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> SignalPerformance:
    supabase = get_supabase()
    query = supabase.table("signals").select("*")
    if symbol:
        query = query.eq("symbol", symbol)
    if timeframe:
        query = query.eq("timeframe", timeframe)
    resp = query.execute()

    rows = resp.data or []
    total = len(rows)
    if total == 0:
        return SignalPerformance()

    active = sum(1 for r in rows if r.get("status") == "active")
    completed = sum(1 for r in rows if r.get("status") == "completed")
    cancelled = sum(1 for r in rows if r.get("status") == "cancelled")
    expired = sum(1 for r in rows if r.get("status") == "expired")
    triggered = sum(1 for r in rows if r.get("status") == "triggered")

    with_pnl = [r for r in rows if r.get("pnl") is not None]
    won = [r for r in with_pnl if r["pnl"] > 0]
    lost = [r for r in with_pnl if r["pnl"] < 0]
    be = [r for r in with_pnl if r["pnl"] == 0]

    wins = len(won)
    losses = len(lost)
    win_rate = (wins / len(with_pnl)) * 100 if with_pnl else 0
    total_pnl = sum(r.get("pnl", 0) for r in rows)
    gross_profit = sum(r["pnl"] for r in won)
    gross_loss = abs(sum(r["pnl"] for r in lost))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
    avg_pnl = total_pnl / len(with_pnl) if with_pnl else 0

    confidences = [r.get("confidence", 0) for r in rows if r.get("confidence") is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    by_type: dict = {}
    for r in rows:
        t = r.get("signal_type", "unknown")
        if t not in by_type:
            by_type[t] = {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        by_type[t]["total"] += 1
        if r.get("pnl"):
            by_type[t]["wins"] += 1 if r["pnl"] > 0 else 0
            by_type[t]["losses"] += 1 if r["pnl"] < 0 else 0
            by_type[t]["pnl"] += r["pnl"]

    by_symbol: dict = {}
    for r in rows:
        s = r.get("symbol", "UNKNOWN")
        if s not in by_symbol:
            by_symbol[s] = {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        by_symbol[s]["total"] += 1
        if r.get("pnl"):
            by_symbol[s]["wins"] += 1 if r["pnl"] > 0 else 0
            by_symbol[s]["losses"] += 1 if r["pnl"] < 0 else 0
            by_symbol[s]["pnl"] += r["pnl"]

    return SignalPerformance(
        total_signals=total,
        active=active,
        completed=completed,
        cancelled=cancelled,
        expired=expired,
        triggered=triggered,
        wins=wins,
        losses=losses,
        breakeven=len(be),
        win_rate=round(win_rate, 2),
        total_pnl=round(total_pnl, 2),
        avg_pnl=round(avg_pnl, 2),
        avg_confidence=round(avg_confidence, 2),
        by_type=by_type,
        by_symbol=by_symbol,
    )
