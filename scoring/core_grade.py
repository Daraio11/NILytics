"""
NILytics — Core Grade Computation (Phase 2.2)

Position-specific weighted composite grade (0-100 scale).
Each component is a PFF grade (already 0-100) or a rate stat that gets normalized.

Weights:
  QB:   60% pass, 10% rush, 10% BTT%, 20% TWP% (inverted)
  RB:   60% rush, 15% receiving, 5% pass block, 5% volume, 15% explosiveness
  WR:   65% route, 5% drop grade (inverted), 10% volume, 20% explosiveness
  TE:   55% receiving, 35% blocking, 10% volume, 10% explosiveness  (sums to 110 — see note)
  OT:   50% pass block, 40% run block, 5% penalties (inv), 5% LT snap volume
  IOL:  45% pass block, 45% run block, 5% penalties (inv), 5% volume
  EDGE: 50% pass rush, 25% total pressures, 15% hurries, 10% sacks
  IDL:  40% pass rush, 40% run defense, 10% volume, 5% penalties, 5% disruption
  LB:   25% coverage, 40% run defense, 15% pass rush, 10% volume, 10% reliability
  CB:   50% coverage, 15% disruption, 15% reliability, 10% volume, 10% explosiveness
  S:    35% coverage, 30% tackling, 15% ball production, 10% volume, 10% reliability
"""

import math


def _safe(d, key, default=0.0):
    """Safely extract a numeric value from a dict."""
    if d is None:
        return default
    v = d.get(key)
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def _clamp(val, lo=0.0, hi=100.0):
    return max(lo, min(hi, val))


def _normalize_rate(value, min_val, max_val):
    """Normalize a rate stat to 0-100 scale given expected min/max."""
    if max_val == min_val:
        return 50.0
    return _clamp(((value - min_val) / (max_val - min_val)) * 100.0)


def _invert(grade):
    """Invert a 0-100 grade (lower is better → higher is better)."""
    return _clamp(100.0 - grade)


# ─── Default weight dicts per position ─────────────────────────────

DEFAULT_QB_WEIGHTS = {
    'passing': 0.60,
    'rushing': 0.10,
    'btt_rate': 0.10,
    'twp_rate': 0.20,
}

DEFAULT_RB_WEIGHTS = {
    'rushing': 0.60,
    'receiving': 0.15,
    'pass_blocking': 0.05,
    'volume': 0.05,
    'explosiveness': 0.15,
}

DEFAULT_WR_WEIGHTS = {
    'route_running': 0.65,
    'drop_grade': 0.05,
    'volume': 0.10,
    'explosiveness': 0.20,
}

DEFAULT_TE_WEIGHTS = {
    'receiving': 0.55,
    'blocking': 0.35,
    'volume': 0.10,
    'explosiveness': 0.10,  # Note: sums to 110% per user spec — will be normalized below
}

DEFAULT_OT_WEIGHTS = {
    'pass_blocking': 0.50,
    'run_blocking': 0.40,
    'penalties': 0.05,
    'lt_snap_volume': 0.05,
}

DEFAULT_IOL_WEIGHTS = {
    'pass_blocking': 0.45,
    'run_blocking': 0.45,
    'penalties': 0.05,
    'volume': 0.05,
}

DEFAULT_EDGE_WEIGHTS = {
    'pass_rush': 0.50,
    'total_pressures': 0.25,
    'hurries': 0.15,
    'sacks': 0.10,
}

DEFAULT_IDL_WEIGHTS = {
    'pass_rush': 0.40,
    'run_defense': 0.40,
    'volume': 0.10,
    'penalties': 0.05,
    'disruption': 0.05,
}

DEFAULT_LB_WEIGHTS = {
    'coverage': 0.25,
    'run_defense': 0.40,
    'pass_rush': 0.15,
    'volume': 0.10,
    'reliability': 0.10,
}

DEFAULT_CB_WEIGHTS = {
    'coverage': 0.50,
    'disruption': 0.15,
    'reliability': 0.15,
    'volume': 0.10,
    'explosiveness': 0.10,
}

DEFAULT_S_WEIGHTS = {
    'coverage': 0.35,
    'tackling': 0.30,
    'ball_production': 0.15,
    'volume': 0.10,
    'reliability': 0.10,
}

DEFAULT_WEIGHTS = {
    'QB': DEFAULT_QB_WEIGHTS,
    'RB': DEFAULT_RB_WEIGHTS,
    'WR': DEFAULT_WR_WEIGHTS,
    'TE': DEFAULT_TE_WEIGHTS,
    'OT': DEFAULT_OT_WEIGHTS,
    'IOL': DEFAULT_IOL_WEIGHTS,
    'EDGE': DEFAULT_EDGE_WEIGHTS,
    'IDL': DEFAULT_IDL_WEIGHTS,
    'LB': DEFAULT_LB_WEIGHTS,
    'CB': DEFAULT_CB_WEIGHTS,
    'S': DEFAULT_S_WEIGHTS,
}

WEIGHT_LABELS = {
    'QB': {
        'passing': 'Passing Grade',
        'rushing': 'Rushing Grade',
        'btt_rate': 'Big Time Throw %',
        'twp_rate': 'Turnover Worthy Play % (inv)',
    },
    'RB': {
        'rushing': 'Rushing Grade',
        'receiving': 'Receiving Grade',
        'pass_blocking': 'Pass Blocking Grade',
        'volume': 'Carry Volume',
        'explosiveness': 'Explosiveness (Elusive Rating)',
    },
    'WR': {
        'route_running': 'Route Running Grade',
        'drop_grade': 'Hands / Drop Grade',
        'volume': 'Target Volume',
        'explosiveness': 'Explosiveness (YPRR/YAC/MTF)',
    },
    'TE': {
        'receiving': 'Receiving Grade',
        'blocking': 'Blocking Grade (Pass + Run)',
        'volume': 'Snap Volume (Routes + Blocking)',
        'explosiveness': 'Explosiveness (YPRR/YAC)',
    },
    'OT': {
        'pass_blocking': 'Pass Blocking Grade',
        'run_blocking': 'Run Blocking Grade',
        'penalties': 'Penalty Avoidance (inv)',
        'lt_snap_volume': 'Left Tackle Snap Volume',
    },
    'IOL': {
        'pass_blocking': 'Pass Blocking Grade',
        'run_blocking': 'Run Blocking Grade',
        'penalties': 'Penalty Avoidance (inv)',
        'volume': 'Snap Volume',
    },
    'EDGE': {
        'pass_rush': 'Pass Rush Grade',
        'total_pressures': 'Total Pressures',
        'hurries': 'Hurries',
        'sacks': 'Sacks',
    },
    'IDL': {
        'pass_rush': 'Pass Rush Grade',
        'run_defense': 'Run Defense Grade',
        'volume': 'Snap Volume',
        'penalties': 'Penalty Avoidance (inv)',
        'disruption': 'Disruption (TFL + Pressures)',
    },
    'LB': {
        'coverage': 'Coverage Grade',
        'run_defense': 'Run Defense Grade',
        'pass_rush': 'Pass Rush Grade',
        'volume': 'Snap Volume',
        'reliability': 'Tackling Reliability (inv MTR)',
    },
    'CB': {
        'coverage': 'Coverage Grade',
        'disruption': 'Disruption (INT + PBU)',
        'reliability': 'Tackling Reliability (inv MTR)',
        'volume': 'Coverage Snap Volume',
        'explosiveness': 'Playmaking (Catch Rate inv + FF)',
    },
    'S': {
        'coverage': 'Coverage Grade',
        'tackling': 'Tackling Grade',
        'ball_production': 'Ball Production (INT/PBU/FF)',
        'volume': 'Snap Volume',
        'reliability': 'Tackling Reliability (inv MTR)',
    },
}


# ─── Position-specific core grade functions ───────────────────────────

def grade_qb(passing: dict | None, rushing: dict | None, weights=None) -> float | None:
    """QB: 60% pass + 10% rush + 10% BTT% + 20% TWP%(inv)"""
    w = weights if weights else DEFAULT_QB_WEIGHTS

    pass_grade = _safe(passing, 'grades_pass')
    if pass_grade == 0:
        return None  # No passing data = can't grade

    rush_grade = _safe(passing, 'grades_run', 50.0)  # grades_run is in passing file for QBs
    btt_rate = _safe(passing, 'btt_rate', 0.0)
    twp_rate = _safe(passing, 'twp_rate', 0.0)

    # BTT% typically 0-12%, normalize to 0-100
    btt_norm = _normalize_rate(btt_rate, 0.0, 12.0)
    # TWP% typically 0-8%, normalize and invert (lower is better)
    twp_norm = _invert(_normalize_rate(twp_rate, 0.0, 8.0))

    return _clamp(
        pass_grade * w['passing'] +
        rush_grade * w['rushing'] +
        btt_norm * w['btt_rate'] +
        twp_norm * w['twp_rate']
    )


def grade_rb(rushing: dict | None, receiving: dict | None, blocking: dict | None, weights=None) -> float | None:
    """RB: 60% rush + 15% receiving + 5% pass block + 5% volume + 15% explosiveness"""
    w = weights if weights else DEFAULT_RB_WEIGHTS

    rush_grade = _safe(rushing, 'grades_run')
    if rush_grade == 0:
        return None

    # Receiving grade comes from rushing file (grades_pass_route) or receiving file
    rec_grade = _safe(rushing, 'grades_pass_route', 0.0)
    if rec_grade == 0:
        rec_grade = _safe(receiving, 'grades_pass_route', 50.0)

    pass_block = _safe(rushing, 'grades_pass_block', _safe(receiving, 'grades_pass_block', 50.0))

    # Volume: attempts, normalize 50-350 range
    attempts = _safe(rushing, 'attempts', 0.0)
    vol_norm = _normalize_rate(attempts, 50.0, 350.0)

    # Explosiveness: elusive_rating (typically 20-150) or breakaway_percent (0-30%)
    elusive = _safe(rushing, 'elusive_rating', 0.0)
    breakaway = _safe(rushing, 'breakaway_percent', 0.0)
    if elusive > 0:
        explo_norm = _normalize_rate(elusive, 20.0, 150.0)
    else:
        explo_norm = _normalize_rate(breakaway, 0.0, 30.0)

    return _clamp(
        rush_grade * w['rushing'] +
        rec_grade * w['receiving'] +
        pass_block * w['pass_blocking'] +
        vol_norm * w['volume'] +
        explo_norm * w['explosiveness']
    )


def grade_wr(receiving: dict | None, rushing: dict | None, weights=None) -> float | None:
    """WR: 65% route + 5% drop grade (inv) + 10% volume + 20% explosiveness (YPRR/YAC/MTF)"""
    w = weights if weights else DEFAULT_WR_WEIGHTS

    route_grade = _safe(receiving, 'grades_pass_route')
    if route_grade == 0:
        return None

    drop_grade = _safe(receiving, 'grades_hands_drop', 50.0)

    # Volume: targets, normalize 20-150
    targets = _safe(receiving, 'targets', 0.0)
    vol_norm = _normalize_rate(targets, 20.0, 150.0)

    # Explosiveness: YPRR (0.5-3.5), YAC/rec (0-15), avoided tackles
    yprr = _safe(receiving, 'yprr', 0.0)
    yac_per_rec = _safe(receiving, 'yards_after_catch_per_reception', 0.0)
    avoided = _safe(receiving, 'avoided_tackles', 0.0)

    yprr_norm = _normalize_rate(yprr, 0.5, 3.5)
    yac_norm = _normalize_rate(yac_per_rec, 0.0, 12.0)
    mtf_norm = _normalize_rate(avoided, 0.0, 25.0)
    explo_norm = (yprr_norm * 0.5 + yac_norm * 0.3 + mtf_norm * 0.2)

    return _clamp(
        route_grade * w['route_running'] +
        drop_grade * w['drop_grade'] +
        vol_norm * w['volume'] +
        explo_norm * w['explosiveness']
    )


def grade_te(receiving: dict | None, blocking: dict | None, weights=None) -> float | None:
    """TE: 55% receiving + 35% blocking + 10% volume + 10% explosiveness"""
    w = weights if weights else DEFAULT_TE_WEIGHTS

    rec_grade = _safe(receiving, 'grades_pass_route', 0.0)
    blk_grade_pass = _safe(blocking, 'grades_pass_block', 0.0)
    blk_grade_run = _safe(blocking, 'grades_run_block', 0.0)

    # Need at least one meaningful grade
    if rec_grade == 0 and blk_grade_pass == 0 and blk_grade_run == 0:
        return None

    # Blocking composite: average of pass block and run block
    blk_composite = 50.0
    if blk_grade_pass > 0 and blk_grade_run > 0:
        blk_composite = (blk_grade_pass + blk_grade_run) / 2
    elif blk_grade_pass > 0:
        blk_composite = blk_grade_pass
    elif blk_grade_run > 0:
        blk_composite = blk_grade_run

    if rec_grade == 0:
        rec_grade = 50.0

    # Volume: routes + blocking snaps
    routes = _safe(receiving, 'routes', 0.0)
    blk_snaps = _safe(blocking, 'snap_counts_block', 0.0)
    vol_norm = _normalize_rate(routes + blk_snaps, 100.0, 800.0)

    # Explosiveness
    yprr = _safe(receiving, 'yprr', 0.0)
    yac_per_rec = _safe(receiving, 'yards_after_catch_per_reception', 0.0)
    explo_norm = (_normalize_rate(yprr, 0.5, 3.0) * 0.5 +
                  _normalize_rate(yac_per_rec, 0.0, 10.0) * 0.5)

    return _clamp(
        rec_grade * w['receiving'] +
        blk_composite * w['blocking'] +
        vol_norm * w['volume'] +
        explo_norm * w['explosiveness']
    )


def grade_ot(blocking: dict | None, weights=None) -> float | None:
    """OT: 50% pass block + 40% run block + 5% penalties (inv) + 5% LT snap volume"""
    w = weights if weights else DEFAULT_OT_WEIGHTS

    pass_blk = _safe(blocking, 'grades_pass_block')
    run_blk = _safe(blocking, 'grades_run_block')
    if pass_blk == 0 and run_blk == 0:
        return None

    if pass_blk == 0:
        pass_blk = 50.0
    if run_blk == 0:
        run_blk = 50.0

    # Penalties: lower is better, normalize 0-15 range then invert
    penalties = _safe(blocking, 'penalties', 0.0)
    pen_norm = _invert(_normalize_rate(penalties, 0.0, 15.0))

    # LT snap volume (premium for left tackle snaps)
    lt_snaps = _safe(blocking, 'snap_counts_lt', 0.0)
    total_snaps = _safe(blocking, 'snap_counts_block', 1.0)
    lt_ratio = lt_snaps / max(total_snaps, 1.0)
    lt_norm = _normalize_rate(lt_ratio, 0.0, 1.0)

    return _clamp(
        pass_blk * w['pass_blocking'] +
        run_blk * w['run_blocking'] +
        pen_norm * w['penalties'] +
        lt_norm * w['lt_snap_volume']
    )


def grade_iol(blocking: dict | None, weights=None) -> float | None:
    """IOL: 45% pass block + 45% run block + 5% penalties (inv) + 5% volume"""
    w = weights if weights else DEFAULT_IOL_WEIGHTS

    pass_blk = _safe(blocking, 'grades_pass_block')
    run_blk = _safe(blocking, 'grades_run_block')
    if pass_blk == 0 and run_blk == 0:
        return None

    if pass_blk == 0:
        pass_blk = 50.0
    if run_blk == 0:
        run_blk = 50.0

    penalties = _safe(blocking, 'penalties', 0.0)
    pen_norm = _invert(_normalize_rate(penalties, 0.0, 15.0))

    total_snaps = _safe(blocking, 'snap_counts_block', 0.0)
    vol_norm = _normalize_rate(total_snaps, 200.0, 900.0)

    return _clamp(
        pass_blk * w['pass_blocking'] +
        run_blk * w['run_blocking'] +
        pen_norm * w['penalties'] +
        vol_norm * w['volume']
    )


def grade_edge(defense: dict | None, weights=None) -> float | None:
    """EDGE: 50% pass rush + 25% total pressures + 15% hurries + 10% sacks"""
    w = weights if weights else DEFAULT_EDGE_WEIGHTS

    pr_grade = _safe(defense, 'grades_pass_rush_defense')
    if pr_grade == 0:
        return None

    # Total pressures: normalize 0-80
    total_press = _safe(defense, 'total_pressures', 0.0)
    press_norm = _normalize_rate(total_press, 0.0, 80.0)

    # Hurries: normalize 0-60
    hurries = _safe(defense, 'hurries', 0.0)
    hurry_norm = _normalize_rate(hurries, 0.0, 60.0)

    # Sacks: normalize 0-18
    sacks = _safe(defense, 'sacks', 0.0)
    sack_norm = _normalize_rate(sacks, 0.0, 18.0)

    return _clamp(
        pr_grade * w['pass_rush'] +
        press_norm * w['total_pressures'] +
        hurry_norm * w['hurries'] +
        sack_norm * w['sacks']
    )


def grade_idl(defense: dict | None, weights=None) -> float | None:
    """IDL: 40% pass rush + 40% run defense + 10% volume + 5% penalties + 5% disruption"""
    w = weights if weights else DEFAULT_IDL_WEIGHTS

    pr_grade = _safe(defense, 'grades_pass_rush_defense')
    run_grade = _safe(defense, 'grades_run_defense')
    if pr_grade == 0 and run_grade == 0:
        return None

    if pr_grade == 0:
        pr_grade = 50.0
    if run_grade == 0:
        run_grade = 50.0

    # Volume: total defensive snaps
    total_snaps = _safe(defense, 'snap_counts_defense', 0.0)
    vol_norm = _normalize_rate(total_snaps, 200.0, 900.0)

    # Penalties
    penalties = _safe(defense, 'penalties', 0.0)
    pen_norm = _invert(_normalize_rate(penalties, 0.0, 12.0))

    # Disruption: TFL + pressures
    tfl = _safe(defense, 'tackles_for_loss', 0.0)
    pressures = _safe(defense, 'total_pressures', 0.0)
    disrupt_norm = _normalize_rate(tfl + pressures, 0.0, 60.0)

    return _clamp(
        pr_grade * w['pass_rush'] +
        run_grade * w['run_defense'] +
        vol_norm * w['volume'] +
        pen_norm * w['penalties'] +
        disrupt_norm * w['disruption']
    )


def grade_lb(defense: dict | None, weights=None) -> float | None:
    """LB: 25% coverage + 40% run defense + 15% pass rush + 10% volume + 10% reliability"""
    w = weights if weights else DEFAULT_LB_WEIGHTS

    cov_grade = _safe(defense, 'grades_coverage_defense')
    run_grade = _safe(defense, 'grades_run_defense')
    if cov_grade == 0 and run_grade == 0:
        return None

    if cov_grade == 0:
        cov_grade = 50.0
    if run_grade == 0:
        run_grade = 50.0

    pr_grade = _safe(defense, 'grades_pass_rush_defense', 50.0)

    total_snaps = _safe(defense, 'snap_counts_defense', 0.0)
    vol_norm = _normalize_rate(total_snaps, 200.0, 900.0)

    # Reliability: missed tackle rate inverted (0-20%)
    mtr = _safe(defense, 'missed_tackle_rate', 10.0)
    reliability = _invert(_normalize_rate(mtr, 0.0, 20.0))

    return _clamp(
        cov_grade * w['coverage'] +
        run_grade * w['run_defense'] +
        pr_grade * w['pass_rush'] +
        vol_norm * w['volume'] +
        reliability * w['reliability']
    )


def grade_cb(defense: dict | None, weights=None) -> float | None:
    """CB: 50% coverage + 15% disruption + 15% reliability + 10% volume + 10% explosiveness"""
    w = weights if weights else DEFAULT_CB_WEIGHTS

    cov_grade = _safe(defense, 'grades_coverage_defense')
    if cov_grade == 0:
        return None

    # Disruption: INTs + PBUs, normalize 0-20
    ints = _safe(defense, 'interceptions', 0.0)
    pbus = _safe(defense, 'pass_break_ups', 0.0)
    disrupt_norm = _normalize_rate(ints + pbus, 0.0, 20.0)

    # Reliability: missed tackle rate inverted
    mtr = _safe(defense, 'missed_tackle_rate', 10.0)
    reliability = _invert(_normalize_rate(mtr, 0.0, 20.0))

    # Volume: coverage snaps
    cov_snaps = _safe(defense, 'snap_counts_coverage', 0.0)
    vol_norm = _normalize_rate(cov_snaps, 100.0, 700.0)

    # Explosiveness: catch rate inverted (lower = better for CB) + forced fumbles
    catch_rate = _safe(defense, 'catch_rate', 60.0)
    catch_inv = _invert(_normalize_rate(catch_rate, 30.0, 80.0))
    ff = _safe(defense, 'forced_fumbles', 0.0)
    ff_norm = _normalize_rate(ff, 0.0, 5.0)
    explo_norm = catch_inv * 0.7 + ff_norm * 0.3

    return _clamp(
        cov_grade * w['coverage'] +
        disrupt_norm * w['disruption'] +
        reliability * w['reliability'] +
        vol_norm * w['volume'] +
        explo_norm * w['explosiveness']
    )


def grade_s(defense: dict | None, weights=None) -> float | None:
    """S: 35% coverage + 30% tackling + 15% ball production + 10% volume + 10% reliability"""
    w = weights if weights else DEFAULT_S_WEIGHTS

    cov_grade = _safe(defense, 'grades_coverage_defense')
    tackle_grade = _safe(defense, 'grades_tackle')
    if cov_grade == 0 and tackle_grade == 0:
        return None

    if cov_grade == 0:
        cov_grade = 50.0
    if tackle_grade == 0:
        tackle_grade = 50.0

    # Ball production: INTs + PBUs + forced fumbles, normalize 0-15
    ints = _safe(defense, 'interceptions', 0.0)
    pbus = _safe(defense, 'pass_break_ups', 0.0)
    ff = _safe(defense, 'forced_fumbles', 0.0)
    ball_prod = _normalize_rate(ints + pbus + ff, 0.0, 15.0)

    # Volume
    total_snaps = _safe(defense, 'snap_counts_defense', 0.0)
    vol_norm = _normalize_rate(total_snaps, 200.0, 900.0)

    # Reliability
    mtr = _safe(defense, 'missed_tackle_rate', 10.0)
    reliability = _invert(_normalize_rate(mtr, 0.0, 20.0))

    return _clamp(
        cov_grade * w['coverage'] +
        tackle_grade * w['tackling'] +
        ball_prod * w['ball_production'] +
        vol_norm * w['volume'] +
        reliability * w['reliability']
    )


# ─── Dispatcher ─────────────────────────────────────────────────────

GRADE_FUNCTIONS = {
    'QB': lambda p, rec, rush, blk, d, w: grade_qb(p, rush, weights=w),
    'RB': lambda p, rec, rush, blk, d, w: grade_rb(rush, rec, blk, weights=w),
    'WR': lambda p, rec, rush, blk, d, w: grade_wr(rec, rush, weights=w),
    'TE': lambda p, rec, rush, blk, d, w: grade_te(rec, blk, weights=w),
    'OT': lambda p, rec, rush, blk, d, w: grade_ot(blk, weights=w),
    'IOL': lambda p, rec, rush, blk, d, w: grade_iol(blk, weights=w),
    'EDGE': lambda p, rec, rush, blk, d, w: grade_edge(d, weights=w),
    'IDL': lambda p, rec, rush, blk, d, w: grade_idl(d, weights=w),
    'LB': lambda p, rec, rush, blk, d, w: grade_lb(d, weights=w),
    'CB': lambda p, rec, rush, blk, d, w: grade_cb(d, weights=w),
    'S': lambda p, rec, rush, blk, d, w: grade_s(d, weights=w),
}


def compute_core_grade(position: str, passing: dict | None, receiving: dict | None,
                       rushing: dict | None, blocking: dict | None, defense: dict | None,
                       weights: dict | None = None) -> float | None:
    """
    Compute core grade for a player based on position and stat dicts.
    Returns float 0-100 or None if insufficient data.

    Args:
        position: Player position (QB, RB, WR, TE, OT, IOL, EDGE, IDL, LB, CB, S)
        passing: Passing stats dict (or None)
        receiving: Receiving stats dict (or None)
        rushing: Rushing stats dict (or None)
        blocking: Blocking stats dict (or None)
        defense: Defense stats dict (or None)
        weights: Optional dict mapping category names to float weights.
                 If None, uses DEFAULT_WEIGHTS for the position.
                 See DEFAULT_WEIGHTS and WEIGHT_LABELS for valid keys per position.
    """
    fn = GRADE_FUNCTIONS.get(position)
    if fn is None:
        return None
    return fn(passing, receiving, rushing, blocking, defense, weights)
