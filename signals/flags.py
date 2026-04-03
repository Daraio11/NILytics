"""
NILytics — Auto-Flag Logic (Phase 3.4)

Assigns alpha signal flags based on player profile and scoring data.

Flags:
  BREAKOUT_CANDIDATE — trending up/breakout trajectory, undervalued, strong output
  HIDDEN_GEM         — low recruit rank or unknown, high output_score, below-market
  REGRESSION_RISK    — overvalued or declining trajectory
  PORTAL_VALUE       — high output_score at G6/FCS, undervalued if moved to P4
  EXPERIENCE_PREMIUM — multi-year P4 starter at premium position
"""

PREMIUM_POSITIONS = {'QB', 'EDGE', 'OT', 'WR', 'CB'}


def compute_flags(
    player_id: int,
    position: str,
    market: str,
    tier: str,
    output_score: float,
    opportunity_score: int,
    trajectory_flag: str,
    star_rating: float | None,
    class_year: str | None,
    seasons_scored: int,
) -> list[str]:
    """
    Return a list of flag strings for this player-season.

    Args:
        player_id: PFF player ID
        position: normalized position
        market: P4/G6/FCS
        tier: T1/T2/T3/T4
        output_score: 0-100 percentile
        opportunity_score: adjusted_value - market_value (positive = undervalued)
        trajectory_flag: UP/DOWN/STABLE/BREAKOUT
        star_rating: recruit star rating (None if unknown)
        class_year: SO/JR/SR/etc (None if unknown)
        seasons_scored: how many seasons this player has scores for
    """
    flags = []

    # NOTE: In the raw pipeline, opportunity_score = adjusted_value - market_value
    # where adjusted_value = market rate, market_value = production/brand worth.
    # Raw NEGATIVE = undervalued in display (production > market cost).
    # Raw POSITIVE = overvalued in display (market cost > production).

    # BREAKOUT_CANDIDATE: trending up with strong production and undervalued
    if star_rating is not None and star_rating >= 3:
        if (class_year in ('SO', 'JR', 'Sophomore', 'Junior')
                and trajectory_flag in ('UP', 'BREAKOUT')
                and opportunity_score < 0):
            flags.append('BREAKOUT_CANDIDATE')
    else:
        if (trajectory_flag == 'BREAKOUT'
                and output_score >= 65
                and opportunity_score < 0):
            flags.append('BREAKOUT_CANDIDATE')

    # HIDDEN_GEM: low recruit rank or unknown, high output, undervalued
    low_recruit = star_rating is None or star_rating <= 2
    if low_recruit and output_score >= 70 and opportunity_score < 0:
        flags.append('HIDDEN_GEM')

    # REGRESSION_RISK: meaningful production decline risk (kept selective)
    #   1. Declining trajectory at T1/T2 — high-value players losing production
    #   2. Breakout player the market has significantly overpriced (unsustainable spike)
    if trajectory_flag == 'DOWN' and tier in ('T1', 'T2'):
        flags.append('REGRESSION_RISK')
    elif trajectory_flag == 'BREAKOUT' and opportunity_score > 200000:
        flags.append('REGRESSION_RISK')

    # PORTAL_VALUE: high output at G6/FCS, would be undervalued at P4
    if market in ('G6', 'FCS') and output_score >= 75 and tier in ('T1', 'T2'):
        flags.append('PORTAL_VALUE')

    # EXPERIENCE_PREMIUM: multi-year P4 starter at premium position
    if (market == 'P4' and position in PREMIUM_POSITIONS
            and seasons_scored >= 3 and tier in ('T1', 'T2')):
        flags.append('EXPERIENCE_PREMIUM')

    return flags
