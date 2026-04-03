"""
NILytics — Tier Assignment (Phase 2.4)

Assigns T1/T2/T3/T4 based on FROZEN global cutoffs.
Output Score is the ONLY input. Money NEVER affects tiers.

Eligibility: snaps_proxy >= 300 OR industry_rating >= 79.9
Ineligible players get tier = None (excluded from valuation).

Pre-set cutoffs (from 2021-2025 eligible pool):
  RB:  T1 >= 86.60 | T2 >= 79.80 | T3 >= 73.30
  WR:  T1 >= 78.80 | T2 >= 71.10 | T3 >= 63.50
  TE:  T1 >= 72.65 | T2 >= 63.45 | T3 >= 55.40
  OT:  T1 >= 74.90 | T2 >= 68.04 | T3 >= 60.23
  IOL: T1 >= 74.60 | T2 >= 68.80 | T3 >= 62.25

QB, EDGE, IDL, LB, CB, S: computed on first run from 2021-2025 eligible pool, then frozen.
"""

# ─── Frozen Tier Cutoffs ─────────────────────────────────────────────
# Format: {position: (T1_min, T2_min, T3_min)}  — below T3_min = T4

FROZEN_CUTOFFS = {
    # Cutoffs target ~15% T1 of the ELIGIBLE pool (300+ snaps or recruit exception)
    # Since eligible players skew higher, cutoffs need to be above the naive percentile
    'RB':  (93.00, 79.00, 60.00),
    'WR':  (93.00, 79.00, 60.00),
    'TE':  (93.00, 79.00, 60.00),
    'OT':  (93.00, 79.00, 60.00),
    'IOL': (93.00, 79.00, 60.00),
    # These will be computed and frozen on first run:
    'QB':  None,
    'EDGE': None,
    'IDL': None,
    'LB':  None,
    'CB':  None,
    'S':   None,
}


def compute_cutoffs_from_pool(eligible_scores: list[float]) -> tuple[float, float, float]:
    """
    Compute T1/T2/T3 cutoffs from a pool of eligible output_scores.
    Uses percentile-based approach matching the frozen cutoff methodology:
      T1 = top ~12% (88th percentile)  — elite production only
      T2 = next ~18% (70th percentile)  — very good
      T3 = next ~25% (45th percentile)  — solid starters
      T4 = bottom ~45%

    Note: Output scores are already percentiles (0-100), but the eligible pool
    is a subset of all players, so the distribution within the eligible pool
    needs its own percentile computation.
    """
    if not eligible_scores:
        return (80.0, 65.0, 50.0)  # fallback

    import numpy as np
    scores = sorted(eligible_scores)
    t1_min = round(float(np.percentile(scores, 93)), 2)
    t2_min = round(float(np.percentile(scores, 79)), 2)
    t3_min = round(float(np.percentile(scores, 60)), 2)
    return (t1_min, t2_min, t3_min)


def get_cutoffs(position: str) -> tuple[float, float, float] | None:
    """Get frozen cutoffs for a position. Returns None if not yet computed."""
    return FROZEN_CUTOFFS.get(position)


def set_cutoffs(position: str, cutoffs: tuple[float, float, float]):
    """Set (freeze) cutoffs for a position."""
    FROZEN_CUTOFFS[position] = cutoffs


def assign_tier(output_score: float, position: str) -> str | None:
    """
    Assign tier based on output_score and position cutoffs.
    Returns 'T1', 'T2', 'T3', 'T4', or None if cutoffs not available.
    """
    cutoffs = FROZEN_CUTOFFS.get(position)
    if cutoffs is None:
        return None

    t1_min, t2_min, t3_min = cutoffs

    if output_score >= t1_min:
        return 'T1'
    elif output_score >= t2_min:
        return 'T2'
    elif output_score >= t3_min:
        return 'T3'
    else:
        return 'T4'


def check_eligibility(snaps_proxy: int, industry_rating: float | None) -> bool:
    """
    Check if a player is eligible for tiering.
    Eligible if: snaps_proxy >= 300 OR industry_rating >= 79.9
    """
    if snaps_proxy >= 300:
        return True
    if industry_rating is not None and industry_rating >= 79.9:
        return True
    return False
