import re
from services.vision.models import VisionObservation, ScoredTrade, ScoringDetail, RiskAssessment

WEIGHTS = {
    "marketStructure": 30,
    "liquidity": 25,
    "trend": 20,
    "momentum": 15,
    "confluence": 10,
}


def _evidence_check(obs: VisionObservation, signal: str) -> tuple[str, str]:
    """
    Enforce hard evidence-check rules derived from observations.
    - HH + HL → SHORT is FORBIDDEN (via marketStructure or explicit booleans)
    - LH + LL → LONG is FORBIDDEN
    - Ranging → forced NEUTRAL
    - Unclear structure + low confidence → NEUTRAL forced
    """
    # Use explicit boolean fields if available, fall back to marketStructure
    has_hh = obs.isHigherHighs is True
    has_hl = obs.isHigherLows is True
    has_lh = obs.isLowerHighs is True
    has_ll = obs.isLowerLows is True

    bull_structure = has_hh and has_hl
    bear_structure = has_lh and has_ll

    # Fallback to marketStructure if boolean fields are not set
    if obs.isHigherHighs is None:
        bull_structure = obs.marketStructure in ("HH_HL", "HH_LL") and obs.trend == "bullish"
        bear_structure = obs.marketStructure in ("LH_LL", "LH_HL") and obs.trend == "bearish"

    strong_bearish_evidence = obs.confluence == "resistance" or obs.liquidity == "above_highs"
    strong_bullish_evidence = obs.confluence == "support" or obs.liquidity == "below_lows"

    reason = ""

    # PHASE 4 rule: HH+HL → SHORT forbidden, LH+LL → LONG forbidden
    if bull_structure and signal in ("SHORT", "STRONG_SHORT"):
        signal = "LONG"
        reason = "HH+HL detected (bullish structure). SHORT forbidden. Overridden to LONG."

    if bear_structure and signal in ("LONG", "STRONG_LONG"):
        signal = "SHORT"
        reason = "LH+LL detected (bearish structure). LONG forbidden. Overridden to SHORT."

    # PHASE 4 rule: Ranging → NO_TRADE
    if obs.marketStructure == "ranging" and signal not in ("NEUTRAL", "NO_TRADE"):
        signal = "NEUTRAL"
        if not reason:
            reason = "Market structure is ranging (no clear HH/HL/LH/LL). NO_TRADE."

    if obs.marketStructure == "unclear" and obs.confidence < 50 and signal not in ("NEUTRAL",):
        signal = "NEUTRAL"
        if not reason:
            reason = "Market structure unclear, confidence too low. No directional bias."

    return signal, reason


def _parse_price(s: str) -> float:
    m = re.search(r"[\d,.]+", s.replace(",", ""))
    return float(m.group(0)) if m else 0.0


def _calc_rr(entry: float, sl: float, tp1: float, tp2: float) -> str:
    if not entry or not sl:
        return ""
    risk = abs(entry - sl)
    if risk == 0:
        return ""
    r1 = abs(tp1 - entry) / risk if tp1 else 0
    r2 = abs(tp2 - entry) / risk if tp2 else 0
    best_rr = max(r1, r2)
    return f"1:{best_rr:.1f}"


def _score_market_structure(obs: VisionObservation) -> tuple[int, int, str]:
    score_map = {
        "HH_HL": (85, 15, "Higher highs + higher lows — bullish structure"),
        "LH_LL": (15, 85, "Lower highs + lower lows — bearish structure"),
        "HH_LL": (65, 35, "Higher highs with lower lows — bullish bias, volatile"),
        "LH_HL": (35, 65, "Lower highs with higher lows — bearish bias, compressing"),
        "ranging": (50, 50, "Price moving sideways — neutral structure"),
    }
    bull, bear, summary = score_map.get(obs.marketStructure, (50, 50, "Unclear structure"))
    return bull, bear, summary


def _score_liquidity(obs: VisionObservation) -> tuple[int, int, str]:
    ld = obs.liquidityDetails
    parts = []
    if ld.equalHighs:
        parts.append("equal highs detected above")
    if ld.equalLows:
        parts.append("equal lows detected below")
    if ld.liquiditySweeps:
        parts.append("liquidity sweep detected")
    if ld.stopHunts:
        parts.append("stop hunt detected")
    summary = "; ".join(parts) if parts else "No clear liquidity patterns"

    base_bull, base_bear = {
        "above_highs": (30, 70),
        "below_lows": (70, 30),
        "both": (50, 50),
        "none": (45, 45),
    }.get(obs.liquidity, (50, 50))

    sweep_bonus = 0
    if ld.liquiditySweeps and base_bear > base_bull:
        sweep_bonus = 10
    elif ld.liquiditySweeps and base_bull > base_bear:
        sweep_bonus = 10
    if ld.stopHunts:
        sweep_bonus += 5

    if base_bull > base_bear:
        bull = min(base_bull + sweep_bonus, 95)
        bear = max(base_bear - sweep_bonus, 5)
    else:
        bull = max(base_bull - sweep_bonus, 5)
        bear = min(base_bear + sweep_bonus, 95)

    return bull, bear, summary


def _score_trend(obs: VisionObservation) -> tuple[int, int, str]:
    score_map = {
        "bullish": (85, 15, "Uptrend — higher timeframe bias is bullish"),
        "bearish": (15, 85, "Downtrend — higher timeframe bias is bearish"),
        "neutral": (50, 50, "Sideways — no clear directional bias"),
    }
    bull, bear, summary = score_map.get(obs.trend, (50, 50, "Unclear trend"))
    return bull, bear, summary


def _score_momentum(obs: VisionObservation) -> tuple[int, int, str]:
    base = {
        "strong": (80, 20),
        "moderate": (60, 40),
        "weak": (40, 60),
    }.get(obs.momentum, (50, 50))
    bull, bear = base
    if obs.trend == "bullish":
        summary = f"{obs.momentum} momentum in direction of trend"
    elif obs.trend == "bearish":
        bull, bear = bear, bull
        summary = f"{obs.momentum} momentum in direction of trend"
    else:
        bull, bear = 50, 50
        summary = "neutral momentum"
    return bull, bear, summary


def _score_confluence(obs: VisionObservation) -> tuple[int, int, str]:
    score_map = {
        "support": (80, 20, "Price respecting support level — bullish confluence"),
        "resistance": (20, 80, "Price rejecting at resistance — bearish confluence"),
        "breakout": (75, 25, "Price breaking key level — directional confluence"),
        "rejection": (70, 30, "Wick rejection at key level — reversal confluence"),
        "none": (50, 50, "No clear confluence levels"),
    }
    bull, bear, summary = score_map.get(obs.confluence, (50, 50, "Unclear confluence"))
    return bull, bear, summary


def _calculate_risk_assessment(entry: float, sl: float, tp1: float, tp2: float,
                               account_size: float = 10000.0, risk_pct: float = 1.5) -> RiskAssessment:
    if not entry or not sl or account_size <= 0:
        return RiskAssessment()
    risk_amount = account_size * (risk_pct / 100.0)
    entry_risk_pct = abs((entry - sl) / entry) * 100.0
    if entry_risk_pct == 0:
        return RiskAssessment(accountSize=account_size, riskPercent=risk_pct, riskAmount=risk_amount)
    position_size = risk_amount / (entry_risk_pct / 100.0)
    quantity = position_size / entry
    max_loss = risk_amount
    pnl1 = abs(tp1 - entry) * quantity if tp1 else 0
    pnl2 = abs(tp2 - entry) * quantity if tp2 else 0
    expected_profit = pnl1 + pnl2
    rr = _calc_rr(entry, sl, tp1, tp2)

    return RiskAssessment(
        accountSize=account_size,
        riskPercent=risk_pct,
        riskAmount=round(risk_amount, 2),
        positionSize=round(position_size, 2),
        maxLoss=round(max_loss, 2),
        expectedProfit=round(expected_profit, 2),
        riskRewardRatio=rr,
    )


def _validate_prices(obs: VisionObservation) -> tuple[str, str, str, str]:
    """Validate entry/SL/TP against detected current price. Clear unrealistic values."""
    if not obs.detectedCurrentPrice:
        return obs.entry_zone, obs.invalidation, obs.target_1, obs.target_2

    current = _parse_price(obs.detectedCurrentPrice)
    if current == 0:
        return obs.entry_zone, obs.invalidation, obs.target_1, obs.target_2

    entry = _parse_price(obs.entry_zone)
    sl = _parse_price(obs.invalidation)
    tp1 = _parse_price(obs.target_1)
    tp2 = _parse_price(obs.target_2)

    entry_zone = obs.entry_zone
    invalidation = obs.invalidation
    target_1 = obs.target_1
    target_2 = obs.target_2

    if entry and abs(entry - current) / current > 0.15:
        entry_zone = ""
    if sl and abs(sl - current) / current > 0.25:
        invalidation = ""
    if tp1 and abs(tp1 - current) / current > 0.50:
        target_1 = ""
    if tp2 and abs(tp2 - current) / current > 0.50:
        target_2 = ""

    return entry_zone, invalidation, target_1, target_2


def score_observation(obs: VisionObservation,
                      account_size: float = 10000.0,
                      risk_pct: float = 1.5) -> ScoredTrade:
    # PHASE 2 gate: OCR confidence too low
    if obs.ocrConfidence < 80:
        reason = f"OCR confidence too low ({obs.ocrConfidence}%). Chart details not reliably readable."
        if obs.reason:
            reason = f"{reason} {obs.reason}"
        return ScoredTrade(
            signal="NO_TRADE",
            confidence=0,
            bullScore=0,
            bearScore=0,
            reason=reason,
            scoring=ScoringDetail(),
        )

    # PHASE 1 gate: chart quality too low
    if obs.quality == "UNREADABLE_CHART":
        return ScoredTrade(
            signal="NO_TRADE",
            confidence=0,
            bullScore=0,
            bearScore=0,
            reason="Chart is unreadable",
            scoring=ScoringDetail(),
        )

    ms_bull, ms_bear, ms_summary = _score_market_structure(obs)
    liq_bull, liq_bear, liq_summary = _score_liquidity(obs)
    tr_bull, tr_bear, tr_summary = _score_trend(obs)
    m_bull, m_bear, mom_summary = _score_momentum(obs)
    c_bull, c_bear, conf_summary = _score_confluence(obs)

    raw_bull = (
        ms_bull * WEIGHTS["marketStructure"]
        + liq_bull * WEIGHTS["liquidity"]
        + tr_bull * WEIGHTS["trend"]
        + m_bull * WEIGHTS["momentum"]
        + c_bull * WEIGHTS["confluence"]
    ) / 100.0
    raw_bear = (
        ms_bear * WEIGHTS["marketStructure"]
        + liq_bear * WEIGHTS["liquidity"]
        + tr_bear * WEIGHTS["trend"]
        + m_bear * WEIGHTS["momentum"]
        + c_bear * WEIGHTS["confluence"]
    ) / 100.0

    bull_score = min(int(round(raw_bull)), 100)
    bear_score = min(int(round(raw_bear)), 100)

    diff = bull_score - bear_score
    if diff >= 30:
        signal = "STRONG_LONG"
    elif diff >= 10:
        signal = "LONG"
    elif diff <= -30:
        signal = "STRONG_SHORT"
    elif diff <= -10:
        signal = "SHORT"
    else:
        signal = "NEUTRAL"

    # Evidence check: enforce observation-driven rules
    signal, evidence_reason = _evidence_check(obs, signal)

    # PHASE 4: Ranging → NO_TRADE
    if obs.marketStructure == "ranging":
        signal = "NO_TRADE"
        if not evidence_reason:
            evidence_reason = "Market structure is ranging (no clear HH/HL/LH/LL). No trade."

    # NO_TRADE if confidence from AI is too low or signal ended up NEUTRAL on unclear chart
    if signal == "NEUTRAL" and obs.confidence < 30:
        signal = "NO_TRADE"
        if not evidence_reason:
            evidence_reason = "Confidence too low."

    # PHASE 5: Price validation — reject unrealistic entry/SL/TP vs detected current price
    validated_entry, validated_sl, validated_tp1, validated_tp2 = _validate_prices(obs)

    # If all entry/SL/TP were rejected and signal is directional, downgrade
    if signal in ("LONG", "STRONG_LONG", "SHORT", "STRONG_SHORT"):
        has_valid_prices = bool(validated_entry or validated_sl or validated_tp1 or validated_tp2)
        if not has_valid_prices:
            signal = "NEUTRAL"
            evidence_reason = (evidence_reason + " | " if evidence_reason else "") + "Prices rejected by validation."
            if obs.confidence < 30:
                signal = "NO_TRADE"

    if signal in ("STRONG_LONG", "STRONG_SHORT"):
        final_conf = max(bull_score, bear_score) + 5
    elif signal in ("LONG", "SHORT"):
        final_conf = max(bull_score, bear_score)
    else:
        final_conf = max(bull_score, bear_score)
    final_conf = min(final_conf, 100)

    if final_conf >= 85:
        risk_summary = "High confidence — standard position sizing"
    elif final_conf >= 70:
        risk_summary = "Medium confidence — consider reduced position size"
    elif final_conf >= 50:
        risk_summary = "Low confidence — caution advised, reduce risk exposure"
    else:
        risk_summary = "No trade — confidence too low"

    # Build reason string from AI reason + evidence check + observation details + OCR metadata
    reason_parts = []
    ocr_parts = []
    if obs.detectedSymbol:
        ocr_parts.append(f"Symbol:{obs.detectedSymbol}")
    if obs.detectedTimeframe:
        ocr_parts.append(f"TF:{obs.detectedTimeframe}")
    if obs.detectedCurrentPrice:
        ocr_parts.append(f"Price:{obs.detectedCurrentPrice}")
    if obs.detectedExchange:
        ocr_parts.append(f"Exch:{obs.detectedExchange}")
    if ocr_parts:
        reason_parts.append("[" + " | ".join(ocr_parts) + "]")
    if obs.reason:
        reason_parts.append(obs.reason)
    if evidence_reason:
        reason_parts.append(evidence_reason)
    final_reason = " | ".join(reason_parts) if reason_parts else "Analysis based on chart observation"

    entry = _parse_price(validated_entry or obs.entry_zone)
    sl = _parse_price(validated_sl or obs.invalidation)
    tp1 = _parse_price(validated_tp1 or obs.target_1)
    tp2 = _parse_price(validated_tp2 or obs.target_2)
    rr = _calc_rr(entry, sl, tp1, tp2)

    risk_assessment = _calculate_risk_assessment(entry, sl, tp1, tp2, account_size, risk_pct)

    scoring = ScoringDetail(
        marketStructure=ms_bull if signal in ("LONG", "STRONG_LONG") else ms_bear,
        liquidity=liq_bull if signal in ("LONG", "STRONG_LONG") else liq_bear,
        momentum=m_bull if signal in ("LONG", "STRONG_LONG") else m_bear,
        trend=tr_bull if signal in ("LONG", "STRONG_LONG") else tr_bear,
        volume=50,
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
        entry_zone=validated_entry or obs.entry_zone,
        stop_loss=validated_sl or obs.invalidation,
        take_profit_1=validated_tp1 or obs.target_1,
        take_profit_2=validated_tp2 or obs.target_2,
        risk_reward=rr,
        reason=final_reason,
        marketStructureSummary=ms_summary,
        liquiditySummary=liq_summary,
        riskSummary=risk_summary,
        riskAssessment=risk_assessment,
        scoring=scoring,
    )
