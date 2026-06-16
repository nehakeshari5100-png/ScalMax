from services.vision.models import MarketExtraction, TradePlan, ScoringBreakdown


def validate_extraction(extraction: MarketExtraction) -> TradePlan:
    """
    Code-level safety net on top of the AI's STEP 10-12.
    Enforces hard rules: NO_TRADE if confidence < 70, structure unclear,
    or evidence contradicts the bias.
    Never forces LONG or SHORT.
    """
    trade = extraction.trade
    ms = extraction.marketStructure
    scoring = extraction.scoring

    confidence = trade.confidence
    bias = trade.bias

    rule_violations = []

    # Rule 1: Confidence must be >= 70
    if confidence < 70 and bias in ("LONG", "SHORT"):
        rule_violations.append(f"Confidence {confidence} < 70. NO_TRADE enforced.")

    # Rule 2: Ranging structure → NO_TRADE
    if ms.classification == "range" and bias in ("LONG", "SHORT"):
        rule_violations.append("Market structure is ranging. NO_TRADE enforced.")

    # Rule 3: HH+HL should not be SHORT
    if ms.higherHighs and ms.higherLows and bias == "SHORT":
        rule_violations.append("HH+HL (bullish structure). SHORT not allowed. NO_TRADE.")

    # Rule 4: LH+LL should not be LONG
    if ms.lowerHighs and ms.lowerLows and bias == "LONG":
        rule_violations.append("LH+LL (bearish structure). LONG not allowed. NO_TRADE.")

    # Rule 5: No entry/stop for directional trade
    if bias in ("LONG", "SHORT") and confidence >= 70:
        if not trade.entry or not trade.stop:
            rule_violations.append("Missing entry or stop loss. NO_TRADE.")

    # Recalculate confidence from scoring breakdown as validation
    if scoring.total == 0 and any([
        scoring.marketStructure, scoring.liquidity, scoring.fvg,
        scoring.orderBlocks, scoring.volume, scoring.momentum,
    ]):
        calculated = (
            scoring.marketStructure * 0.25
            + scoring.liquidity * 0.20
            + scoring.fvg * 0.15
            + scoring.orderBlocks * 0.15
            + scoring.volume * 0.15
            + scoring.momentum * 0.10
        )
        scoring.total = int(round(calculated))
        if scoring.total < 70 and bias in ("LONG", "SHORT"):
            rule_violations.append(f"Calculated confidence {scoring.total} < 70. NO_TRADE enforced.")

    if rule_violations:
        return TradePlan(
            bias="NO_TRADE",
            confidence=min(confidence, 50),
            entry="",
            stop="",
            tp1="",
            tp2="",
            tp3="",
            riskReward="",
            probabilityScore="",
            reasoning=trade.reasoning + rule_violations,
        )

    return trade
