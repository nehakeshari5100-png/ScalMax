
"""
Confluence Scoring Engine.

Combines Indicator Engine, Market Structure Engine, and Liquidity Engine
outputs into a single 0-100 confluence score with grade, reasons, and risks.

Usage:
    from services.confluence import score_confluence
    result = score_confluence(input_data)
"""

from services.confluence.scorer import ConfluenceScorer
from services.confluence.models import ConfluenceInput, ConfluenceOutput


def score_confluence(data: ConfluenceInput) -> ConfluenceOutput:
    """Compute a confluence score from all available engine inputs."""
    return ConfluenceScorer.score(data)


__all__ = ["score_confluence", "ConfluenceInput", "ConfluenceOutput"]
