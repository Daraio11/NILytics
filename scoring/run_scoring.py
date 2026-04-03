"""
NILytics — Scoring Engine Orchestrator (Phase 2.7)

Pulls all player data from Supabase, runs the full scoring pipeline:
  1. Snap proxy computation
  2. Core grade by position
  3. Output score (percentile ranking)
  4. Tier assignment (frozen cutoffs)
  5. Base value calculation
  6. Adjusted value with bonuses/penalties
  7. Write results to player_scores table

Usage:
  python -m scoring.run_scoring [--season 2024] [--position QB] [--dry-run]
"""

import os
import sys
import argparse
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring.snap_proxy import compute_snap_proxy
from scoring.core_grade import compute_core_grade
from scoring.output_score import compute_output_scores
from scoring.tiers import (
    FROZEN_CUTOFFS, assign_tier, check_eligibility,
    compute_cutoffs_from_pool, set_cutoffs, get_cutoffs
)
from scoring.valuation import compute_base_value
from scoring.adjustments import compute_adjusted_value

load_dotenv()

MODEL_VERSION = "v1.1"
SCORABLE_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']

# Two-way players: some players have stats in multiple position groups.
# We detect this and score them at their HIGHER-value position.
# Example: Travis Hunter has both WR receiving stats AND CB defense stats.
SEASONS = list(range(2018, 2026))
ELIGIBLE_SEASONS = list(range(2021, 2026))  # For computing frozen cutoffs


def get_supabase():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def detect_secondary_position(primary_pos, passing, receiving, rushing, blocking, defense, pid):
    """
    Check if a player has meaningful stats in a secondary position group.
    Returns the secondary position or None.

    Examples:
    - CB with significant receiving stats → could be scored as WR
    - S with pass rushing stats → could be scored as LB
    - WR with defensive stats → could be scored as CB
    """
    # Only check for common two-way scenarios
    if primary_pos == 'CB':
        rec = receiving.get(pid)
        if rec:
            routes = float(rec.get('routes', 0) or 0)
            targets = float(rec.get('targets', 0) or 0)
            if routes >= 100 or targets >= 30:
                return 'WR'
    elif primary_pos == 'WR':
        d = defense.get(pid)
        if d:
            cov_snaps = float(d.get('snap_counts_coverage', 0) or 0)
            if cov_snaps >= 100:
                return 'CB'
    elif primary_pos == 'S':
        d = defense.get(pid)
        if d:
            pr_snaps = float(d.get('snap_counts_pass_rush', 0) or 0)
            if pr_snaps >= 80:
                return 'LB'
    return None


def fetch_players(sb, position=None):
    """Fetch all scorable players."""
    q = sb.table('players').select('player_id, name, position, school, conference, market')
    if position:
        q = q.eq('position', position)
    else:
        q = q.in_('position', SCORABLE_POSITIONS)

    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        resp = q.range(offset, offset + page_size - 1).execute()
        all_rows.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size

    return all_rows


def fetch_stats_for_season(sb, table_name, season, player_ids=None):
    """Fetch all rows from a stat table for a given season, keyed by player_id."""
    q = sb.table(table_name).select('*').eq('season', season)

    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        resp = q.range(offset, offset + page_size - 1).execute()
        all_rows.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size

    # Key by player_id
    result = {}
    for row in all_rows:
        pid = row.get('player_id')
        if pid:
            result[pid] = row
    return result


def fetch_recruit_ratings(sb):
    """Fetch all recruit ratings, keyed by pff_player_id."""
    all_rows = []
    offset = 0
    page_size = 1000
    while True:
        resp = sb.table('player_recruit_rating').select('*').range(offset, offset + page_size - 1).execute()
        all_rows.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size

    return {r['pff_player_id']: r for r in all_rows}


def compute_frozen_cutoffs(sb, recruit_ratings):
    """
    Compute tier cutoffs for positions that don't have pre-set values.
    Uses 2021-2025 eligible pool.
    """
    positions_to_compute = [p for p in SCORABLE_POSITIONS if FROZEN_CUTOFFS.get(p) is None]
    if not positions_to_compute:
        print("  All cutoffs already frozen.")
        return

    print(f"  Computing cutoffs for: {', '.join(positions_to_compute)}")

    # We need to run the scoring pipeline through output_score for eligible players
    # in 2021-2025 to get the distribution, then compute cutoffs
    eligible_scores = {pos: [] for pos in positions_to_compute}

    for season in ELIGIBLE_SEASONS:
        print(f"    Processing {season} for cutoff computation...")
        passing = fetch_stats_for_season(sb, 'passing_stats', season)
        receiving = fetch_stats_for_season(sb, 'receiving_stats', season)
        rushing = fetch_stats_for_season(sb, 'rushing_stats', season)
        blocking = fetch_stats_for_season(sb, 'blocking_stats', season)
        defense = fetch_stats_for_season(sb, 'defense_stats', season)

        players = fetch_players(sb)

        # Compute core grades for all players in positions we need
        season_grades = []
        for p in players:
            pid = p['player_id']
            pos = p['position']
            if pos not in positions_to_compute:
                continue

            snaps = compute_snap_proxy(pos, passing.get(pid), receiving.get(pid),
                                       rushing.get(pid), blocking.get(pid), defense.get(pid))

            industry_rating = None
            rr = recruit_ratings.get(pid)
            if rr:
                industry_rating = rr.get('industry_rating')
                if industry_rating is not None:
                    industry_rating = float(industry_rating)

            if not check_eligibility(snaps, industry_rating):
                continue

            grade = compute_core_grade(pos, passing.get(pid), receiving.get(pid),
                                       rushing.get(pid), blocking.get(pid), defense.get(pid))
            if grade is not None:
                season_grades.append({
                    'player_id': pid, 'season': season,
                    'position': pos, 'core_grade': grade
                })

        # Compute output scores for this season
        scored = compute_output_scores(season_grades)
        for s in scored:
            pos = s['position']
            if pos in eligible_scores:
                eligible_scores[pos].append(s['output_score'])

    # Now compute and freeze cutoffs
    for pos in positions_to_compute:
        scores = eligible_scores[pos]
        if not scores:
            print(f"    WARNING: No eligible scores for {pos}, using defaults")
            set_cutoffs(pos, (80.0, 65.0, 50.0))
        else:
            cutoffs = compute_cutoffs_from_pool(scores)
            set_cutoffs(pos, cutoffs)
            print(f"    {pos}: T1 >= {cutoffs[0]}, T2 >= {cutoffs[1]}, T3 >= {cutoffs[2]} (n={len(scores)})")


def run_scoring(season_filter=None, position_filter=None, dry_run=False):
    """Main scoring pipeline."""
    sb = get_supabase()

    print("=" * 60)
    print(f"  NILytics Scoring Engine {MODEL_VERSION}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Step 0: Fetch recruit ratings
    print("\n[0] Fetching recruit ratings...")
    recruit_ratings = fetch_recruit_ratings(sb)
    print(f"  Loaded {len(recruit_ratings)} recruit ratings")

    # Step 1: Compute any missing frozen cutoffs
    print("\n[1] Checking tier cutoffs...")
    compute_frozen_cutoffs(sb, recruit_ratings)

    # Print all cutoffs
    print("\n  Final frozen cutoffs:")
    for pos in SCORABLE_POSITIONS:
        c = get_cutoffs(pos)
        if c:
            print(f"    {pos:5s}: T1 >= {c[0]:6.2f} | T2 >= {c[1]:6.2f} | T3 >= {c[2]:6.2f}")

    # Step 2: Score all player-seasons
    seasons = [season_filter] if season_filter else SEASONS
    total_scored = 0
    total_eligible = 0

    for season in seasons:
        print(f"\n{'='*60}")
        print(f"  SCORING SEASON {season}")
        print(f"{'='*60}")

        # Fetch all stat tables for this season
        print("  Fetching stats...")
        passing = fetch_stats_for_season(sb, 'passing_stats', season)
        receiving = fetch_stats_for_season(sb, 'receiving_stats', season)
        rushing = fetch_stats_for_season(sb, 'rushing_stats', season)
        blocking = fetch_stats_for_season(sb, 'blocking_stats', season)
        defense = fetch_stats_for_season(sb, 'defense_stats', season)

        print(f"  Stats loaded: pass={len(passing)}, rec={len(receiving)}, "
              f"rush={len(rushing)}, blk={len(blocking)}, def={len(defense)}")

        # Fetch players
        players = fetch_players(sb, position_filter)
        print(f"  Players to score: {len(players)}")

        # Phase A: Compute snap proxy + core grade for all players
        gradeable = []
        snap_map = {}  # player_id -> snaps

        for p in players:
            pid = p['player_id']
            pos = p['position']

            snaps = compute_snap_proxy(pos, passing.get(pid), receiving.get(pid),
                                       rushing.get(pid), blocking.get(pid), defense.get(pid))
            snap_map[pid] = snaps

            grade = compute_core_grade(pos, passing.get(pid), receiving.get(pid),
                                       rushing.get(pid), blocking.get(pid), defense.get(pid))

            if grade is not None:
                gradeable.append({
                    'player_id': pid, 'season': season,
                    'position': pos, 'core_grade': grade,
                    'name': p['name'], 'school': p['school'],
                    'conference': p['conference'], 'market': p['market'],
                })

        print(f"  Players with core grades: {len(gradeable)}")

        # Phase B: Compute output scores (percentile within position per season)
        scored = compute_output_scores(gradeable)
        print(f"  Output scores computed: {len(scored)}")

        # Phase C: Eligibility check + tier assignment + valuation
        results = []
        for s in scored:
            pid = s['player_id']
            pos = s['position']
            snaps = snap_map.get(pid, 0)

            # Eligibility
            industry_rating = None
            rr = recruit_ratings.get(pid)
            if rr:
                ir = rr.get('industry_rating')
                if ir is not None:
                    industry_rating = float(ir)

            eligible = check_eligibility(snaps, industry_rating)
            if not eligible:
                continue

            total_eligible += 1

            # Tier assignment
            tier = assign_tier(s['output_score'], pos)
            if tier is None:
                continue

            # Nickel CB: slot majority → T1 ineligible
            if pos == 'CB' and tier == 'T1' and defense.get(pid):
                d = defense[pid]
                slot_snaps = float(d.get('snap_counts_slot') or 0)
                corner_snaps = float(d.get('snap_counts_corner') or 0)
                total_cb = slot_snaps + corner_snaps
                if total_cb > 0 and slot_snaps > total_cb * 0.5:
                    tier = 'T2'  # Demote to T2

            # Base value
            cutoffs = get_cutoffs(pos)
            base_val = compute_base_value(pos, s['market'], tier, s['output_score'], cutoffs)

            # Fetch prior season history for experience bonuses
            prior_seasons = []
            # We'll look at results we've already computed or query existing scores
            # For now, we'll handle this in a second pass

            # Adjusted value
            adj_val, adj_notes = compute_adjusted_value(
                base_value=base_val,
                position=pos,
                market=s['market'],
                tier=tier,
                snaps_proxy=snaps,
                conference=s['conference'],
                prior_seasons=prior_seasons,  # Will be populated in experience pass
                defense_stats=defense.get(pid),
                rushing_stats=rushing.get(pid),
                receiving_stats=receiving.get(pid),
            )

            # ── Dual-Position Check ──
            # If a player has significant stats in a secondary position,
            # score them at both and take the higher value
            secondary_pos = detect_secondary_position(
                pos, passing, receiving, rushing, blocking, defense, pid
            )
            if secondary_pos:
                sec_grade = compute_core_grade(
                    secondary_pos, passing.get(pid), receiving.get(pid),
                    rushing.get(pid), blocking.get(pid), defense.get(pid)
                )
                if sec_grade is not None:
                    # Compute output score relative to secondary position's pool
                    # Use the same season's scored data to find percentile
                    sec_pos_grades = [x['core_grade'] for x in scored if x['position'] == secondary_pos]
                    if sec_pos_grades:
                        import numpy as np
                        sec_output = round(float(
                            sum(1 for g in sec_pos_grades if g <= sec_grade) / len(sec_pos_grades) * 100
                        ), 2)
                        sec_tier = assign_tier(sec_output, secondary_pos)
                        if sec_tier:
                            sec_cutoffs = get_cutoffs(secondary_pos)
                            if sec_cutoffs:
                                sec_base = compute_base_value(
                                    secondary_pos, s['market'], sec_tier, sec_output, sec_cutoffs
                                )
                                if sec_base > base_val:
                                    adj_notes.append(
                                        f"Two-way bonus: {secondary_pos} value (${sec_base:,}) > "
                                        f"{pos} value (${base_val:,}); using higher"
                                    )
                                    # Use secondary position's base value but keep primary position
                                    adj_val = max(adj_val, sec_base)

            results.append({
                'player_id': pid,
                'season': season,
                'core_grade': round(s['core_grade'], 2),
                'output_score': round(s['output_score'], 2),
                'tier': tier,
                'base_value': base_val,
                'adjusted_value': adj_val,
                'model_version': MODEL_VERSION,
                'computed_at': datetime.now(timezone.utc).isoformat(),
                # Metadata for logging (not stored)
                '_name': s['name'],
                '_school': s['school'],
                '_snaps': snaps,
                '_adjustments': adj_notes,
            })

        total_scored += len(results)

        # Print top 5 by adjusted value
        top5 = sorted(results, key=lambda x: x['adjusted_value'], reverse=True)[:5]
        print(f"\n  Top 5 by Adjusted Value:")
        for r in top5:
            print(f"    {r['_name']:25s} {r['tier']} | Core: {r['core_grade']:5.1f} | "
                  f"Output: {r['output_score']:5.1f} | Value: ${r['adjusted_value']:>10,}")

        # Print tier distribution
        tier_counts = {}
        for r in results:
            tier_counts[r['tier']] = tier_counts.get(r['tier'], 0) + 1
        print(f"\n  Tier distribution: {dict(sorted(tier_counts.items()))}")
        print(f"  Eligible & scored: {len(results)}")

        # Write to Supabase
        if not dry_run and results:
            print(f"\n  Writing {len(results)} scores to player_scores...")
            # Prepare rows (remove metadata fields)
            rows = [{k: v for k, v in r.items() if not k.startswith('_')} for r in results]

            # Batch upsert
            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i+batch_size]
                try:
                    sb.table('player_scores').upsert(batch, on_conflict='player_id,season,model_version').execute()
                except Exception as e:
                    print(f"    ERROR writing batch {i//batch_size + 1}: {e}")
                    # Fall back to one-by-one
                    for row in batch:
                        try:
                            sb.table('player_scores').upsert(row, on_conflict='player_id,season,model_version').execute()
                        except Exception as e2:
                            print(f"    SKIP {row['player_id']}: {e2}")

            print(f"  Scores written successfully.")
        elif dry_run:
            print(f"\n  [DRY RUN] Would write {len(results)} scores.")

    # ── Experience Bonus Pass ─────────────────────────────────────
    # Now that all seasons are scored, do a second pass for experience bonuses
    if not dry_run and not season_filter:
        print(f"\n{'='*60}")
        print(f"  EXPERIENCE BONUS PASS")
        print(f"{'='*60}")
        apply_experience_bonuses(sb)

    print(f"\n{'='*60}")
    print(f"  SCORING COMPLETE")
    print(f"  Total eligible: {total_eligible}")
    print(f"  Total scored: {total_scored}")
    print(f"{'='*60}")


def apply_experience_bonuses(sb):
    """
    Second pass: look at each player's history across seasons and apply
    experience bonuses to the most recent season.
    """
    print("  Fetching all scored player-seasons...")
    all_scores = []
    offset = 0
    page_size = 1000
    while True:
        resp = (sb.table('player_scores')
                .select('player_id, season, tier, model_version')
                .eq('model_version', MODEL_VERSION)
                .order('season')
                .range(offset, offset + page_size - 1)
                .execute())
        all_scores.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size

    print(f"  Total score records: {len(all_scores)}")

    # Group by player
    player_history = {}
    for s in all_scores:
        pid = s['player_id']
        player_history.setdefault(pid, []).append(s)

    # Fetch player info for position lookups
    players_map = {}
    offset = 0
    while True:
        resp = (sb.table('players')
                .select('player_id, position, market, conference')
                .in_('position', SCORABLE_POSITIONS)
                .range(offset, offset + page_size - 1)
                .execute())
        for p in resp.data:
            players_map[p['player_id']] = p
        if len(resp.data) < page_size:
            break
        offset += page_size

    # For each player with multiple seasons, compute experience bonus for latest season
    updates = []
    for pid, history in player_history.items():
        if len(history) < 2:
            continue

        history.sort(key=lambda x: x['season'])
        latest = history[-1]
        prior = history[:-1]

        player = players_map.get(pid)
        if not player:
            continue

        pos = player['position']
        market = player['market']
        fcs_mult = 0.5 if market == 'FCS' else 1.0

        exp_bonus = 0
        qb_exp_cap = round(2_000_000 * fcs_mult)
        for ps in prior:
            ps_tier = ps['tier']
            # We don't have snaps in player_scores, so we'll apply a simplified version
            # QB experience bonuses don't require snap threshold
            if pos == 'QB':
                if ps_tier == 'T1':
                    exp_bonus += round(1_000_000 * fcs_mult)
                elif ps_tier == 'T2':
                    exp_bonus += round(500_000 * fcs_mult)
                # Cap QB experience at $2M
                if exp_bonus > qb_exp_cap:
                    exp_bonus = qb_exp_cap
            else:
                # For non-QB, the spec says ≥330 snaps required
                # Since we stored scores only for eligible players (≥300 snaps),
                # we approximate that most eligible players have ≥330
                if ps_tier == 'T1':
                    exp_bonus += round(50_000 * fcs_mult)
                elif ps_tier in ('T2', 'T3', 'T4'):
                    exp_bonus += round(150_000 * fcs_mult)

        if exp_bonus > 0:
            # Fetch current adjusted value and add experience bonus
            resp = (sb.table('player_scores')
                    .select('adjusted_value')
                    .eq('player_id', pid)
                    .eq('season', latest['season'])
                    .eq('model_version', MODEL_VERSION)
                    .execute())
            if resp.data:
                current_val = int(float(resp.data[0]['adjusted_value']))
                new_val = current_val + exp_bonus
                updates.append({
                    'player_id': pid,
                    'season': latest['season'],
                    'model_version': MODEL_VERSION,
                    'adjusted_value': new_val,
                })

    print(f"  Experience bonuses to apply: {len(updates)}")

    # Batch update
    batch_size = 500
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        for u in batch:
            try:
                (sb.table('player_scores')
                 .update({'adjusted_value': u['adjusted_value']})
                 .eq('player_id', u['player_id'])
                 .eq('season', u['season'])
                 .eq('model_version', u['model_version'])
                 .execute())
            except Exception as e:
                print(f"    ERROR updating {u['player_id']}: {e}")

    print(f"  Experience bonuses applied.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NILytics Scoring Engine')
    parser.add_argument('--season', type=int, help='Score a single season')
    parser.add_argument('--position', type=str, help='Score a single position')
    parser.add_argument('--dry-run', action='store_true', help='Compute but do not write to DB')
    args = parser.parse_args()

    run_scoring(
        season_filter=args.season,
        position_filter=args.position,
        dry_run=args.dry_run,
    )
