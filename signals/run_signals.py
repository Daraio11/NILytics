"""
NILytics — Alpha Signal Orchestrator (Phase 3.6)

Pulls scored players from player_scores, computes market estimates,
opportunity scores, trajectory flags, and auto-flags.
Writes results to alpha_signals and nil_market_estimates tables.

Usage:
  python -m signals.run_signals [--season 2024] [--dry-run]
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signals.market_estimate import estimate_market_value
from signals.opportunity import compute_opportunity_score
from signals.trajectory import compute_trajectory
from signals.flags import compute_flags

load_dotenv()

MODEL_VERSION = "v1.1"
SEASONS = list(range(2018, 2026))


def get_supabase():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def paginated_fetch(query, page_size=1000):
    """Generic paginated fetch for Supabase queries."""
    all_rows = []
    offset = 0
    while True:
        resp = query.range(offset, offset + page_size - 1).execute()
        all_rows.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size
    return all_rows


def run_signals(season_filter=None, dry_run=False):
    sb = get_supabase()

    print("=" * 60)
    print("  NILytics Alpha Signal Engine")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 1. Fetch ALL player_scores (need full history for trajectory even if filtering output)
    print("\n[1] Fetching player scores...")
    q = sb.table('player_scores').select('player_id, season, core_grade, output_score, tier, adjusted_value, model_version').eq('model_version', MODEL_VERSION)
    all_scores = paginated_fetch(q)
    print(f"  Loaded {len(all_scores)} score records")

    # 2. Fetch player info (position, school, conference, market, class_year)
    print("\n[2] Fetching player info...")
    players_raw = paginated_fetch(
        sb.table('players').select('player_id, name, position, school, conference, market, class_year')
    )
    players = {p['player_id']: p for p in players_raw}
    print(f"  Loaded {len(players)} players")

    # 3. Fetch recruit ratings
    print("\n[3] Fetching recruit ratings...")
    recruits_raw = paginated_fetch(
        sb.table('player_recruit_rating').select('pff_player_id, star_rating')
    )
    recruits = {r['pff_player_id']: r for r in recruits_raw}
    print(f"  Loaded {len(recruits)} recruit ratings")

    # 4. Group scores by player for trajectory
    print("\n[4] Computing trajectories...")
    player_seasons = {}
    for s in all_scores:
        pid = s['player_id']
        player_seasons.setdefault(pid, []).append(s)

    # Sort each player's seasons
    for pid in player_seasons:
        player_seasons[pid].sort(key=lambda x: x['season'])

    # 5. Process each player-season
    seasons = [season_filter] if season_filter else SEASONS
    total_signals = 0
    total_market_estimates = 0

    for season in seasons:
        print(f"\n{'=' * 60}")
        print(f"  PROCESSING SEASON {season}")
        print(f"{'=' * 60}")

        season_scores = [s for s in all_scores if s['season'] == season]
        print(f"  Scored players this season: {len(season_scores)}")

        alpha_rows = []
        market_rows = []

        for s in season_scores:
            pid = s['player_id']
            player = players.get(pid)
            if not player:
                continue

            pos = player['position']
            market = player['market']
            conference = player['conference']
            tier = s['tier']
            output_score = float(s['output_score'])
            adjusted_value = int(float(s['adjusted_value']))

            # Market estimate (seeded by player_id + season for reproducibility)
            seed = pid * 10000 + season
            market_value, confidence = estimate_market_value(
                position=pos,
                market=market,
                tier=tier,
                output_score=output_score,
                conference=conference or '',
                seed=seed,
            )

            # Opportunity score
            opp_score = compute_opportunity_score(adjusted_value, market_value)

            # Trajectory (uses ALL seasons for this player, not just current filter)
            history = player_seasons.get(pid, [])
            # Only include seasons up to current for trajectory
            history_up_to = [h for h in history if h['season'] <= season]
            trajectory = compute_trajectory(history_up_to)

            # Count total seasons scored for this player
            seasons_scored = len(history_up_to)

            # Recruit info
            recruit = recruits.get(pid)
            star_rating = None
            if recruit and recruit.get('star_rating'):
                star_rating = float(recruit['star_rating'])

            class_year = player.get('class_year')

            # Auto-flags
            flag_list = compute_flags(
                player_id=pid,
                position=pos,
                market=market,
                tier=tier,
                output_score=output_score,
                opportunity_score=opp_score,
                trajectory_flag=trajectory,
                star_rating=star_rating,
                class_year=class_year,
                seasons_scored=seasons_scored,
            )

            # Build alpha_signals row
            alpha_rows.append({
                'player_id': pid,
                'season': season,
                'player_value': adjusted_value,
                'market_value': market_value,
                'opportunity_score': opp_score,
                'trajectory_flag': trajectory,
                'flags': json.dumps(flag_list),
                'computed_at': datetime.now(timezone.utc).isoformat(),
            })

            # Build nil_market_estimates row
            market_rows.append({
                'player_id': pid,
                'season': season,
                'estimated_market_value': market_value,
                'source': 'nilytics_model_v1',
                'confidence_band': confidence,
                'scraped_at': datetime.now(timezone.utc).isoformat(),
            })

        total_signals += len(alpha_rows)
        total_market_estimates += len(market_rows)

        # Stats
        if alpha_rows:
            undervalued = sum(1 for r in alpha_rows if r['opportunity_score'] > 0)
            overvalued = sum(1 for r in alpha_rows if r['opportunity_score'] < 0)
            flag_counts = {}
            for r in alpha_rows:
                for f in json.loads(r['flags']):
                    flag_counts[f] = flag_counts.get(f, 0) + 1
            traj_counts = {}
            for r in alpha_rows:
                t = r['trajectory_flag']
                traj_counts[t] = traj_counts.get(t, 0) + 1

            print(f"\n  Undervalued: {undervalued} | Overvalued: {overvalued}")
            print(f"  Trajectory: {dict(sorted(traj_counts.items()))}")
            print(f"  Flags: {dict(sorted(flag_counts.items()))}")

            # Top 5 undervalued (Moneyball picks)
            top_under = sorted(alpha_rows, key=lambda x: x['opportunity_score'], reverse=True)[:5]
            print(f"\n  Top 5 Undervalued (Moneyball Picks):")
            for r in top_under:
                p = players.get(r['player_id'], {})
                print(f"    {p.get('name','?'):25s} {p.get('position','?'):5s} | "
                      f"Value: ${r['player_value']:>10,} | Market: ${r['market_value']:>10,} | "
                      f"Alpha: ${r['opportunity_score']:>+10,} | {r['trajectory_flag']}")

            # Top 5 overvalued
            top_over = sorted(alpha_rows, key=lambda x: x['opportunity_score'])[:5]
            print(f"\n  Top 5 Overvalued:")
            for r in top_over:
                p = players.get(r['player_id'], {})
                print(f"    {p.get('name','?'):25s} {p.get('position','?'):5s} | "
                      f"Value: ${r['player_value']:>10,} | Market: ${r['market_value']:>10,} | "
                      f"Alpha: ${r['opportunity_score']:>+10,} | {r['trajectory_flag']}")

        # Write to DB
        if not dry_run and alpha_rows:
            print(f"\n  Writing {len(alpha_rows)} alpha signals...")
            batch_size = 500
            for i in range(0, len(alpha_rows), batch_size):
                batch = alpha_rows[i:i + batch_size]
                try:
                    sb.table('alpha_signals').upsert(
                        batch, on_conflict='player_id,season'
                    ).execute()
                except Exception as e:
                    print(f"    ERROR batch {i // batch_size + 1}: {e}")
                    for row in batch:
                        try:
                            sb.table('alpha_signals').upsert(
                                row, on_conflict='player_id,season'
                            ).execute()
                        except Exception as e2:
                            print(f"    SKIP {row['player_id']}: {e2}")
            print("  Alpha signals written.")

            print(f"  Writing {len(market_rows)} market estimates...")
            for i in range(0, len(market_rows), batch_size):
                batch = market_rows[i:i + batch_size]
                try:
                    sb.table('nil_market_estimates').upsert(
                        batch, on_conflict='player_id,season'
                    ).execute()
                except Exception as e:
                    print(f"    ERROR batch {i // batch_size + 1}: {e}")
                    for row in batch:
                        try:
                            sb.table('nil_market_estimates').upsert(
                                row, on_conflict='player_id,season'
                            ).execute()
                        except Exception as e2:
                            print(f"    SKIP {row['player_id']}: {e2}")
            print("  Market estimates written.")
        elif dry_run:
            print(f"\n  [DRY RUN] Would write {len(alpha_rows)} signals + {len(market_rows)} market estimates.")

    print(f"\n{'=' * 60}")
    print(f"  ALPHA SIGNALS COMPLETE")
    print(f"  Total signals: {total_signals}")
    print(f"  Total market estimates: {total_market_estimates}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NILytics Alpha Signal Engine')
    parser.add_argument('--season', type=int, help='Process a single season')
    parser.add_argument('--dry-run', action='store_true', help='Compute but do not write')
    args = parser.parse_args()

    run_signals(season_filter=args.season, dry_run=args.dry_run)
