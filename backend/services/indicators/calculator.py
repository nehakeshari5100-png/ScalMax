"""
Pure mathematical indicator calculations.
No dependencies beyond Python built-ins and math.

Every function is:
- Deterministic: same input → same output
- Stateless: no hidden state
- Vectorized for arrays of floats
"""
import math
from typing import List, Tuple, Optional


# ─── Moving Averages ─────────────────────────────────────────────

def sma(values: List[float], period: int) -> List[float]:
    """Simple Moving Average."""
    if len(values) < period or period <= 0:
        return []

    result = []
    for i in range(len(values)):
        if i < period - 1:
            continue
        result.append(sum(values[i - period + 1:i + 1]) / period)
    return result


def ema(values: List[float], period: int, smoothing: Optional[float] = None) -> List[float]:
    """Exponential Moving Average."""
    if len(values) < period or period <= 0:
        return []

    k = smoothing if smoothing is not None else (2.0 / (period + 1))
    result = []

    # Start with SMA
    init_ema = sum(values[:period]) / period
    result.append(init_ema)

    for i in range(period, len(values)):
        ema_val = (values[i] * k) + (result[-1] * (1 - k))
        result.append(ema_val)

    return result


def ema_last(values: List[float], period: int, smoothing: Optional[float] = None) -> float:
    """Calculate only the last EMA value (optimized)."""
    if len(values) < period or period <= 0:
        return 0.0

    k = smoothing if smoothing is not None else (2.0 / (period + 1))
    ema_val = sum(values[:period]) / period

    for i in range(period, len(values)):
        ema_val = (values[i] * k) + (ema_val * (1 - k))

    return ema_val


def wma(values: List[float], period: int) -> float:
    """Weighted Moving Average (most recent has highest weight)."""
    if len(values) < period or period <= 0:
        return 0.0

    recent = values[-period:]
    weight_sum = sum(w for w in range(1, period + 1))
    weighted = sum(v * w for v, w in zip(recent, range(1, period + 1)))
    return weighted / weight_sum


# ─── Momentum Indicators ─────────────────────────────────────────

def rsi(values: List[float], period: int = 14) -> List[float]:
    """Relative Strength Index."""
    if len(values) < period + 1:
        return []

    gains = []
    losses = []

    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    result = []

    for i in range(period, len(gains)):
        avg_gain = sum(gains[i - period:i]) / period
        avg_loss = sum(losses[i - period:i]) / period

        if avg_loss == 0:
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100.0 - (100.0 / (1.0 + rs))

        result.append(rsi_val)

    return result


def rsi_last(values: List[float], period: int = 14) -> float:
    """Calculate only the last RSI value (optimized)."""
    if len(values) < period + 1:
        return 50.0

    gains = []
    losses = []

    for i in range(len(values) - period, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(
    values: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[List[float], List[float], List[float]]:
    """MACD: macd_line, signal_line, histogram."""
    fast_ema = ema(values, fast_period)
    slow_ema = ema(values, slow_period)

    min_len = min(len(fast_ema), len(slow_ema))
    offset = len(slow_ema) - len(fast_ema)

    macd_line = []
    for i in range(min_len):
        macd_val = fast_ema[i] - slow_ema[i + offset] if i + offset < len(slow_ema) else 0.0
        macd_line.append(macd_val)

    signal_line = ema(macd_line, signal_period) if len(macd_line) >= signal_period else [0.0]

    # Align signal line length
    signal_offset = len(macd_line) - len(signal_line)
    histogram = []
    for i in range(len(signal_line)):
        hist_val = macd_line[i + signal_offset] - signal_line[i]
        histogram.append(hist_val)

    return macd_line, signal_line, histogram


def macd_last(
    values: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[float, float, float]:
    """Calculate only the last MACD values (optimized)."""
    if len(values) < slow_period + signal_period:
        return (0.0, 0.0, 0.0)

    fast_e = ema_last(values, fast_period)
    slow_e = ema_last(values, slow_period)

    macd_val = fast_e - slow_e

    # For signal, we need recent macd history
    macd_history = []
    for i in range(slow_period + signal_period, len(values)):
        fe = ema_last(values[:i + 1], fast_period)
        se = ema_last(values[:i + 1], slow_period)
        macd_history.append(fe - se)

    signal_v = ema_last(macd_history, signal_period) if len(macd_history) >= signal_period else 0.0
    hist_val = macd_val - signal_v

    return (macd_val, signal_v, hist_val)


def stochastic_rsi(
    values: List[float],
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_smoothing: int = 3,
    d_smoothing: int = 3,
) -> Tuple[List[float], List[float]]:
    """Stochastic RSI: returns (k_values, d_values)."""
    rsi_values = rsi(values, rsi_period)
    if len(rsi_values) < stoch_period:
        return ([], [])

    k_values = []
    for i in range(stoch_period - 1, len(rsi_values)):
        rsi_slice = rsi_values[i - stoch_period + 1:i + 1]
        min_rsi = min(rsi_slice)
        max_rsi = max(rsi_slice)

        if max_rsi == min_rsi:
            k = 50.0
        else:
            k = ((rsi_values[i] - min_rsi) / (max_rsi - min_rsi)) * 100.0

        k_values.append(k)

    d_values = []
    if len(k_values) >= d_smoothing:
        for i in range(d_smoothing - 1, len(k_values)):
            d_val = sum(k_values[i - d_smoothing + 1:i + 1]) / d_smoothing
            d_values.append(d_val)

    # Apply k smoothing
    if k_smoothing > 1 and len(k_values) >= k_smoothing:
        smoothed_k = []
        for i in range(k_smoothing - 1, len(k_values)):
            smoothed_k.append(sum(k_values[i - k_smoothing + 1:i + 1]) / k_smoothing)
        k_values = smoothed_k

    return (k_values, d_values)


def stochastic_rsi_last(
    values: List[float],
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_smoothing: int = 3,
    d_smoothing: int = 3,
) -> Tuple[float, float]:
    """Stochastic RSI last values only."""
    k, d = stochastic_rsi(values, rsi_period, stoch_period, k_smoothing, d_smoothing)
    return (k[-1] if k else 50.0, d[-1] if d else 50.0)


# ─── Volume Indicators ───────────────────────────────────────────

def vwap(closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> List[float]:
    """Volume-Weighted Average Price."""
    if not closes or not volumes or len(closes) != len(volumes):
        return []

    result = []
    cum_pv = 0.0
    cum_vol = 0.0

    for i in range(len(closes)):
        typical_price = (highs[i] + lows[i] + closes[i]) / 3.0
        cum_pv += typical_price * volumes[i]
        cum_vol += volumes[i]

        if cum_vol > 0:
            result.append(cum_pv / cum_vol)
        else:
            result.append(closes[i])

    return result


def vwap_last(closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> float:
    """VWAP last value only."""
    v = vwap(closes, highs, lows, volumes)
    return v[-1] if v else 0.0


def volume_delta(buy_volumes: List[float], sell_volumes: List[float]) -> float:
    """Calculate volume delta (buy - sell) over the period."""
    total_buy = sum(buy_volumes)
    total_sell = sum(sell_volumes)
    return total_buy - total_sell


def volume_spike_ratio(
    current_volume: float,
    recent_volumes: List[float],
    multiplier: float = 2.0,
) -> Tuple[bool, float]:
    """Detect if current volume is a spike compared to recent average."""
    if not recent_volumes:
        return (False, 0.0)

    avg_volume = sum(recent_volumes) / len(recent_volumes)
    if avg_volume <= 0:
        return (False, 0.0)

    ratio = current_volume / avg_volume
    return (ratio >= multiplier, ratio)


# ─── Volatility Indicators ───────────────────────────────────────

def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    """Average True Range."""
    if len(highs) < period + 1:
        return []

    tr_values = []
    for i in range(1, len(highs)):
        h = highs[i]
        l = lows[i]
        pc = closes[i - 1]

        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_values.append(tr)

    result = []
    if len(tr_values) < period:
        return []

    atr_val = sum(tr_values[:period]) / period
    result.append(atr_val)

    for i in range(period, len(tr_values)):
        atr_val = ((atr_val * (period - 1)) + tr_values[i]) / period
        result.append(atr_val)

    return result


def atr_last(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """ATR last value only."""
    a = atr(highs, lows, closes, period)
    return a[-1] if a else 0.0


def bollinger_bands(
    values: List[float],
    period: int = 20,
    num_std: float = 2.0,
) -> Tuple[List[float], List[float], List[float]]:
    """Bollinger Bands: upper, middle, lower."""
    middle = sma(values, period)
    if not middle:
        return ([], [], [])

    upper = []
    lower = []
    offset = period - 1

    for i, m in enumerate(middle):
        idx = offset + i
        slice_vals = values[idx - period + 1:idx + 1]

        variance = sum((v - m) ** 2 for v in slice_vals) / period
        std_dev = math.sqrt(variance)

        upper.append(m + (num_std * std_dev))
        lower.append(m - (num_std * std_dev))

    return (upper, middle, lower)


def bollinger_bands_last(
    values: List[float],
    period: int = 20,
    num_std: float = 2.0,
) -> Tuple[float, float, float, float, float]:
    """Bollinger Bands last values only: upper, middle, lower, bandwidth, %b."""
    upper, middle, lower = bollinger_bands(values, period, num_std)
    if not upper or not middle or not lower:
        return (0.0, 0.0, 0.0, 0.0, 0.0)

    u = upper[-1]
    m = middle[-1]
    lo = lower[-1]

    bandwidth = ((u - lo) / m) * 100.0 if m != 0 else 0.0
    current_price = values[-1]

    if u != lo:
        percent_b = (current_price - lo) / (u - lo)
    else:
        percent_b = 0.5

    return (u, m, lo, bandwidth, percent_b)


# ─── Scoring Functions ───────────────────────────────────────────

def trend_strength_score(
    ema9: float,
    ema20: float,
    ema50: float,
    ema200: float,
    current_price: float,
) -> Tuple[float, str, str]:
    """
    Calculate trend strength score (0.0 to 1.0).

    Scoring:
    - Price above/below EMAs
    - EMA alignment (9 > 20 > 50 > 200 for uptrend)
    - Distance between EMAs as momentum proxy
    """
    if current_price <= 0:
        return (0.0, "neutral", "Insufficient data")

    emas = [
        ("ema9", ema9),
        ("ema20", ema20),
        ("ema50", ema50),
        ("ema200", ema200),
    ]
    valid_emas = [(n, v) for n, v in emas if v > 0]
    if len(valid_emas) < 2:
        return (0.0, "neutral", "Insufficient EMAs")

    score = 0.0
    max_score = 0.0

    # 1. Price relative to EMAs (40% weight)
    active_weight = 0.4
    max_score += active_weight
    above_count = 0
    for _, v in valid_emas:
        if current_price > v:
            above_count += 1
    score += (above_count / len(valid_emas)) * active_weight

    # 2. EMA alignment (40% weight)
    align_weight = 0.4
    max_score += align_weight
    sorted_by_value = sorted(valid_emas, key=lambda x: x[1], reverse=True)
    sorted_by_period = sorted(valid_emas, key=lambda x: int(x[0].replace("ema", "")))

    # For uptrend: short EMAs should be above long EMAs
    align_score = 0.0
    checks = 0
    for i in range(len(sorted_by_period)):
        for j in range(i + 1, len(sorted_by_period)):
            short_ema = sorted_by_period[i]
            long_ema = sorted_by_period[j]
            if short_ema[1] > long_ema[1]:
                align_score += 1.0
            elif short_ema[1] < long_ema[1]:
                align_score -= 0.3
            checks += 1

    if checks > 0:
        align_factor = align_score / checks
        score += (align_factor + 1.0) / 2.0 * align_weight

    # 3. EMA distance momentum (20% weight)
    momentum_weight = 0.2
    max_score += momentum_weight
    if len(valid_emas) >= 2:
        sorted_p = sorted(valid_emas, key=lambda x: int(x[0].replace("ema", "")))
        nearest = sorted_p[0][1]
        farthest = sorted_p[-1][1]
        if farthest > 0:
            distance_pct = abs(nearest - farthest) / farthest * 100
            # Normalize: 0-5% range maps to 0-1
            momentum_val = min(distance_pct / 5.0, 1.0)

            # Distance direction tells us trend conviction
            if (nearest > farthest and current_price > nearest) or \
               (nearest < farthest and current_price < nearest):
                score += momentum_val * momentum_weight
            else:
                score += (1.0 - momentum_val) * momentum_weight * 0.5

    # Normalize
    normalized = score / max_score if max_score > 0 else 0.0
    normalized = max(0.0, min(1.0, normalized))

    # Determine direction
    above_200 = current_price > ema200 if ema200 > 0 else None
    ema_bullish = ema9 > ema20 > ema50 > ema200 if all(v > 0 for v in [ema9, ema20, ema50, ema200]) else None

    if ema_bullish is True and above_200 is not False:
        direction = "bullish"
    elif ema_bullish is False and above_200 is not True:
        direction = "bearish"
    else:
        direction = "neutral"

    if normalized >= 0.7:
        desc = f"Strong {direction} trend"
    elif normalized >= 0.4:
        desc = f"Moderate {direction} trend"
    else:
        desc = "Weak or no trend"

    return (round(normalized, 4), direction, desc)


def momentum_strength_score(rsi_val: float, macd_histogram: float, stoch_k: float) -> Tuple[float, str, str]:
    """
    Calculate momentum strength score (0.0 to 1.0).

    Combines RSI momentum, MACD momentum, and Stochastic momentum.
    """
    score = 0.0

    # 1. RSI contribution (40%)
    # RSI 50 is neutral → 0.5. 30 → 0, 70 → 1.0
    rsi_norm = rsi_val / 100.0 if rsi_val > 0 else 0.5
    score += rsi_norm * 0.4

    # 2. MACD contribution (35%)
    if macd_histogram != 0:
        # Sign and magnitude of histogram
        macd_signal = 0.5 + (macd_histogram / abs(macd_histogram)) * 0.3
        macd_signal = max(0.0, min(1.0, macd_signal))
        score += macd_signal * 0.35
    else:
        score += 0.5 * 0.35

    # 3. Stochastic contribution (25%)
    stoch_norm = stoch_k / 100.0 if stoch_k > 0 else 0.5
    score += stoch_norm * 0.25

    # Direction
    if rsi_val > 60 and macd_histogram > 0 and stoch_k > 50:
        direction = "bullish"
    elif rsi_val < 40 and macd_histogram < 0 and stoch_k < 50:
        direction = "bearish"
    elif rsi_val > 50:
        direction = "slightly_bullish"
    elif rsi_val < 50:
        direction = "slightly_bearish"
    else:
        direction = "neutral"

    if score >= 0.7:
        desc = f"Strong {direction} momentum"
    elif score >= 0.4:
        desc = f"Moderate {direction} momentum"
    else:
        desc = "Weak momentum"

    return (round(score, 4), direction, desc)


def volatility_score(atr_percent: float, bb_bandwidth: float) -> Tuple[float, str]:
    """
    Calculate volatility score (0.0 to 1.0).

    Higher score = higher volatility.
    """
    score = 0.0

    # ATR contribution (50%)
    atr_norm = min(atr_percent / 5.0, 1.0)  # 5% ATR = max
    score += atr_norm * 0.5

    # Bollinger Bandwidth contribution (50%)
    bb_norm = min(bb_bandwidth / 10.0, 1.0)  # 10% bandwidth = max
    score += bb_norm * 0.5

    score = round(score, 4)

    if score >= 0.7:
        desc = "High volatility"
    elif score >= 0.4:
        desc = "Moderate volatility"
    else:
        desc = "Low volatility"

    return (score, desc)


# ─── Normalization ───────────────────────────────────────────────

def normalize(values: List[float]) -> List[float]:
    """Min-max normalize a list of values to [0, 1]."""
    if not values:
        return []
    mn = min(values)
    mx = max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]
