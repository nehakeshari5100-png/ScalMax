import re
from enum import Enum

from services.vision.models import MarketExtraction, ValidationLayer, ValidationReport


class SignalStrength(str, Enum):
    STRONG_SIGNAL = "STRONG_SIGNAL"
    VALID_SIGNAL = "VALID_SIGNAL"
    WATCHLIST = "WATCHLIST"
    NO_TRADE = "NO_TRADE"


class SignalValidator:
    LAYER_CONFIG = [
        ("Market Structure", 20),
        ("Liquidity", 20),
        ("SMC Confirmation", 15),
        ("FVG / Order Block", 15),
        ("Volume", 10),
        ("Momentum", 10),
        ("Risk Reward", 10),
    ]

    @classmethod
    def validate(cls, extraction: MarketExtraction) -> ValidationReport:
        trade = extraction.trade
        ms = extraction.marketStructure
        liq = extraction.liquidity
        smc = extraction.smc
        fvgs = extraction.fvgs
        obs = extraction.orderBlocks
        vol = extraction.volume
        mom = extraction.momentum

        layers: List[ValidationLayer] = []
        passed: List[str] = []
        failed: List[str] = []

        results = [
            cls._check_market_structure(ms, trade.bias),
            cls._check_liquidity(liq),
            cls._check_smc(smc),
            cls._check_zone(fvgs, obs),
            cls._check_volume(vol),
            cls._check_momentum(mom),
            cls._check_risk_reward(trade.riskReward),
        ]

        for layer in results:
            layers.append(layer)
            if layer.passed:
                passed.append(layer.name)
            else:
                failed.append(layer.name)

        final_score = sum(l.score for l in layers)

        if final_score >= 80:
            strength = SignalStrength.STRONG_SIGNAL.value
        elif final_score >= 70:
            strength = SignalStrength.VALID_SIGNAL.value
        elif final_score >= 60:
            strength = SignalStrength.WATCHLIST.value
        else:
            strength = SignalStrength.NO_TRADE.value

        return ValidationReport(
            layers=layers,
            passedLayers=passed,
            failedLayers=failed,
            finalScore=final_score,
            signalStrength=strength,
        )

    @classmethod
    def _check_market_structure(cls, ms, bias: str) -> ValidationLayer:
        score = 0
        details = ""
        passed = False

        if bias == "LONG" and ms.higherHighs and ms.higherLows:
            score = 20
            details = "HH+HL confirmed for LONG bias"
            passed = True
        elif bias == "SHORT" and ms.lowerHighs and ms.lowerLows:
            score = 20
            details = "LH+LL confirmed for SHORT bias"
            passed = True
        elif ms.classification == "range":
            details = f"Ranging structure ({ms.classification}). No directional bias."
            passed = False
        elif ms.higherHighs and ms.higherLows:
            details = "HH+HL detected but bias is not LONG"
            passed = False
        elif ms.lowerHighs and ms.lowerLows:
            details = "LH+LL detected but bias is not SHORT"
            passed = False
        else:
            details = f"Mixed or unclear structure ({ms.classification})"
            passed = False

        return ValidationLayer(
            name="Market Structure",
            passed=passed,
            score=score,
            maxScore=20,
            details=details,
        )

    @classmethod
    def _check_liquidity(cls, liq) -> ValidationLayer:
        score = 0
        details = ""
        passed = False

        if liq.swept:
            score = 20
            details = f"Liquidity sweep confirmed: {liq.sweepType}"
            passed = True
        elif liq.buySideLiquidity or liq.sellSideLiquidity:
            score = 10
            details = "Liquidity identified but no sweep confirmed"
            passed = True
        else:
            details = "No liquidity data available"
            passed = False

        return ValidationLayer(
            name="Liquidity",
            passed=passed,
            score=score,
            maxScore=20,
            details=details,
        )

    @classmethod
    def _check_smc(cls, smc) -> ValidationLayer:
        score = 0
        details = ""
        passed = False
        confirms = []

        if smc.bos and smc.bosConfidence >= 70:
            confirms.append(f"BOS ({smc.bosConfidence}%)")
            score += 8
        if smc.choch and smc.chochConfidence >= 70:
            confirms.append(f"CHOCH ({smc.chochConfidence}%)")
            score += 8
        if smc.mss and smc.mssConfidence >= 70:
            confirms.append(f"MSS ({smc.mssConfidence}%)")
            score += 8

        if confirms:
            details = "Confirmed: " + ", ".join(confirms)
            passed = True
            score = min(score, 15)
        else:
            details = "No SMC confirmation (BOS/CHOCH/MSS below 70 confidence)"
            passed = False

        return ValidationLayer(
            name="SMC Confirmation",
            passed=passed,
            score=score,
            maxScore=15,
            details=details,
        )

    @classmethod
    def _check_zone(cls, fvgs, obs) -> ValidationLayer:
        score = 0
        details = ""
        passed = False
        zones = []

        for fvg in fvgs:
            if fvg.strength >= 60 and fvg.status in ("untouched", "partially_filled"):
                zones.append(f"FVG ({fvg.type}, S:{fvg.strength})")
                score += 8
                break

        for ob in obs:
            if ob.status in ("unmitigated", "fresh"):
                zones.append(f"OB ({ob.type}, {ob.status})")
                score += 8
                break

        if zones:
            details = "Zone reaction: " + ", ".join(zones)
            passed = True
            score = min(score, 15)
        else:
            details = "No usable FVG or Order Block detected"
            passed = False

        return ValidationLayer(
            name="FVG / Order Block",
            passed=passed,
            score=score,
            maxScore=15,
            details=details,
        )

    @classmethod
    def _check_volume(cls, vol) -> ValidationLayer:
        score = 0
        details = ""
        passed = False

        bv = (vol.breakoutVolume or "").lower()
        spikes = (vol.spikes or "").lower()

        if "high" in bv or "strong" in bv or "expansion" in bv:
            score = 10
            details = f"Breakout volume: {vol.breakoutVolume}"
            passed = True
        elif spikes and ("high" in spikes or "spike" in spikes):
            score = 7
            details = f"Volume spikes detected: {vol.spikes}"
            passed = True
        elif "weak" not in bv and bv:
            score = 5
            details = f"Volume present: {vol.breakoutVolume}"
            passed = True
        else:
            details = "No volume confirmation (weak or missing)"
            passed = False

        return ValidationLayer(
            name="Volume",
            passed=passed,
            score=score,
            maxScore=10,
            details=details,
        )

    @classmethod
    def _check_momentum(cls, mom) -> ValidationLayer:
        score = 0
        details = ""
        passed = False

        if mom.score >= 80:
            score = 10
            details = f"Strong momentum ({mom.score}/100)"
            passed = True
        elif mom.score >= 60:
            score = 7
            details = f"Moderate momentum ({mom.score}/100)"
            passed = True
        elif mom.score >= 40:
            score = 4
            details = f"Weak momentum ({mom.score}/100)"
            passed = True
        else:
            details = f"Poor momentum score ({mom.score}/100)"
            passed = False

        return ValidationLayer(
            name="Momentum",
            passed=passed,
            score=score,
            maxScore=10,
            details=details,
        )

    @classmethod
    def _check_risk_reward(cls, risk_reward: str) -> ValidationLayer:
        score = 0
        details = ""
        passed = False

        if not risk_reward:
            details = "No risk-reward ratio provided"
            passed = False
            return ValidationLayer(
                name="Risk Reward",
                passed=passed,
                score=score,
                maxScore=10,
                details=details,
            )

        match = re.search(r"1:([\d.]+)", risk_reward)
        if match:
            ratio = float(match.group(1))
            if ratio >= 3.0:
                score = 10
                details = f"RR {risk_reward} (excellent)"
                passed = True
            elif ratio >= 2.0:
                score = 7
                details = f"RR {risk_reward} (acceptable)"
                passed = True
            elif ratio >= 1.5:
                score = 4
                details = f"RR {risk_reward} (below preferred minimum)"
                passed = True
            else:
                details = f"RR {risk_reward} (below 1:2 — REJECTED)"
                passed = False
        else:
            details = f"Could not parse RR: {risk_reward}"
            passed = False

        return ValidationLayer(
            name="Risk Reward",
            passed=passed,
            score=score,
            maxScore=10,
            details=details,
        )
