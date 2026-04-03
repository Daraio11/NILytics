"""
NILytics — Market Value Estimator (Phase 3.1/3.2)

Estimates what the market THINKS a player is worth, independent of our model.
This is deliberately different from our adjusted_value — the gap IS the alpha.

Approach:
  1. Start with position/market/tier median from industry research
  2. Apply name-recognition multiplier (output_score as proxy for visibility)
  3. Apply conference premium (SEC/B1G get outsized market attention)
  4. Add noise band to reflect market irrationality

Sources: ESPN, CBS Sports, On3 industry ranges:
  QB portal elite: $1M-$2M+
  WR high-end: $1M-$2M; average: $500K-$800K
  RB high-end: $400K-$900K
  OT elite: $800K-$1.2M+
  DL elite: $500K-$1M
  CB top: $250K-$400K
  P4 average: ~$75K; all-division average: ~$40K
  SEC/B1G premium confirmed across all sources
"""

import random

# Market perception ranges by position/market/tier
# These represent what the MARKET pays, not what we think players are worth
# Key insight: market overpays QBs and brand-name positions, underpays OL/defense
MARKET_RANGES = {
    'QB': {
        'P4': {'T1': (2_800_000, 5_000_000), 'T2': (1_200_000, 2_800_000), 'T3': (500_000, 1_200_000), 'T4': (150_000, 500_000)},
        'G6': {'T1': (800_000, 1_800_000), 'T2': (350_000, 800_000), 'T3': (150_000, 350_000), 'T4': (50_000, 150_000)},
        'FCS': {'T1': (200_000, 500_000), 'T2': (75_000, 200_000), 'T3': (25_000, 75_000), 'T4': (10_000, 25_000)},
    },
    'RB': {
        'P4': {'T1': (800_000, 1_500_000), 'T2': (400_000, 800_000), 'T3': (150_000, 400_000), 'T4': (40_000, 150_000)},
        'G6': {'T1': (300_000, 600_000), 'T2': (120_000, 300_000), 'T3': (40_000, 120_000), 'T4': (12_000, 40_000)},
        'FCS': {'T1': (75_000, 175_000), 'T2': (30_000, 75_000), 'T3': (12_000, 30_000), 'T4': (4_000, 12_000)},
    },
    'WR': {
        'P4': {'T1': (1_000_000, 2_000_000), 'T2': (500_000, 1_000_000), 'T3': (200_000, 500_000), 'T4': (50_000, 200_000)},
        'G6': {'T1': (350_000, 750_000), 'T2': (150_000, 350_000), 'T3': (50_000, 150_000), 'T4': (15_000, 50_000)},
        'FCS': {'T1': (100_000, 200_000), 'T2': (40_000, 100_000), 'T3': (15_000, 40_000), 'T4': (5_000, 15_000)},
    },
    'TE': {
        'P4': {'T1': (400_000, 700_000), 'T2': (200_000, 400_000), 'T3': (75_000, 200_000), 'T4': (25_000, 75_000)},
        'G6': {'T1': (150_000, 300_000), 'T2': (60_000, 150_000), 'T3': (25_000, 60_000), 'T4': (10_000, 25_000)},
        'FCS': {'T1': (50_000, 100_000), 'T2': (20_000, 50_000), 'T3': (10_000, 20_000), 'T4': (5_000, 10_000)},
    },
    'OT': {
        # Market UNDERVALUES OL — this is where alpha lives
        'P4': {'T1': (600_000, 1_000_000), 'T2': (300_000, 600_000), 'T3': (150_000, 300_000), 'T4': (50_000, 150_000)},
        'G6': {'T1': (200_000, 400_000), 'T2': (80_000, 200_000), 'T3': (30_000, 80_000), 'T4': (15_000, 30_000)},
        'FCS': {'T1': (75_000, 150_000), 'T2': (30_000, 75_000), 'T3': (10_000, 30_000), 'T4': (5_000, 10_000)},
    },
    'IOL': {
        # Even more undervalued than OT
        'P4': {'T1': (400_000, 750_000), 'T2': (200_000, 400_000), 'T3': (100_000, 200_000), 'T4': (30_000, 100_000)},
        'G6': {'T1': (150_000, 300_000), 'T2': (60_000, 150_000), 'T3': (25_000, 60_000), 'T4': (10_000, 25_000)},
        'FCS': {'T1': (50_000, 100_000), 'T2': (20_000, 50_000), 'T3': (10_000, 20_000), 'T4': (5_000, 10_000)},
    },
    'EDGE': {
        'P4': {'T1': (700_000, 1_200_000), 'T2': (350_000, 700_000), 'T3': (150_000, 350_000), 'T4': (50_000, 150_000)},
        'G6': {'T1': (250_000, 500_000), 'T2': (100_000, 250_000), 'T3': (40_000, 100_000), 'T4': (15_000, 40_000)},
        'FCS': {'T1': (75_000, 150_000), 'T2': (30_000, 75_000), 'T3': (10_000, 30_000), 'T4': (5_000, 10_000)},
    },
    'IDL': {
        'P4': {'T1': (500_000, 900_000), 'T2': (250_000, 500_000), 'T3': (100_000, 250_000), 'T4': (30_000, 100_000)},
        'G6': {'T1': (175_000, 350_000), 'T2': (75_000, 175_000), 'T3': (30_000, 75_000), 'T4': (10_000, 30_000)},
        'FCS': {'T1': (50_000, 100_000), 'T2': (25_000, 50_000), 'T3': (10_000, 25_000), 'T4': (5_000, 10_000)},
    },
    'LB': {
        'P4': {'T1': (400_000, 700_000), 'T2': (200_000, 400_000), 'T3': (75_000, 200_000), 'T4': (25_000, 75_000)},
        'G6': {'T1': (150_000, 300_000), 'T2': (60_000, 150_000), 'T3': (25_000, 60_000), 'T4': (10_000, 25_000)},
        'FCS': {'T1': (50_000, 100_000), 'T2': (20_000, 50_000), 'T3': (10_000, 20_000), 'T4': (5_000, 10_000)},
    },
    'CB': {
        'P4': {'T1': (250_000, 450_000), 'T2': (125_000, 250_000), 'T3': (50_000, 125_000), 'T4': (20_000, 50_000)},
        'G6': {'T1': (100_000, 200_000), 'T2': (40_000, 100_000), 'T3': (15_000, 40_000), 'T4': (5_000, 15_000)},
        'FCS': {'T1': (30_000, 75_000), 'T2': (15_000, 30_000), 'T3': (5_000, 15_000), 'T4': (2_500, 5_000)},
    },
    'S': {
        'P4': {'T1': (250_000, 500_000), 'T2': (125_000, 250_000), 'T3': (50_000, 125_000), 'T4': (20_000, 50_000)},
        'G6': {'T1': (100_000, 200_000), 'T2': (40_000, 100_000), 'T3': (15_000, 40_000), 'T4': (5_000, 15_000)},
        'FCS': {'T1': (30_000, 75_000), 'T2': (15_000, 30_000), 'T3': (5_000, 15_000), 'T4': (2_500, 5_000)},
    },
}

# Conferences with outsized NIL market premium (fan base + booster money)
PREMIUM_CONFERENCES = {'SEC', 'Big Ten'}
PREMIUM_MULTIPLIER = 1.20  # 20% market premium

# High-visibility multiplier: top output_score players get more market attention
# This creates the "brand name tax" the market pays
VISIBILITY_THRESHOLDS = [
    (95, 1.25),  # Stars get 25% premium
    (85, 1.10),  # Very good players get 10% premium
    (70, 1.00),  # Average — no adjustment
    (0,  0.85),  # Below average — market discounts
]


def estimate_market_value(
    position: str,
    market: str,
    tier: str,
    output_score: float,
    conference: str,
    seed: int | None = None,
) -> tuple[int, str]:
    """
    Estimate what the market thinks this player is worth.

    Returns (estimated_value, confidence_band).
    Confidence band: 'high' (well-known player), 'medium', 'low' (obscure player).
    """
    if seed is not None:
        random.seed(seed)

    # Base: get market range for position/market/tier
    pos_ranges = MARKET_RANGES.get(position)
    if not pos_ranges:
        return (0, 'low')

    mkt_ranges = pos_ranges.get(market)
    if not mkt_ranges:
        return (0, 'low')

    tier_range = mkt_ranges.get(tier)
    if not tier_range:
        return (0, 'low')

    range_min, range_max = tier_range

    # Interpolate based on output_score within tier
    # Higher output_score = market perceives as better within tier
    pct = max(0.0, min(1.0, output_score / 100.0))
    base_estimate = range_min + pct * (range_max - range_min)

    # Apply visibility multiplier
    vis_mult = 0.85
    for threshold, mult in VISIBILITY_THRESHOLDS:
        if output_score >= threshold:
            vis_mult = mult
            break
    base_estimate *= vis_mult

    # Apply conference premium
    if conference in PREMIUM_CONFERENCES:
        base_estimate *= PREMIUM_MULTIPLIER

    # Cap at 1.25× the tier range ceiling to prevent compounding multipliers
    # from producing unrealistic values
    cap = range_max * 1.25
    final_estimate = min(base_estimate, cap)

    # Determine confidence band
    if output_score >= 90:
        confidence = 'high'  # Well-known, lots of market data
    elif output_score >= 65:
        confidence = 'medium'
    else:
        confidence = 'low'  # Obscure player, market estimate is a guess

    return (max(0, round(final_estimate)), confidence)
