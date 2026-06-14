
"""
Signal Engine and Signal Center.

Generates validated signals from the Master AI Decision Engine,
stores them in SQLite, and provides history, performance tracking,
filtering, and search.

Signal types:
- Strong Buy: bullish, confidence >= 80
- Buy: bullish, confidence >= 70
- Sell: bearish, confidence >= 70
- Strong Sell: bearish, confidence >= 80
- Neutral: all other cases

Rules:
- Score below 70: No signal generated (No Trade)
- All signals stored with validation status
"""

from services.signals.engine import SignalGenerator
from services.signals.models import (
    SignalRecord,
    SignalType,
    SignalStatus,
    ValidationStatus,
    SignalPerformance,
    SignalCreateRequest,
    SignalUpdateRequest,
)
from services.signals.db import (
    save_signal,
    get_signal,
    list_signals,
    update_signal,
    delete_signal,
    get_performance,
)

__all__ = [
    "SignalGenerator",
    "SignalRecord",
    "SignalType",
    "SignalStatus",
    "ValidationStatus",
    "SignalPerformance",
    "SignalCreateRequest",
    "SignalUpdateRequest",
    "save_signal",
    "get_signal",
    "list_signals",
    "update_signal",
    "delete_signal",
    "get_performance",
]
