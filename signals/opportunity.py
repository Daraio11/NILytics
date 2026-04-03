"""
NILytics — Opportunity Score (Phase 3.3)

opportunity_score = adjusted_value - market_value_estimate
(Stored raw in DB; display layer negates and swaps columns so that
 positive Alpha = undervalued = production worth exceeds market cost.)
"""


def compute_opportunity_score(adjusted_value: int, market_value: int) -> int:
    """Return the gap between our valuation and market perception."""
    return adjusted_value - market_value
