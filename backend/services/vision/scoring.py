import re
from services.vision.models import VisionObservation, ScoredTrade, ScoringDetail, RiskAssessment

WEIGHTS = {
    "marketStructure": 30,
    "liquidity": 25,
    "trend": 20,
    "momentum": 15,
    "confluence": 10,
}


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


def score_observation(obs: VisionObservation,
                      account_size: float = 10000.0,
                      risk_pct: float = 1.5) -> ScoredTrade:
    if obs.quality == "UNREADABLE_CHART":
        return ScoredTrade(
            signal="NEUTRAL",
            confidence=0,
            bullScore=0,
            bearScore=0,
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

    entry = _parse_price(obs.entry_zone)
    sl = _parse_price(obs.invalidation)
    tp1 = _parse_price(obs.target_1)
    tp2 = _parse_price(obs.target_2)
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
        entry_zone=obs.entry_zone,
        stop_loss=obs.invalidation,
        take_profit_1=obs.target_1,
        take_profit_2=obs.target_2,
        risk_reward=rr,
        marketStructureSummary=ms_summary,
        liquiditySummary=liq_summary,
        riskSummary=risk_summary,
        riskAssessment=risk_assessment,
        scoring=scoring,
    )
