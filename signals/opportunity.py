"""
NILytics — Opportunity Score (Phase 3.3)

opportunity_score = adjusted_value - market_value_estimate

Where:
  adjusted_value = production worth (valuation.py NIL_RANGES)
  market_value   = market rate      (market_estimate.py MARKET_RANGES)

Positive alpha  = production > market → UNDERVALUED (good deal for buyer)
Negative alpha  = market pays more than production warrants → OVERVALUED
"""


def compute_opportunity_score(adjusted_value: int, market_value: int) -> int:
    """Return the gap between our valuation and market perception."""
    return adjusted_value - market_value
