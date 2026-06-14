from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_supabase
from services.calibration.models import (
    TradeRecord,
    TradeOutcome,
    CalibrationData,
    BucketStats,
    BucketLabel,
    BUCKET_DEFS,
    bucket_for_score,
    CalibrationResult,
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


class CalibrationStore:
    """Supabase-backed store for calibration trade records."""

    _instance: Optional["CalibrationStore"] = None
    _min_samples: int = 10

    def __init__(self):
        self._min_samples = 10

    @classmethod
    def get_instance(cls) -> "CalibrationStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_trade(self, record: TradeRecord) -> None:
        supabase = get_supabase()
        supabase.table("calibration_trades").insert({
            "trade_id": record.trade_id or None,
            "symbol": record.symbol,
            "raw_score": record.raw_score,
            "outcome": record.outcome.value,
            "profit_loss": record.profit_loss,
            "fees": record.fees,
            "direction": record.direction,
            "bucket": record.bucket or bucket_for_score(record.raw_score).value,
        }).execute()

    def clear_records(self) -> None:
        supabase = get_supabase()
        supabase.table("calibration_trades").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    def _load_records(self) -> List[TradeRecord]:
        supabase = get_supabase()
        resp = supabase.table("calibration_trades").select("*").order("timestamp", desc=True).execute()
        result = []
        for r in (resp.data or []):
            outcome = TradeOutcome(r["outcome"]) if isinstance(r.get("outcome"), str) else TradeOutcome.BREAK_EVEN
            result.append(TradeRecord(
                trade_id=r.get("trade_id", ""),
                symbol=r.get("symbol", ""),
                raw_score=r.get("raw_score", 0),
                outcome=outcome,
                profit_loss=r.get("profit_loss", 0.0),
                fees=r.get("fees", 0.0),
                direction=r.get("direction", "neutral"),
                bucket=r.get("bucket", ""),
            ))
        return result

    def calibrate_scores(self, scores: List[int], min_samples: Optional[int] = None) -> List[CalibrationResult]:
        records = self._load_records()
        min_samp = min_samples or self._min_samples

        bucket_records: dict[str, list[TradeRecord]] = {}
        for rec in records:
            b = rec.bucket or bucket_for_score(rec.raw_score).value
            bucket_records.setdefault(b, []).append(rec)

        bucket_stats: dict[str, BucketStats] = {}
        for label, lo, hi in BUCKET_DEFS:
            bucket = label.value
            recs = bucket_records.get(bucket, [])
            total = len(recs)
            wins = sum(1 for r in recs if r.outcome == TradeOutcome.WIN)
            losses = sum(1 for r in recs if r.outcome == TradeOutcome.LOSS)
            break_even = sum(1 for r in recs if r.outcome == TradeOutcome.BREAK_EVEN)
            total_return = sum(r.profit_loss for r in recs)
            total_fees = sum(r.fees for r in recs)
            win_rate = (wins / total * 100) if total > 0 else 0
            loss_rate = (losses / total * 100) if total > 0 else 0
            avg_return = total_return / total if total > 0 else 0
            gross_profit = sum(r.profit_loss for r in recs if r.profit_loss > 0)
            gross_loss = abs(sum(r.profit_loss for r in recs if r.profit_loss < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)

            blended_win_rate = win_rate if total >= 5 else (win_rate * 0.7 + 50 * 0.3)
            adjusted_conf = blended_win_rate if total >= min_samp else blended_win_rate * 0.8

            bucket_stats[bucket] = BucketStats(
                label=bucket,
                min_score=lo,
                max_score=hi,
                trade_count=total,
                wins=wins,
                losses=losses,
                break_even=break_even,
                win_rate=round(win_rate, 2),
                loss_rate=round(loss_rate, 2),
                total_return=round(total_return, 2),
                total_fees=round(total_fees, 2),
                avg_return=round(avg_return, 2),
                profit_factor=round(profit_factor, 2),
                expected_return=round(avg_return * (win_rate / 100) - abs(avg_return) * (loss_rate / 100), 2),
                adjusted_win_rate=round(blended_win_rate, 2),
                adjusted_confidence=round(adjusted_conf, 2),
            )

        results = []
        for score in scores:
            b = bucket_for_score(score)
            stats = bucket_stats.get(b.value)
            if stats and stats.trade_count > 0:
                calibrated = int(stats.adjusted_confidence) if stats.trade_count >= min_samp else int(stats.adjusted_confidence * 0.8)
                results.append(CalibrationResult(
                    raw_score=score,
                    calibrated_score=calibrated,
                    bucket_label=stats.label,
                    bucket_win_rate=stats.win_rate,
                    sample_size=stats.trade_count,
                    has_sufficient_data=stats.trade_count >= min_samp,
                    calibrated_confidence=calibrated,
                ))
            else:
                results.append(CalibrationResult(
                    raw_score=score,
                    calibrated_score=score,
                    bucket_label=b.value,
                    bucket_win_rate=0.0,
                    sample_size=0,
                    has_sufficient_data=False,
                    calibrated_confidence=score,
                ))

        return results

    def compute_calibration(self, min_samples: int = 10) -> CalibrationData:
        records = self._load_records()
        overall = len(records)
        overall_wins = sum(1 for r in records if r.outcome == TradeOutcome.WIN)
        overall_win_rate = (overall_wins / overall * 100) if overall > 0 else 0

        bucket_records: dict[str, list[TradeRecord]] = {}
        for rec in records:
            b = rec.bucket or bucket_for_score(rec.raw_score).value
            bucket_records.setdefault(b, []).append(rec)

        buckets = []
        for label, lo, hi in BUCKET_DEFS:
            bucket = label.value
            recs = bucket_records.get(bucket, [])
            total = len(recs)
            wins = sum(1 for r in recs if r.outcome == TradeOutcome.WIN)
            losses = sum(1 for r in recs if r.outcome == TradeOutcome.LOSS)
            break_even = sum(1 for r in recs if r.outcome == TradeOutcome.BREAK_EVEN)
            total_return = sum(r.profit_loss for r in recs)
            total_fees = sum(r.fees for r in recs)
            win_rate = (wins / total * 100) if total > 0 else 0
            loss_rate = (losses / total * 100) if total > 0 else 0
            avg_return = total_return / total if total > 0 else 0
            gross_profit = sum(r.profit_loss for r in recs if r.profit_loss > 0)
            gross_loss = abs(sum(r.profit_loss for r in recs if r.profit_loss < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)

            blended_win_rate = win_rate if total >= 5 else (win_rate * 0.7 + 50 * 0.3)
            adjusted_conf = blended_win_rate if total >= min_samples else blended_win_rate * 0.8

            buckets.append(BucketStats(
                label=bucket,
                min_score=lo,
                max_score=hi,
                trade_count=total,
                wins=wins,
                losses=losses,
                break_even=break_even,
                win_rate=round(win_rate, 2),
                loss_rate=round(loss_rate, 2),
                total_return=round(total_return, 2),
                total_fees=round(total_fees, 2),
                avg_return=round(avg_return, 2),
                profit_factor=round(profit_factor, 2),
                expected_return=round(avg_return * (win_rate / 100) - abs(avg_return) * (loss_rate / 100), 2),
                adjusted_win_rate=round(blended_win_rate, 2),
                adjusted_confidence=round(adjusted_conf, 2),
            ))

        return CalibrationData(
            buckets=buckets,
            total_trades=overall,
            overall_win_rate=round(overall_win_rate, 2),
            last_updated=int(datetime.now(timezone.utc).timestamp() * 1000),
            min_samples_required=min_samples,
        )
