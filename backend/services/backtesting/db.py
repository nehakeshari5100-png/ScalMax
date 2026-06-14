from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from app.database import get_supabase
from services.backtesting.models import BacktestResult


def save_result(result: BacktestResult) -> None:
    rid = result.id or str(uuid4())
    result.id = rid

    config_dict = result.config.model_dump()
    result_dict = result.model_dump()

    supabase = get_supabase()
    supabase.table("backtest_results").upsert({
        "id": rid,
        "config": config_dict,
        "result": result_dict,
        "symbol": result.config.symbol,
        "timeframe": result.config.timeframe,
        "strategy_version": result.config.strategy_version,
        "net_profit": result.metrics.net_profit,
        "win_rate": result.metrics.win_rate,
        "sharpe_ratio": result.metrics.sharpe_ratio,
        "max_drawdown_pct": result.metrics.max_drawdown_pct,
        "total_trades": result.metrics.total_trades,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def load_result(rid: str) -> Optional[BacktestResult]:
    supabase = get_supabase()
    resp = supabase.table("backtest_results").select("result").eq("id", rid).maybe_single().execute()
    if resp.data and resp.data.get("result"):
        return BacktestResult(**resp.data["result"])
    return None


def list_results(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    strategy_version: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[BacktestResult], int]:
    supabase = get_supabase()
    query = supabase.table("backtest_results").select("*", count="exact")

    if symbol:
        query = query.eq("symbol", symbol)
    if timeframe:
        query = query.eq("timeframe", timeframe)
    if strategy_version:
        query = query.eq("strategy_version", strategy_version)

    resp = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    total = resp.count or 0
    results = []
    for row in (resp.data or []):
        if row.get("result"):
            results.append(BacktestResult(**row["result"]))
    return results, total


def delete_result(rid: str) -> bool:
    supabase = get_supabase()
    resp = supabase.table("backtest_results").delete().eq("id", rid).execute()
    return len(resp.data or []) > 0
