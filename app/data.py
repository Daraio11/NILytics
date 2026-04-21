"""
NILytics — Data Access Layer for Streamlit App
Caches queries to avoid repeated DB hits.
"""
import os
import sys
from pathlib import Path

import time
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from postgrest.exceptions import APIError

# Load .env from project root (handles Streamlit's working-dir quirks)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


def _get_secret(key: str) -> str:
    """Get a secret from environment or Streamlit Cloud secrets."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        raise ValueError(f"Missing secret: {key}. Set in .env or Streamlit Cloud secrets.")


@st.cache_resource
def get_supabase():
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    return create_client(url, key)


def _paginated_fetch(query, page_size=1000, retries=3):
    """Fetch all rows with pagination and retry on transient errors."""
    all_rows = []
    offset = 0
    while True:
        for attempt in range(retries):
            try:
                resp = query.range(offset, offset + page_size - 1).execute()
                break
            except APIError as e:
                code = getattr(e, 'code', None) or (e.args[0].get('code') if e.args else None)
                if code in (502, 503, 504) and attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
                    continue
                raise
        all_rows.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size
    return all_rows


@st.cache_data(ttl=300)
def load_leaderboard(season: int):
    """Load merged leaderboard data for a given season."""
    sb = get_supabase()

    # Fetch scores
    scores = _paginated_fetch(
        sb.table('player_scores')
        .select('player_id, season, core_grade, output_score, tier, base_value, adjusted_value')
        .eq('season', season)
        .eq('model_version', 'v1.1')
    )

    # Fetch signals
    signals = _paginated_fetch(
        sb.table('alpha_signals')
        .select('player_id, season, player_value, market_value, opportunity_score, trajectory_flag, flags')
        .eq('season', season)
    )

    # Fetch players
    players = _paginated_fetch(
        sb.table('players')
        .select('player_id, name, position, school, conference, market, class_year')
    )

    scores_df = pd.DataFrame(scores)
    signals_df = pd.DataFrame(signals)
    players_df = pd.DataFrame(players)

    if scores_df.empty:
        return pd.DataFrame()

    # Merge
    merged = scores_df.merge(players_df, on='player_id', how='left')
    if not signals_df.empty:
        merged = merged.merge(
            signals_df[['player_id', 'market_value', 'opportunity_score', 'trajectory_flag', 'flags']],
            on='player_id', how='left'
        )

    # Convert numeric columns
    for col in ['core_grade', 'output_score', 'base_value', 'adjusted_value',
                'market_value', 'opportunity_score']:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors='coerce')

    # DB semantics (already correct — do NOT swap):
    #   adjusted_value (from valuation.py NIL_RANGES)   = production worth  → "Value"
    #   market_value   (from market_estimate.py)        = market rate       → "Mkt Value"
    #   opportunity_score = adjusted_value - market_value
    #   Positive alpha  = production > market → undervalued (good deal for buyer)
    #   Negative alpha  = market overpays production → overvalued

    # Merge portal/transfer status for THIS season (player entered portal before/during season)
    try:
        transfer_map = load_transfer_map(season)
        if transfer_map:
            merged['transferred'] = merged['player_id'].map(lambda pid: pid in transfer_map)
            merged['transfer_from'] = merged['player_id'].map(lambda pid: transfer_map.get(pid, {}).get('from'))
        else:
            merged['transferred'] = False
            merged['transfer_from'] = None
    except Exception:
        merged['transferred'] = False
        merged['transfer_from'] = None

    return merged


@st.cache_data(ttl=600)
def load_transfer_map(season: int) -> dict:
    """
    Return {player_id: {'from': from_school, 'to': to_school}} for players
    who transferred INTO this season (from previous season).
    """
    sb = get_supabase()
    rows = _paginated_fetch(
        sb.table('portal_history').select('player_id, season, from_school, to_school').eq('season', season)
    )
    return {
        int(r['player_id']): {'from': r.get('from_school'), 'to': r.get('to_school')}
        for r in rows
    }


def get_transfer_status(player_id: int) -> list[dict]:
    """
    Return all transfer events for a specific player, sorted by season desc.
    Each event: {'season', 'from_school', 'to_school'}
    """
    sb = get_supabase()
    resp = (sb.table('portal_history')
            .select('season, from_school, to_school')
            .eq('player_id', int(player_id))
            .order('season', desc=True)
            .execute())
    return resp.data or []


def get_team_departures(user_email: str, school: str, season: int) -> set:
    """Return the set of player_ids the user has marked as departed for this team+season."""
    sb = get_supabase()
    resp = (sb.table('team_departures')
            .select('player_id')
            .eq('user_email', user_email)
            .eq('school', school)
            .eq('season', season)
            .execute())
    return {int(r['player_id']) for r in (resp.data or [])}


def mark_player_departed(user_email: str, school: str, season: int, player_id: int):
    """Mark a single player as departed for this team+season (idempotent)."""
    sb = get_supabase()
    try:
        sb.table('team_departures').insert({
            'user_email': user_email,
            'school': school,
            'season': season,
            'player_id': int(player_id),
        }).execute()
    except Exception:
        pass  # UNIQUE constraint means already marked — safe to ignore


def unmark_player_departed(user_email: str, school: str, season: int, player_id: int):
    """Restore a player to the projected roster (removes the departure mark)."""
    sb = get_supabase()
    (sb.table('team_departures').delete()
     .eq('user_email', user_email)
     .eq('school', school)
     .eq('season', season)
     .eq('player_id', int(player_id))
     .execute())


def clear_team_departures(user_email: str, school: str, season: int):
    """Remove every departure mark for this team+season."""
    sb = get_supabase()
    (sb.table('team_departures').delete()
     .eq('user_email', user_email)
     .eq('school', school)
     .eq('season', season)
     .execute())


@st.cache_data(ttl=600)
def _load_seasons_played_map(school: str, season: int, player_ids: tuple) -> dict:
    """Return {player_id: total_seasons_with_stats_ever} for a given set of pids."""
    if not player_ids:
        return {}
    sb = get_supabase()
    # Use rushing_stats as a cheap source since every position appears somewhere.
    # Actually we need all five tables. Query each and union.
    seasons_by_pid: dict[int, set] = {}

    for table in ('passing_stats', 'rushing_stats', 'receiving_stats',
                  'blocking_stats', 'defense_stats'):
        try:
            # Batch the IN query
            batch = list(player_ids)
            rows = []
            for i in range(0, len(batch), 500):
                chunk = batch[i:i + 500]
                resp = (sb.table(table).select('player_id, season')
                        .in_('player_id', chunk).execute())
                rows.extend(resp.data or [])
            for r in rows:
                pid = int(r['player_id'])
                seasons_by_pid.setdefault(pid, set()).add(int(r['season']))
        except Exception:
            continue

    return {pid: len(ss) for pid, ss in seasons_by_pid.items()}


@st.cache_data(ttl=600)
def load_team_roster(school: str, season: int) -> pd.DataFrame:
    """
    Load the FULL roster for a team in a given season by querying all 5 PFF stats
    tables for team_name = school. Returns every player who appeared in a box score,
    whether or not they qualified for eligibility scoring.

    Merges in:
      - player_scores (core_grade, output_score, tier, adjusted_value) if available
      - alpha_signals (market_value, opportunity_score, trajectory_flag, flags) if available
      - players (name, position, class_year, etc.)
      - portal_history (transferred, transfer_from) if this season

    Adds `eligibility_status` column: 'eligible' (has v1.1 score) or 'depth'
    (played but didn't meet scoring threshold).
    """
    sb = get_supabase()

    # 1. Collect all player_ids + position + snaps per stats table
    stats_tables = [
        ('passing_stats', 'passing_snaps'),
        ('rushing_stats', 'attempts'),
        ('receiving_stats', 'routes'),
        ('blocking_stats', 'snap_counts_block'),
        ('defense_stats', 'snap_counts_defense'),
    ]

    pid_rows = {}  # pid -> {position, snaps}
    for table_name, snap_col in stats_tables:
        try:
            rows = _paginated_fetch(
                sb.table(table_name)
                .select(f'player_id, position, {snap_col}')
                .eq('team_name', school)
                .eq('season', season)
            )
            for r in rows:
                pid = r.get('player_id')
                if pid is None:
                    continue
                snaps = float(r.get(snap_col, 0) or 0)
                if pid not in pid_rows:
                    pid_rows[pid] = {'position_raw': r.get('position'), 'snaps': snaps, 'stat_table': table_name}
                else:
                    # Keep the higher snap count as the primary record
                    if snaps > pid_rows[pid]['snaps']:
                        pid_rows[pid] = {'position_raw': r.get('position'), 'snaps': snaps, 'stat_table': table_name}
        except Exception:
            continue

    if not pid_rows:
        return pd.DataFrame()

    all_pids = list(pid_rows.keys())

    # 2. Fetch player info for these pids
    players_data = {}
    batch_size = 500
    for i in range(0, len(all_pids), batch_size):
        batch = all_pids[i:i + batch_size]
        resp = (sb.table('players')
                .select('player_id, name, position, school, conference, market, class_year')
                .in_('player_id', batch)
                .execute())
        for p in resp.data or []:
            players_data[p['player_id']] = p

    # 3. Fetch scores (may be empty for depth players who didn't qualify)
    scores_data = {}
    for i in range(0, len(all_pids), batch_size):
        batch = all_pids[i:i + batch_size]
        resp = (sb.table('player_scores')
                .select('player_id, core_grade, output_score, tier, adjusted_value, base_value')
                .eq('season', season)
                .eq('model_version', 'v1.1')
                .in_('player_id', batch)
                .execute())
        for s in resp.data or []:
            scores_data[s['player_id']] = s

    # 4. Fetch alpha signals (market, opportunity) for eligible players
    signals_data = {}
    for i in range(0, len(all_pids), batch_size):
        batch = all_pids[i:i + batch_size]
        resp = (sb.table('alpha_signals')
                .select('player_id, market_value, opportunity_score, trajectory_flag, flags')
                .eq('season', season)
                .in_('player_id', batch)
                .execute())
        for s in resp.data or []:
            signals_data[s['player_id']] = s

    # 5. Fetch transfer status for the season
    try:
        transfer_map = load_transfer_map(season)
    except Exception:
        transfer_map = {}

    # 5b. Total seasons played (any stats) — proxy for remaining eligibility.
    # Class_year data is unpopulated in our DB, so seasons_played is the best
    # auto-signal for "how much college football this player has on tape."
    try:
        seasons_played_map = _load_seasons_played_map(school, season, tuple(all_pids))
    except Exception:
        seasons_played_map = {}

    # PFF → our position taxonomy
    POSITION_MAP = {
        'HB': 'RB', 'T': 'OT', 'C': 'IOL', 'G': 'IOL',
        'ED': 'EDGE', 'DI': 'IDL', 'LB': 'LB',
        'QB': 'QB', 'WR': 'WR', 'TE': 'TE', 'CB': 'CB', 'S': 'S',
    }

    # 6. Build rows
    records = []
    for pid, info in pid_rows.items():
        player = players_data.get(pid, {})
        scores = scores_data.get(pid, {})
        signals = signals_data.get(pid, {})

        pos_raw = info.get('position_raw') or player.get('position') or '?'
        position = POSITION_MAP.get(pos_raw, pos_raw)

        _seasons_played = seasons_played_map.get(pid, 1)
        record = {
            'player_id': pid,
            'name': player.get('name', f'Player {pid}'),
            'position': position,
            'position_raw': pos_raw,
            'school': player.get('school', school),
            'conference': player.get('conference', ''),
            'market': player.get('market', ''),
            'class_year': player.get('class_year', ''),
            'seasons_played': _seasons_played,
            'snaps': info.get('snaps', 0),
            'eligibility_status': 'eligible' if pid in scores_data else 'depth',
            'core_grade': scores.get('core_grade'),
            'output_score': scores.get('output_score'),
            'tier': scores.get('tier', '—'),
            'adjusted_value': scores.get('adjusted_value'),
            'market_value': signals.get('market_value'),
            'opportunity_score': signals.get('opportunity_score'),
            'trajectory_flag': signals.get('trajectory_flag'),
            'flags': signals.get('flags', '[]'),
            'transferred': pid in transfer_map,
            'transfer_from': transfer_map.get(pid, {}).get('from'),
            # Rough class estimate: seasons_played ≈ years since first appearance
            # With 5-year eligibility typical: 1→FR, 2→SO, 3→JR, 4→SR, 5+→RSR/GS
            'est_class': (
                'FR' if _seasons_played <= 1 else
                'SO' if _seasons_played == 2 else
                'JR' if _seasons_played == 3 else
                'SR' if _seasons_played == 4 else
                'GS'  # 5+
            ),
        }
        records.append(record)

    df = pd.DataFrame(records)
    # Numeric conversion for sort stability
    for col in ['core_grade', 'output_score', 'adjusted_value', 'market_value',
                'opportunity_score', 'snaps']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


@st.cache_data(ttl=300)
def load_player_history(player_id: int):
    """Load all season data for a specific player."""
    sb = get_supabase()

    scores = _paginated_fetch(
        sb.table('player_scores')
        .select('*')
        .eq('player_id', player_id)
        .eq('model_version', 'v1.1')
        .order('season')
    )

    signals = _paginated_fetch(
        sb.table('alpha_signals')
        .select('*')
        .eq('player_id', player_id)
        .order('season')
    )

    return pd.DataFrame(scores), pd.DataFrame(signals)


@st.cache_data(ttl=300)
def load_player_info(player_id: int):
    """Load player info."""
    sb = get_supabase()
    resp = sb.table('players').select('*').eq('player_id', player_id).execute()
    if resp.data:
        return resp.data[0]
    return None


@st.cache_data(ttl=300)
def load_comps(position: str, output_score: float, season: int, player_id: int, n=5):
    """Load comparable players — same position, similar output_score, same season."""
    sb = get_supabase()

    # Get players within ±5 output_score
    lo = max(0, output_score - 5)
    hi = min(100, output_score + 5)

    scores = _paginated_fetch(
        sb.table('player_scores')
        .select('player_id, output_score, tier, adjusted_value')
        .eq('season', season)
        .eq('model_version', 'v1.1')
        .gte('output_score', lo)
        .lte('output_score', hi)
        .neq('player_id', player_id)
    )

    if not scores:
        return pd.DataFrame()

    scores_df = pd.DataFrame(scores)
    pids = scores_df['player_id'].tolist()

    # Fetch player info for these
    players = []
    for i in range(0, len(pids), 50):
        batch = pids[i:i+50]
        resp = sb.table('players').select('player_id, name, position, school').in_('player_id', batch).execute()
        players.extend(resp.data)

    players_df = pd.DataFrame(players)
    if players_df.empty:
        return pd.DataFrame()

    merged = scores_df.merge(players_df, on='player_id', how='left')
    merged = merged[merged['position'] == position]

    # Fetch alpha_signals for comparable players
    comp_pids = merged['player_id'].tolist()
    signals = []
    for i in range(0, len(comp_pids), 50):
        batch = comp_pids[i:i+50]
        try:
            resp = sb.table('alpha_signals').select(
                'player_id, market_value, opportunity_score'
            ).eq('season', season).in_('player_id', batch).execute()
            signals.extend(resp.data)
        except Exception:
            pass

    if signals:
        signals_df = pd.DataFrame(signals)
        # Apply the same value swap as load_leaderboard:
        # adjusted_value (from player_scores) = market rate, market_value (from alpha_signals) = production worth
        if 'adjusted_value' in merged.columns and 'market_value' in signals_df.columns:
            merged = merged.merge(signals_df[['player_id', 'market_value', 'opportunity_score']],
                                  on='player_id', how='left')
            av_copy = merged['adjusted_value'].copy()
            merged['adjusted_value'] = merged['market_value']
            merged['market_value'] = av_copy
            merged['opportunity_score'] = merged['adjusted_value'].fillna(0) - merged['market_value'].fillna(0)
        else:
            merged = merged.merge(signals_df[['player_id', 'market_value', 'opportunity_score']],
                                  on='player_id', how='left')
    else:
        merged['market_value'] = 0
        merged['opportunity_score'] = 0

    # Sort by closest output_score
    merged['_dist'] = abs(merged['output_score'].astype(float) - output_score)
    merged = merged.sort_values('_dist').head(n).drop(columns=['_dist'])

    return merged


# ── Stat table mapping by position ──
POSITION_STAT_TABLES = {
    'QB': ['passing_stats', 'rushing_stats'],
    'RB': ['rushing_stats', 'receiving_stats'],
    'WR': ['receiving_stats'],
    'TE': ['receiving_stats', 'blocking_stats'],
    'OT': ['blocking_stats'],
    'IOL': ['blocking_stats'],
    'EDGE': ['defense_stats'],
    'IDL': ['defense_stats'],
    'LB': ['defense_stats'],
    'CB': ['defense_stats'],
    'S': ['defense_stats'],
}

# PFF position names that map to our positions
PFF_POS_MAP = {
    'QB': ['QB'],
    'RB': ['HB', 'RB', 'FB'],
    'WR': ['WR'],
    'TE': ['TE'],
    'OT': ['T', 'OT', 'LT', 'RT'],
    'IOL': ['G', 'C', 'IOL', 'LG', 'RG'],
    'EDGE': ['ED', 'EDGE', 'OLB'],
    'IDL': ['DI', 'IDL', 'DT', 'NT'],
    'LB': ['LB', 'ILB', 'MLB', 'WLB', 'SLB'],
    'CB': ['CB'],
    'S': ['S', 'FS', 'SS'],
}


@st.cache_data(ttl=300)
def load_player_stats(player_id: int, position: str, season: int = None):
    """Load raw stats for a player from the appropriate stat tables."""
    sb = get_supabase()
    tables = POSITION_STAT_TABLES.get(position, [])
    all_stats = {}

    for table in tables:
        try:
            query = sb.table(table).select('*').eq('player_id', player_id)
            if season:
                query = query.eq('season', season)
            resp = query.execute()
            if resp.data:
                all_stats[table] = resp.data
        except Exception:
            pass

    return all_stats


@st.cache_data(ttl=300)
def load_position_percentiles(position: str, season: int):
    """Load all players at a position for a season to compute percentiles."""
    sb = get_supabase()
    tables = POSITION_STAT_TABLES.get(position, [])
    pff_positions = PFF_POS_MAP.get(position, [position])
    result = {}

    for table in tables:
        try:
            all_rows = []
            for pff_pos in pff_positions:
                rows = _paginated_fetch(
                    sb.table(table).select('*').eq('season', season).eq('position', pff_pos)
                )
                all_rows.extend(rows)
            if all_rows:
                result[table] = pd.DataFrame(all_rows)
        except Exception:
            pass

    return result


@st.cache_data(ttl=300)
def load_all_position_stats_for_season(position: str, season: int):
    """
    Load all raw stat dicts for players at a position+season.
    Returns dict of player_id -> {passing: dict, receiving: dict, rushing: dict, blocking: dict, defense: dict}
    Used by the Lab page for custom weight recomputation.
    """
    sb = get_supabase()
    tables = POSITION_STAT_TABLES.get(position, [])
    table_map = {
        'passing_stats': 'passing',
        'receiving_stats': 'receiving',
        'rushing_stats': 'rushing',
        'blocking_stats': 'blocking',
        'defense_stats': 'defense',
    }

    result = {}  # player_id -> {passing: ..., receiving: ..., ...}

    for table_name in tables:
        stat_key = table_map.get(table_name, table_name)
        try:
            rows = _paginated_fetch(
                sb.table(table_name).select('*').eq('season', season)
            )
            for row in rows:
                pid = row.get('player_id')
                if pid is not None:
                    if pid not in result:
                        result[pid] = {'passing': None, 'receiving': None, 'rushing': None,
                                       'blocking': None, 'defense': None}
                    # Only keep first row per player per table
                    if result[pid][stat_key] is None:
                        result[pid][stat_key] = row
        except Exception:
            pass

    return result


@st.cache_data(ttl=300)
def load_full_player_pool(season: int):
    """
    Load ALL players who have any stat data for a season — not just eligible ones.
    Returns the normal leaderboard merged with unscored players from stat tables.
    Unscored players get a provisional core_grade from their raw PFF grades and
    are flagged with limited_sample=True.
    """
    # 1. Load the normal scored leaderboard
    scored_df = load_leaderboard(season)
    scored_pids = set(scored_df['player_id'].tolist()) if not scored_df.empty else set()

    sb = get_supabase()

    # 2. Collect all player_ids from stat tables for this season
    stat_tables_grades = {
        'passing_stats': ('grades_pass', 'passing_snaps'),
        'rushing_stats': ('grades_run', 'attempts'),
        'receiving_stats': ('grades_pass_route', 'routes'),
        'blocking_stats': ('grades_pass_block', 'snap_counts_block'),
        'defense_stats': ('grades_defense', 'snap_counts_defense'),
    }

    # For defense_stats, grades_defense doesn't exist as a single column.
    # We'll use grades_run_defense or grades_coverage_defense as proxy.
    # Let's collect raw data per player.
    unscored_players = {}  # pid -> {grade, snaps, position, stat_table}

    for table_name, (grade_col, snap_col) in stat_tables_grades.items():
        try:
            # Only fetch the columns we need
            cols = f'player_id,position,{grade_col},{snap_col}'
            # defense_stats doesn't have a single 'grades_defense' — use multiple
            if table_name == 'defense_stats':
                cols = 'player_id,position,grades_pass_rush_defense,grades_run_defense,grades_coverage_defense,snap_counts_defense'

            rows = _paginated_fetch(
                sb.table(table_name).select(cols).eq('season', season)
            )
            for row in rows:
                pid = row.get('player_id')
                if pid is None or pid in scored_pids or pid in unscored_players:
                    continue

                # Compute a representative grade
                if table_name == 'defense_stats':
                    # Average of available defense grades
                    grades = [
                        float(row.get('grades_pass_rush_defense', 0) or 0),
                        float(row.get('grades_run_defense', 0) or 0),
                        float(row.get('grades_coverage_defense', 0) or 0),
                    ]
                    valid = [g for g in grades if g > 0]
                    grade = sum(valid) / len(valid) if valid else 0
                    snaps = float(row.get('snap_counts_defense', 0) or 0)
                else:
                    grade = float(row.get(grade_col, 0) or 0)
                    snaps = float(row.get(snap_col, 0) or 0)

                pos_raw = row.get('position', '')

                # Only keep if they have SOME grade data
                if grade > 0:
                    # Update if this table gives a better grade
                    if pid not in unscored_players or grade > unscored_players[pid]['grade']:
                        unscored_players[pid] = {
                            'grade': grade,
                            'snaps': snaps,
                            'pff_position': pos_raw,
                        }
        except Exception:
            pass

    if not unscored_players:
        # No additional players found
        if not scored_df.empty:
            scored_df['limited_sample'] = False
        return scored_df

    # 3. Fetch player info for unscored players
    unscored_pids = list(unscored_players.keys())
    player_info = []
    for i in range(0, len(unscored_pids), 50):
        batch = unscored_pids[i:i+50]
        try:
            resp = sb.table('players').select(
                'player_id, name, position, school, conference, market, class_year'
            ).in_('player_id', batch).execute()
            player_info.extend(resp.data)
        except Exception:
            pass

    if not player_info:
        if not scored_df.empty:
            scored_df['limited_sample'] = False
        return scored_df

    # 4. Build DataFrame for unscored players
    unscored_rows = []
    for info in player_info:
        pid = info['player_id']
        stats = unscored_players.get(pid, {})
        grade = stats.get('grade', 0)
        snaps = stats.get('snaps', 0)
        position = info.get('position', '')
        market = info.get('market', 'P4')

        # Provisional value based on grade (very rough floor values)
        if grade >= 80:
            prov_value = 75_000 if market == 'P4' else 30_000 if market == 'G6' else 10_000
        elif grade >= 70:
            prov_value = 50_000 if market == 'P4' else 20_000 if market == 'G6' else 10_000
        else:
            prov_value = 25_000 if market in ('P4', 'G6') else 10_000

        unscored_rows.append({
            'player_id': pid,
            'season': season,
            'core_grade': round(grade, 1),
            'output_score': 0,  # No percentile ranking available
            'tier': 'UR',       # Unranked
            'base_value': prov_value,
            'adjusted_value': prov_value,
            'name': info.get('name', ''),
            'position': position,
            'school': info.get('school', ''),
            'conference': info.get('conference', ''),
            'market': market,
            'class_year': info.get('class_year', ''),
            'market_value': prov_value,
            'opportunity_score': 0,
            'trajectory_flag': None,
            'flags': '[]',
            'limited_sample': True,
            'snaps': snaps,
        })

    unscored_df = pd.DataFrame(unscored_rows)

    # 5. Add limited_sample=False to scored players and combine
    if not scored_df.empty:
        scored_df['limited_sample'] = False
        if 'snaps' not in scored_df.columns:
            scored_df['snaps'] = None
        combined = pd.concat([scored_df, unscored_df], ignore_index=True)
    else:
        combined = unscored_df

    return combined


@st.cache_data(ttl=300)
def load_stat_table_for_season(table_name: str, season: int):
    """Load all rows from a stat table for a given season. Returns DataFrame keyed by player_id."""
    sb = get_supabase()
    try:
        rows = _paginated_fetch(
            sb.table(table_name).select('*').eq('season', season)
        )
        if rows:
            df = pd.DataFrame(rows)
            # If multiple rows per player, keep the one with highest snap count or first
            if 'player_id' in df.columns and df['player_id'].duplicated().any():
                df = df.drop_duplicates(subset='player_id', keep='first')
            return df
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_recruit_prospects(class_years: list = None):
    """
    Load ESPN 300 recruit ratings from Supabase.
    Returns DataFrame with projected values for prospects who may lack PFF production.
    Default: 2025 + 2026 classes (most likely to have zero production data).
    """
    if class_years is None:
        class_years = [2025, 2026]

    sb = get_supabase()
    all_rows = []
    for year in class_years:
        try:
            rows = _paginated_fetch(
                sb.table('recruit_ratings')
                .select('*')
                .eq('recruit_class', year)
                .order('national_rank')
            )
            all_rows.extend(rows)
        except Exception:
            pass

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)

    # Import the valuation functions
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scoring.freshman_valuation import (
        espn_grade_to_tier, project_recruit_value, project_recruit_market_value, map_espn_position
    )

    # Compute projected values
    records = []
    for _, row in df.iterrows():
        rank = int(row['national_rank'])
        grade = float(row['espn_grade'])
        espn_pos = row['position']
        school = row['school_committed']
        nil_pos = map_espn_position(espn_pos)
        tier = espn_grade_to_tier(grade)
        player_value = project_recruit_value(rank, grade, espn_pos)
        market_value = project_recruit_market_value(rank, grade, espn_pos, school=school, years_remaining=4)

        records.append({
            'player_id': f"REC{row['recruit_class']}_{rank:04d}",
            'name': row['player_name'],
            'position': nil_pos,
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
            'stars': int(row['stars']),
            'recruit_rank': rank,
            'recruit_class': int(row['recruit_class']),
            'limited_sample': True,
        })

    return pd.DataFrame(records)


# ── Roster Persistence ──

def save_roster(user_email: str, name: str, season: int, roster_data: dict,
                slot_assignments: dict, off_formation: str, def_formation: str,
                budget_preset: str, roster_id: int = None) -> int:
    """Save or update a roster. Returns the roster id."""
    import json
    sb = get_supabase()
    payload = {
        'user_email': user_email,
        'name': name,
        'season': season,
        'roster_data': json.dumps({str(k): v for k, v in roster_data.items()}),
        'slot_assignments': json.dumps({str(k): v for k, v in slot_assignments.items()}),
        'off_formation': off_formation,
        'def_formation': def_formation,
        'budget_preset': budget_preset,
        'updated_at': 'now()',
    }
    if roster_id:
        resp = sb.table('saved_rosters').update(payload).eq('id', roster_id).execute()
    else:
        resp = sb.table('saved_rosters').insert(payload).execute()
    return resp.data[0]['id'] if resp.data else None


def list_rosters(user_email: str) -> list[dict]:
    """List all saved rosters for a user."""
    sb = get_supabase()
    resp = (sb.table('saved_rosters')
            .select('id, name, season, budget_preset, updated_at')
            .eq('user_email', user_email)
            .order('updated_at', desc=True)
            .execute())
    return resp.data or []


def load_roster(roster_id: int) -> dict | None:
    """Load a saved roster by id."""
    import json
    sb = get_supabase()
    resp = sb.table('saved_rosters').select('*').eq('id', roster_id).execute()
    if not resp.data:
        return None
    row = resp.data[0]
    row['roster_data'] = json.loads(row['roster_data']) if isinstance(row['roster_data'], str) else row['roster_data']
    row['slot_assignments'] = json.loads(row['slot_assignments']) if isinstance(row['slot_assignments'], str) else row['slot_assignments']
    return row


def delete_roster(roster_id: int):
    """Delete a saved roster."""
    sb = get_supabase()
    sb.table('saved_rosters').delete().eq('id', roster_id).execute()


# ── Auto-save (persists roster per user across browser sessions) ──
_AUTOSAVE_NAME = '__autosave__'


def load_autosave_roster(user_email: str) -> dict | None:
    """Fetch the auto-saved roster for this user. Returns None if none exists."""
    import json
    sb = get_supabase()
    resp = (sb.table('saved_rosters').select('*')
            .eq('user_email', user_email)
            .eq('name', _AUTOSAVE_NAME)
            .limit(1)
            .execute())
    if not resp.data:
        return None
    row = resp.data[0]
    row['roster_data'] = json.loads(row['roster_data']) if isinstance(row['roster_data'], str) else row['roster_data']
    row['slot_assignments'] = json.loads(row['slot_assignments']) if isinstance(row['slot_assignments'], str) else row['slot_assignments']
    return row


def save_autosave_roster(user_email: str, season: int, roster_data: dict,
                          slot_assignments: dict, off_formation: str, def_formation: str,
                          budget_preset: str):
    """Upsert the auto-saved roster for this user."""
    import json
    sb = get_supabase()
    payload = {
        'user_email': user_email,
        'name': _AUTOSAVE_NAME,
        'season': season,
        'roster_data': json.dumps({str(k): v for k, v in roster_data.items()}),
        'slot_assignments': json.dumps({str(k): v for k, v in slot_assignments.items()}),
        'off_formation': off_formation,
        'def_formation': def_formation,
        'budget_preset': budget_preset,
        'updated_at': 'now()',
    }
    # Does one already exist?
    existing = (sb.table('saved_rosters').select('id')
                .eq('user_email', user_email)
                .eq('name', _AUTOSAVE_NAME)
                .limit(1)
                .execute())
    if existing.data:
        sb.table('saved_rosters').update(payload).eq('id', existing.data[0]['id']).execute()
    else:
        sb.table('saved_rosters').insert(payload).execute()


# ── Player Notes & Tags ──

def get_player_note(player_id: int, user_email: str) -> dict | None:
    """Get a user's note for a player."""
    sb = get_supabase()
    resp = (sb.table('player_notes')
            .select('*')
            .eq('player_id', player_id)
            .eq('user_email', user_email)
            .execute())
    return resp.data[0] if resp.data else None


def save_player_note(player_id: int, user_email: str, note: str, tags: list[str], status: str):
    """Save or update a note for a player."""
    sb = get_supabase()
    existing = get_player_note(player_id, user_email)
    payload = {
        'player_id': player_id,
        'user_email': user_email,
        'note': note,
        'tags': tags,
        'status': status,
        'updated_at': 'now()',
    }
    if existing:
        sb.table('player_notes').update(payload).eq('id', existing['id']).execute()
    else:
        sb.table('player_notes').insert(payload).execute()


def get_all_user_notes(user_email: str) -> list[dict]:
    """Get all notes for a user (for pipeline view)."""
    sb = get_supabase()
    resp = (sb.table('player_notes')
            .select('*')
            .eq('user_email', user_email)
            .order('updated_at', desc=True)
            .execute())
    return resp.data or []


@st.cache_data(ttl=600)
def load_market_rate_history(seasons: list[int] | None = None):
    """
    Load average market rates by position across multiple seasons.
    Returns DataFrame with columns: season, position, avg_value, avg_mkt, avg_alpha, player_count
    """
    if seasons is None:
        seasons = [2022, 2023, 2024, 2025]

    rows = []
    for season in seasons:
        try:
            df = load_leaderboard(season)
            if df.empty:
                continue
            for pos in ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']:
                pos_df = df[df['position'] == pos]
                if pos_df.empty:
                    continue
                rows.append({
                    'season': season,
                    'position': pos,
                    'avg_value': pos_df['adjusted_value'].fillna(0).mean(),
                    'avg_mkt': pos_df['market_value'].fillna(0).mean(),
                    'avg_alpha': pos_df['opportunity_score'].fillna(0).mean(),
                    'median_value': pos_df['adjusted_value'].fillna(0).median(),
                    'median_mkt': pos_df['market_value'].fillna(0).median(),
                    'top10_avg_value': pos_df.nlargest(10, 'adjusted_value')['adjusted_value'].mean() if len(pos_df) >= 10 else pos_df['adjusted_value'].mean(),
                    'player_count': len(pos_df),
                })
        except Exception:
            pass

    return pd.DataFrame(rows)


def get_notes_by_status(user_email: str, status: str) -> list[dict]:
    """Get notes filtered by status."""
    sb = get_supabase()
    resp = (sb.table('player_notes')
            .select('*')
            .eq('user_email', user_email)
            .eq('status', status)
            .order('updated_at', desc=True)
            .execute())
    return resp.data or []
# Bump 20260421_163648
