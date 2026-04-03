"""
NILytics — Custom Weight Recomputation Engine

Runs the full scoring pipeline in-memory with custom weights for a single position.
Does NOT write to the database — purely for "what-if" analysis.

Pipeline: Custom Core Grade → Output Score → Tier → Base Value → Adjusted Value
"""

from scipy import stats as scipy_stats

from scoring.core_grade import compute_core_grade, DEFAULT_WEIGHTS
from scoring.tiers import FROZEN_CUTOFFS, assign_tier, get_cutoffs
from scoring.valuation import compute_base_value


def recompute_position(
    position: str,
    custom_weights: dict,
    player_stats: list[dict],
    season: int,
    leaderboard_df=None,
) -> list[dict]:
    """
    Recompute the full pipeline for a position with custom weights.

    Args:
        position: e.g. 'WR'
        custom_weights: dict of {category: weight} (must sum to 1.0)
        player_stats: list of dicts, each with:
            - player_id, name, school, market, conference, position
            - passing, receiving, rushing, blocking, defense (stat dicts or None)
            - original_core_grade, original_output_score, original_tier,
              original_adjusted_value (from DB for comparison)
        season: the season year
        leaderboard_df: optional pandas DataFrame with original leaderboard data

    Returns:
        list of dicts with both original and custom values for comparison
    """
    # Step 1: Recompute Core Grade for each player with custom weights
    graded = []
    for p in player_stats:
        custom_grade = compute_core_grade(
            position,
            p.get('passing'),
            p.get('receiving'),
            p.get('rushing'),
            p.get('blocking'),
            p.get('defense'),
            weights=custom_weights,
        )
        if custom_grade is not None:
            p['custom_core_grade'] = custom_grade
            graded.append(p)

    if not graded:
        return []

    # Step 2: Compute Output Score (percentile within this position-season)
    grades = [p['custom_core_grade'] for p in graded]
    n = len(grades)

    for p in graded:
        if n == 1:
            p['custom_output_score'] = 50.0
        else:
            pct = scipy_stats.percentileofscore(grades, p['custom_core_grade'], kind='rank')
            p['custom_output_score'] = round(pct, 2)

    # Step 3: Assign Tier using FROZEN cutoffs
    cutoffs = get_cutoffs(position)
    if cutoffs is None:
        cutoffs = (93.0, 79.0, 60.0)  # fallback

    for p in graded:
        p['custom_tier'] = assign_tier(p['custom_output_score'], position)

    # Step 4: Compute Base Value → Adjusted Value (simplified — no experience bonuses)
    for p in graded:
        market = p.get('market', 'P4')
        tier = p['custom_tier']
        if tier:
            base_val = compute_base_value(
                position, market, tier,
                p['custom_output_score'], cutoffs
            )
            p['custom_base_value'] = base_val
            p['custom_adjusted_value'] = base_val  # simplified (no exp/bonus pass)
        else:
            p['custom_base_value'] = 0
            p['custom_adjusted_value'] = 0

    # Step 5: Compute deltas from original values
    for p in graded:
        orig_val = p.get('original_adjusted_value', 0) or 0
        custom_val = p.get('custom_adjusted_value', 0) or 0
        p['value_delta'] = custom_val - orig_val

        orig_grade = p.get('original_core_grade', 0) or 0
        p['grade_delta'] = p['custom_core_grade'] - orig_grade

        orig_tier = p.get('original_tier', 'T4')
        custom_tier = p.get('custom_tier', 'T4')
        tier_order = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}
        orig_rank = tier_order.get(orig_tier, 4)
        custom_rank = tier_order.get(custom_tier, 4)
        if custom_rank < orig_rank:
            p['tier_change'] = 'UP'
        elif custom_rank > orig_rank:
            p['tier_change'] = 'DOWN'
        else:
            p['tier_change'] = 'SAME'

    return graded
