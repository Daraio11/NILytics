"""
NILytics — Adjusted Value Calculation (Phase 2.6, tuned v1.1)

Applies bonuses, penalties, and experience modifiers to base_value.

Adjustments:
  Snap penalty:        snaps < 300 → -25% NIL value (even for recruit exceptions)
  Experience (non-QB): +$50K per prior T1 season w/ ≥330 snaps
                       +$150K per prior T2+ season w/ ≥330 snaps
  Experience (QB):     +$500K per prior T2 season; +$1M per prior T1 season
                       CAPPED at $2M total experience bonus
  EDGE bonus:          10+ sacks → +$250K
  RB bonus:            1200+ scrimmage yards → +$150K; 10+ TDs → +$100K
  CB bonus:            catch rate ≤45% → +$100K; ≥5 INTs → +$75K
  S elite deviation:   T1 + coverage ≥90 + 800+ snaps + (3 INTs or 8 PBUs) → +$200K-$350K
  SEC/B1G CB or S:     +$100K conference bonus
  Nickel CB penalty:   slot snap majority → T1 ineligible, -$75K (reduced from $125K)
  FCS bonuses:         50% of standard bonus values
  Value floor:         adjusted_value never drops below $25K (P4/G6) or $10K (FCS)
"""

# Maximum QB experience bonus (prevents runaway values for 4-year starters)
QB_EXP_CAP = 2_000_000


def compute_adjusted_value(
    base_value: int,
    position: str,
    market: str,
    tier: str,
    snaps_proxy: int,
    conference: str,
    # Experience history: list of dicts with keys: season, tier, snaps_proxy
    prior_seasons: list[dict] | None = None,
    # Current season stats for position bonuses
    defense_stats: dict | None = None,
    rushing_stats: dict | None = None,
    receiving_stats: dict | None = None,
) -> tuple[int, list[str]]:
    """
    Compute adjusted value from base value + all modifiers.
    Returns (adjusted_value, list_of_applied_adjustments).
    """
    value = base_value
    adjustments = []
    fcs_mult = 0.5 if market == 'FCS' else 1.0

    def _safe(d, key, default=0.0):
        if d is None:
            return default
        v = d.get(key)
        if v is None:
            return default
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    # ── Snap Penalty ──────────────────────────────────────────────
    if snaps_proxy < 300:
        penalty = round(value * 0.25)
        value -= penalty
        adjustments.append(f"Snap penalty (<300 snaps): -${penalty:,}")

    # ── Experience Bonuses ────────────────────────────────────────
    if prior_seasons:
        exp_bonus = 0
        for ps in prior_seasons:
            ps_tier = ps.get('tier')
            ps_snaps = ps.get('snaps_proxy', 0)
            ps_season = ps.get('season')

            if position == 'QB':
                if ps_tier == 'T1':
                    bonus = round(1_000_000 * fcs_mult)
                    exp_bonus += bonus
                    adjustments.append(f"QB T1 experience ({ps_season}): +${bonus:,}")
                elif ps_tier == 'T2':
                    bonus = round(500_000 * fcs_mult)
                    exp_bonus += bonus
                    adjustments.append(f"QB T2 experience ({ps_season}): +${bonus:,}")
                # Cap QB experience bonus
                qb_cap = round(QB_EXP_CAP * fcs_mult)
                if exp_bonus > qb_cap:
                    adjustments.append(f"QB experience capped at ${qb_cap:,} (was ${exp_bonus:,})")
                    exp_bonus = qb_cap
            else:
                if ps_snaps >= 330:
                    if ps_tier == 'T1':
                        bonus = round(50_000 * fcs_mult)
                        exp_bonus += bonus
                        adjustments.append(f"T1 experience ({ps_season}, {ps_snaps} snaps): +${bonus:,}")
                    elif ps_tier in ('T2', 'T3', 'T4'):
                        bonus = round(150_000 * fcs_mult)
                        exp_bonus += bonus
                        adjustments.append(f"T2+ experience ({ps_season}, {ps_snaps} snaps): +${bonus:,}")

        value += exp_bonus

    # ── Position-Specific Bonuses ─────────────────────────────────

    # EDGE: 10+ sacks
    if position == 'EDGE' and defense_stats:
        sacks = _safe(defense_stats, 'sacks')
        if sacks >= 10:
            bonus = round(250_000 * fcs_mult)
            value += bonus
            adjustments.append(f"EDGE sack bonus ({sacks:.0f} sacks): +${bonus:,}")

    # RB: 1200+ scrimmage yards, 10+ TDs
    if position == 'RB':
        rush_yards = _safe(rushing_stats, 'yards')
        rec_yards = _safe(receiving_stats, 'yards', _safe(rushing_stats, 'rec_yards'))
        total_yards = rush_yards + rec_yards
        if total_yards >= 1200:
            bonus = round(150_000 * fcs_mult)
            value += bonus
            adjustments.append(f"RB yardage bonus ({total_yards:.0f} scrimmage yds): +${bonus:,}")

        rush_tds = _safe(rushing_stats, 'touchdowns')
        rec_tds = _safe(receiving_stats, 'touchdowns')
        total_tds = rush_tds + rec_tds
        if total_tds >= 10:
            bonus = round(100_000 * fcs_mult)
            value += bonus
            adjustments.append(f"RB TD bonus ({total_tds:.0f} TDs): +${bonus:,}")

    # CB: catch rate ≤45%, ≥5 INTs
    if position == 'CB' and defense_stats:
        catch_rate = _safe(defense_stats, 'catch_rate', 100.0)
        if catch_rate <= 45.0:
            bonus = round(100_000 * fcs_mult)
            value += bonus
            adjustments.append(f"CB catch rate bonus ({catch_rate:.1f}%): +${bonus:,}")

        ints = _safe(defense_stats, 'interceptions')
        if ints >= 5:
            bonus = round(75_000 * fcs_mult)
            value += bonus
            adjustments.append(f"CB INT bonus ({ints:.0f} INTs): +${bonus:,}")

    # S: elite deviation layer
    if position == 'S' and defense_stats and tier == 'T1':
        cov_grade = _safe(defense_stats, 'grades_coverage_defense')
        total_snaps = _safe(defense_stats, 'snap_counts_defense')
        ints = _safe(defense_stats, 'interceptions')
        pbus = _safe(defense_stats, 'pass_break_ups')

        if cov_grade >= 90 and total_snaps >= 800 and (ints >= 3 or pbus >= 8):
            # Scale bonus based on how elite: $200K base, up to $350K
            elite_score = min(1.0, (cov_grade - 90) / 10)  # 0-1 scale above 90
            bonus_base = 200_000 + elite_score * 150_000
            bonus = round(bonus_base * fcs_mult)
            value += bonus
            adjustments.append(f"S elite deviation bonus (cov {cov_grade:.1f}, {ints:.0f} INT, {pbus:.0f} PBU): +${bonus:,}")

    # SEC/B1G conference bonus for CB and S
    if position in ('CB', 'S') and conference in ('SEC', 'Big Ten'):
        bonus = round(100_000 * fcs_mult)
        value += bonus
        adjustments.append(f"{conference} conference bonus: +${bonus:,}")

    # Nickel CB penalty: slot snap majority (reduced from $125K to $75K)
    if position == 'CB' and defense_stats:
        slot_snaps = _safe(defense_stats, 'snap_counts_slot')
        corner_snaps = _safe(defense_stats, 'snap_counts_corner')
        total_cb_snaps = slot_snaps + corner_snaps
        if total_cb_snaps > 0 and slot_snaps > total_cb_snaps * 0.5:
            penalty = round(75_000 * fcs_mult)
            value -= penalty
            adjustments.append(f"Nickel CB penalty (slot majority {slot_snaps:.0f}/{total_cb_snaps:.0f}): -${penalty:,}")

    # ── Value Floor ────────────────────────────────────────────────
    # No player should value at $0. Set minimum floor.
    floor = 10_000 if market == 'FCS' else 25_000
    if value < floor:
        adjustments.append(f"Value floor applied (was ${max(0, round(value)):,}, set to ${floor:,})")
        value = floor

    return round(value), adjustments
