"""Scoring Engine — converts AI observations into trade decisions using weighted logic."""

from services.vision.models import VisionObservation, ScoredTrade, ScoringDetail

# Weights per component (total = 100)
WEIGHTS = {
    "marketStructure": 30,
    "liquidity": 25,
    "momentum": 15,
    "trend": 15,
    "volume": 10,
    "confluence": 5,
}


def _parse_price(s: str) -> float:
    """Extract numeric price from a price string like '67250-67300' or '67180'."""
    import re
    m = re.search(r"[\d,.]+", s.replace(",", ""))
    return float(m.group(0)) if m else 0.0


def _calc_rr(entry: float, sl: float, tp1: float, tp2: float) -> str:
    """Calculate risk/reward ratio string."""
    if not entry or not sl:
        return ""
    risk = abs(entry - sl)
    if risk == 0:
        return ""
    r1 = abs(tp1 - entry) / risk if tp1 else 0
    r2 = abs(tp2 - entry) / risk if tp2 else 0
    best_rr = max(r1, r2)
    if best_rr >= 1:
        return f"1:{best_rr:.1f}"
    return f"1:{best_rr:.1f}"


def score_observation(obs: VisionObservation) -> ScoredTrade:
    """Apply weighted logic to AI observations and return a scored trade decision."""
    if obs.quality == "UNREADABLE_CHART":
        return ScoredTrade(
            signal="NEUTRAL",
            confidence=0,
            bullScore=0,
            bearScore=0,
            scoring=ScoringDetail(),
        )

    # --- Market Structure (30%) ---
    ms_bull, ms_bear = {
        "HH_HL": (90, 10),
        "LH_LL": (10, 90),
        "HH_LL": (50, 50),
        "LH_HL": (50, 50),
        "ranging": (40, 40),
    }.get(obs.marketStructure, (50, 50))

    # --- Liquidity (25%) ---
    liq_bull, liq_bear = {
        "above_highs": (30, 70),
        "below_lows": (70, 30),
        "both": (50, 50),
        "none": (45, 45),
    }.get(obs.liquidity, (50, 50))

    # --- Trend (15%) ---
    tr_bull, tr_bear = {
        "bullish": (85, 15),
        "bearish": (15, 85),
        "neutral": (45, 45),
    }.get(obs.trend, (50, 50))

    # --- Momentum (15%) — amplifies trend direction ---
    is_bullish_trend = obs.trend == "bullish"
    m_bull, m_bear = {
        "strong": (80, 20),
        "moderate": (60, 40),
        "weak": (40, 60),
    }.get(obs.momentum, (50, 50))
    if not is_bullish_trend and obs.trend != "neutral":
        m_bull, m_bear = m_bear, m_bull
    elif obs.trend == "neutral":
        m_bull, m_bear = 50, 50

    # --- Volume (10%) — confirm signal, no directional bias ---
    vol_mult = {"high": 1.2, "medium": 1.0, "low": 0.8}.get(obs.volume, 1.0)
    v_bull = min(50 * vol_mult, 100)
    v_bear = min(50 * vol_mult, 100)

    # --- Confluence (5%) — alignment check ---
    c_bull = int((ms_bull + tr_bull + m_bull) / 3)
    c_bear = int((ms_bear + tr_bear + m_bear) / 3)

    # Weighted sum
    raw_bull = (
        ms_bull * WEIGHTS["marketStructure"]
        + liq_bull * WEIGHTS["liquidity"]
        + tr_bull * WEIGHTS["trend"]
        + m_bull * WEIGHTS["momentum"]
        + v_bull * WEIGHTS["volume"]
        + c_bull * WEIGHTS["confluence"]
    ) / 100.0
    raw_bear = (
        ms_bear * WEIGHTS["marketStructure"]
        + liq_bear * WEIGHTS["liquidity"]
        + tr_bear * WEIGHTS["trend"]
        + m_bear * WEIGHTS["momentum"]
        + v_bear * WEIGHTS["volume"]
        + c_bear * WEIGHTS["confluence"]
    ) / 100.0

    # Apply AI confidence as a modifier (0.0–1.0)
    confidence_mod = obs.confidence / 100.0
    bull_score = raw_bull * (0.5 + 0.5 * confidence_mod)
    bear_score = raw_bear * (0.5 + 0.5 * confidence_mod)

    # Normalize to 0–100
    bull_score = min(int(round(bull_score)), 100)
    bear_score = min(int(round(bear_score)), 100)

    # Determine signal
    diff = bull_score - bear_score
    threshold = 8
    if diff >= 30:
        signal = "STRONG_LONG"
    elif diff >= threshold:
        signal = "LONG"
    elif diff <= -30:
        signal = "STRONG_SHORT"
    elif diff <= -threshold:
        signal = "SHORT"
    else:
        signal = "NEUTRAL"

    # Final confidence = max(bull, bear) with boost for strong signals
    final_conf = max(bull_score, bear_score)
    if signal in ("STRONG_LONG", "STRONG_SHORT"):
        final_conf = min(final_conf + 5, 100)

    # Risk / reward from entry/SL/TP
    entry = _parse_price(obs.entry_zone)
    sl = _parse_price(obs.invalidation)
    tp1 = _parse_price(obs.target_1)
    tp2 = _parse_price(obs.target_2)
    rr = _calc_rr(entry, sl, tp1, tp2)

    # Per-component scores for frontend display
    scoring = ScoringDetail(
        marketStructure=ms_bull if signal in ("LONG", "STRONG_LONG") else ms_bear,
        liquidity=liq_bull if signal in ("LONG", "STRONG_LONG") else liq_bear,
        momentum=m_bull if signal in ("LONG", "STRONG_LONG") else m_bear,
        trend=tr_bull if signal in ("LONG", "STRONG_LONG") else tr_bear,
        volume=int(v_bull),
        confluence=c_bull if signal in ("LONG", "STRONG_LONG") else c_bear,
        bullScore=bull_score,
        bearScore=bear_score,
        overall=int(round((bull_score + bear_score) / 2)),
    )

    return ScoredTrade(
        signal=signal,
        confidence=final_conf,
        bullScore=bull_score,
        bearScore=bear_score,
        entry_zone=obs.entry_zone,
        stop_loss=obs.invalidation,
        take_profit_1=obs.target_1,
        take_profit_2=obs.target_2,
        risk_reward=rr,
        scoring=scoring,
    )
