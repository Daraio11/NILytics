"""
NILytics — Recruit / Prospect Valuation

Maps ESPN 300 Grade → Projected Tier → Projected NIL Value.
Used for:
  1. Incoming freshmen (2026 class) in GM Mode
  2. Players with no/limited PFF production (injured, redshirt, etc.)

ESPN Grade → Tier mapping:
  - 92+ (Top ~10, 5-star elite)    → T1 projected
  - 90+ (Top ~25, 5-star / high 4) → T2 projected
  - 86+ (Top ~75, 4-star)          → T3 projected
  - Below 86 (low 4-star / 3-star) → T4 projected

Top 100 recruits at premium positions (QB, EDGE, OT, WR, CB) get a premium multiplier.

Value is a PROJECTED range, not production-based. Flagged with 🌟 PROSPECT.
"""

import os
import csv

# Premium positions command higher NIL dollars
PREMIUM_POSITIONS = {'QB', 'EDGE', 'OT', 'WR', 'CB'}

# ESPN position → NILytics position mapping
ESPN_POS_MAP = {
    'QB': 'QB', 'QB-PP': 'QB', 'QB-DT': 'QB',
    'RB': 'RB', 'HB': 'RB',
    'WR': 'WR', 'ATH': 'WR',  # ATH default to WR
    'TE': 'TE', 'TE-H': 'TE', 'TE-Y': 'TE',
    'OT': 'OT', 'OG': 'IOL', 'OC': 'IOL',
    'DE': 'EDGE', 'OLB': 'EDGE',
    'DT': 'IDL',
    'ILB': 'LB',
    'CB': 'CB',
    'S': 'S',
}

# ESPN Grade → Tier thresholds
TIER_THRESHOLDS = [
    (92, 'T1'),
    (90, 'T2'),
    (86, 'T3'),
    (0,  'T4'),
]

# Base projected value ranges by tier for recruits
# Slightly lower than proven players, but reflects real NIL market premiums on potential
RECRUIT_VALUE_RANGES = {
    'T1': (750_000, 2_000_000),   # Elite 5-star: $750K-$2M
    'T2': (250_000, 750_000),     # High 4-star/5-star: $250K-$750K
    'T3': (75_000, 250_000),      # Mid 4-star: $75K-$250K
    'T4': (25_000, 75_000),       # Low 4-star / 3-star: $25K-$75K
}

# Premium position multiplier (top 100 only)
PREMIUM_MULTIPLIER = 1.25


def espn_grade_to_tier(grade: float) -> str:
    """Map an ESPN 300 grade (80-95 scale) to a projected tier."""
    for threshold, tier in TIER_THRESHOLDS:
        if grade >= threshold:
            return tier
    return 'T4'


def map_espn_position(espn_pos: str) -> str:
    """Map ESPN recruiting position to NILytics position."""
    return ESPN_POS_MAP.get(espn_pos, espn_pos)


def project_recruit_value(rank: int, espn_grade: float, position: str) -> int:
    """
    Project an NIL value for a recruit/prospect.

    Uses ESPN grade to determine tier, then interpolates within
    that tier's value range. Top 100 at premium positions get a multiplier.
    """
    tier = espn_grade_to_tier(espn_grade)
    lo, hi = RECRUIT_VALUE_RANGES[tier]

    # Find where this grade falls within its tier range
    for i, (thresh, t) in enumerate(TIER_THRESHOLDS):
        if t == tier:
            tier_top = TIER_THRESHOLDS[i - 1][0] if i > 0 else 100
            tier_bottom = thresh
            break
    else:
        tier_top, tier_bottom = 100, 0

    # Interpolate: higher grade within tier = higher value
    if tier_top == tier_bottom:
        pct = 0.5
    else:
        pct = (espn_grade - tier_bottom) / (tier_top - tier_bottom)
        pct = max(0.0, min(1.0, pct))

    base_value = lo + (hi - lo) * pct

    # Premium position multiplier for top 100
    nil_position = map_espn_position(position)
    if rank <= 100 and nil_position in PREMIUM_POSITIONS:
        base_value *= PREMIUM_MULTIPLIER

    # Top 10 overall bonus
    if rank <= 10:
        base_value *= 1.25
    elif rank <= 25:
        base_value *= 1.10

    return int(round(base_value, -3))  # Round to nearest $1K


# ── Market Value: what the NIL market actually pays for potential ──
# This is SEPARATE from Player Value (production-based).
# Market pays for: recruit pedigree + program prestige + remaining eligibility + position scarcity.

# P4 programs pay more than G6/FCS — use school name as rough proxy
# (We'll match against conference_teams in the full pipeline, but for CSV-based
# loading we use the ESPN committed school which is almost always P4 for ESPN 300)
MARKET_PROGRAM_TIER = {
    # Tier 1 programs (highest NIL spending)
    'Ohio State': 1.4, 'Texas': 1.4, 'Georgia': 1.4, 'Alabama': 1.4,
    'Oregon': 1.35, 'USC': 1.35, 'Michigan': 1.3, 'LSU': 1.3,
    'Clemson': 1.25, 'Notre Dame': 1.25, 'Tennessee': 1.25, 'Miami': 1.25,
    'Oklahoma': 1.2, 'Texas A&M': 1.2, 'Penn State': 1.2, 'Florida': 1.2,
    'Ole Miss': 1.2, 'Auburn': 1.15, 'Colorado': 1.15, 'S Carolina': 1.1,
}

# Remaining eligibility multiplier: more years = more market value
# Freshmen (4 yrs left) get the biggest premium
ELIGIBILITY_MULTIPLIER = {
    4: 1.5,   # True freshman — 4 years of potential
    3: 1.3,   # Sophomore
    2: 1.15,  # Junior
    1: 1.0,   # Senior — market pays for production, not potential
}


def project_recruit_market_value(rank: int, espn_grade: float, position: str,
                                  school: str = '', years_remaining: int = 4) -> int:
    """
    Project what the NIL MARKET would actually pay for this prospect.

    This is higher than Player Value because the market prices in:
    - Recruit pedigree (ESPN grade/stars/rank)
    - Program prestige (Oregon pays more than FCS)
    - Remaining eligibility (4 years > 1 year)
    - Position scarcity (QBs command premium)

    A 4-star safety at Oregon with 4 years left → "low T1 / high T2" range.
    """
    # Start with the production-based value as a floor
    player_value = project_recruit_value(rank, espn_grade, position)

    # Market premium based on recruit ranking (top recruits get outsized market deals)
    if rank <= 5:
        rank_mult = 2.0
    elif rank <= 15:
        rank_mult = 1.8
    elif rank <= 30:
        rank_mult = 1.6
    elif rank <= 50:
        rank_mult = 1.5
    elif rank <= 100:
        rank_mult = 1.3
    elif rank <= 150:
        rank_mult = 1.2
    else:
        rank_mult = 1.1

    market_value = player_value * rank_mult

    # Program prestige multiplier
    program_mult = MARKET_PROGRAM_TIER.get(school, 1.0)
    market_value *= program_mult

    # Remaining eligibility multiplier
    elig_mult = ELIGIBILITY_MULTIPLIER.get(years_remaining, 1.0)
    market_value *= elig_mult

    return int(round(market_value, -3))  # Round to nearest $1K


def load_recruits_from_csv(class_year: int) -> list[dict]:
    """
    Load a recruiting class from local CSV and compute projected values.
    Returns list of dicts compatible with the leaderboard/GM Mode.
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'recruits', f'espn300_{class_year}.csv'
    )

    if not os.path.exists(csv_path):
        return []

    recruits = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rank = int(row['rank'])
            name = row['name'].strip()
            espn_pos = row['position'].strip()
            school = row['school'].strip()
            grade = float(row['grade'])
            stars = int(row['stars'])

            nil_position = map_espn_position(espn_pos)
            tier = espn_grade_to_tier(grade)
            player_value = project_recruit_value(rank, grade, espn_pos)
            market_value = project_recruit_market_value(
                rank, grade, espn_pos, school=school, years_remaining=4
            )

            recruits.append({
                'player_id': f'REC{class_year}_{rank:04d}',
                'name': name,
                'position': nil_position,
                'school': school,
                'tier': tier,
                'core_grade': grade,
                'output_score': max(0, 100 - rank * 0.3),
                'adjusted_value': player_value,      # production floor → displays as "Value"
                'market_value': market_value,        # market premium → displays as "Mkt Value"
                'opportunity_score': player_value - market_value,  # negative = overvalued (market > production)
                'trajectory_flag': 'STABLE',
                'flags': '["🌟 PROSPECT"]',
                'conference': '',
                'market': '',
                'is_prospect': True,
                'espn_grade': grade,
                'stars': stars,
                'recruit_rank': rank,
                'recruit_class': class_year,
            })

    return recruits


def load_2026_recruits() -> list[dict]:
    """Convenience wrapper for 2026 class (backward compat)."""
    return load_recruits_from_csv(2026)


def load_all_prospects(class_years: list[int] = None) -> list[dict]:
    """
    Load recruits from all specified class years.
    Default: 2025 + 2026 (most likely to have zero production).
    """
    if class_years is None:
        class_years = [2025, 2026]
    all_recruits = []
    for year in class_years:
        all_recruits.extend(load_recruits_from_csv(year))
    return all_recruits
