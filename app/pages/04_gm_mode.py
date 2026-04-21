"""
NILytics — GM Mode
Build your roster under a budget. Find out if you're getting value or overpaying.
"""
import json
import math
import streamlit as st
import pandas as pd

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import (load_leaderboard, load_full_player_pool, load_stat_table_for_season,
                       POSITION_STAT_TABLES, save_roster, list_rosters, load_roster, delete_roster,
                       load_autosave_roster, save_autosave_roster)
from app.components.filters import POSITIONS, MARKETS
from app.components.card_front import fmt_money
from app.components.exports import export_roster_csv
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar
from scoring.freshman_valuation import load_recruits_from_csv, load_all_prospects

st.set_page_config(page_title="NILytics — GM Mode", page_icon="🏈", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

# GM Mode uses the sidebar for controls — user opens it via hamburger toggle

# ── Page-specific CSS ──
st.markdown("""
<style>
/* ── View toggle: restyle radio as segmented pill control ── */
.stRadio > div[role="radiogroup"] {
    display: inline-flex !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 8px !important;
    background: #f6f8fa !important;
    overflow: hidden !important;
    gap: 0 !important;
    padding: 2px !important;
}
.stRadio > div[role="radiogroup"] > label {
    padding: 6px 18px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border: none !important;
    background: transparent !important;
    cursor: pointer !important;
    color: #6b7280 !important;
    transition: all 0.15s !important;
    margin: 0 !important;
    border-radius: 6px !important;
    white-space: nowrap !important;
}
.stRadio > div[role="radiogroup"] > label p,
.stRadio > div[role="radiogroup"] > label span {
    color: #6b7280 !important;
}
.stRadio > div[role="radiogroup"] > label:hover {
    background: #e5e7eb !important;
}
.stRadio > div[role="radiogroup"] > label > div:first-child {
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}
.stRadio > div[role="radiogroup"] > label[data-checked="true"],
.stRadio > div[role="radiogroup"] > label:has(input:checked) {
    background: #E8390E !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
}
.stRadio > div[role="radiogroup"] > label[data-checked="true"] p,
.stRadio > div[role="radiogroup"] > label[data-checked="true"] span,
.stRadio > div[role="radiogroup"] > label:has(input:checked) p,
.stRadio > div[role="radiogroup"] > label:has(input:checked) span {
    color: #FFFFFF !important;
}

/* ── GM action buttons — ultra-compact ── */
.gm-action-col .stButton > button {
    height: 26px !important;
    width: 32px !important;
    min-height: 0 !important;
    padding: 0 !important;
    border-radius: 4px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    line-height: 26px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ── Mono class ── */
.mono { font-family: 'DM Mono', 'SF Mono', 'Fira Code', monospace; }

/* ── Reduce whitespace ── */
hr { margin: 0.4rem 0 !important; }
.stRadio { margin-bottom: 0 !important; }

/* ── Flag filter buttons: restyle Streamlit primary/secondary buttons ── */
div[data-testid="stHorizontalBlock"] .stButton > button {
    height: 36px !important;
    padding: 0 14px !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
    transition: all 0.15s !important;
    line-height: 1 !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
    background: #f3f4f6 !important;
    border: 1px solid #e5e7eb !important;
    color: #6b7280 !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"]:hover {
    background: #e5e7eb !important;
    border-color: #E8390E !important;
    color: #E8390E !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
    background: #E8390E !important;
    border: 1px solid #E8390E !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"]:hover {
    background: #CC3210 !important;
    border-color: #CC3210 !important;
    color: #FFFFFF !important;
}

/* ── Sort arrows ── */
.sort-arrows { font-size: 8px; color: #4B5563; margin-left: 4px; letter-spacing: -1px; opacity: 0.5; }

/* ── Compact buttons everywhere ── */
.stButton > button { min-height: 0 !important; padding: 4px 10px !important; }

/* ── Player row styling ── */
.gm-row {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 5px 8px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 12px;
    min-height: 34px;
    color: #1f2937;
}
.gm-row:hover { background: #f9fafb; }
.gm-header {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 6px 8px;
    background: #f6f8fa;
    border-bottom: 2px solid #e5e7eb;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #6b7280;
}
.gm-cell { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.gm-roster-mark { color: #16A34A; font-weight: 700; margin-right: 3px; }

/* Compact dataframe styling */
div[data-testid="stDataFrame"] table {
    font-size: 11px !important;
}
div[data-testid="stDataFrame"] th {
    font-size: 10px !important;
    padding: 4px 6px !important;
    background: #3a4553 !important;
    color: #ffffff !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}
div[data-testid="stDataFrame"] td {
    padding: 3px 5px !important;
    font-size: 11px !important;
}
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='gm_mode')
user = check_auth()
render_user_sidebar()

# Initialize session state for roster
if 'gm_roster' not in st.session_state:
    st.session_state['gm_roster'] = {}  # {player_id: row_dict}

# Initialize session state for slot assignments
if 'gm_slot_assignments' not in st.session_state:
    st.session_state['gm_slot_assignments'] = {}  # {slot_key: player_id}

# Initialize pagination state
if 'gm_market_page' not in st.session_state:
    st.session_state['gm_market_page'] = 0

# ── AUTO-LOAD: pull persisted roster from DB on first visit this session ──
_autoload_email = user.get('email', 'test@nilytics.com')
if (not st.session_state.get('gm_autoload_done')
        and not st.session_state['gm_roster']):
    try:
        _auto = load_autosave_roster(_autoload_email)
        if _auto and _auto.get('roster_data'):
            st.session_state['gm_roster'] = {int(k): v for k, v in _auto['roster_data'].items()}
            _slots = _auto.get('slot_assignments') or {}
            st.session_state['gm_slot_assignments'] = _slots if isinstance(_slots, dict) else {}
            if _auto.get('off_formation'):
                st.session_state['off_formation'] = _auto['off_formation']
            if _auto.get('def_formation'):
                st.session_state['def_formation'] = _auto['def_formation']
    except Exception:
        pass  # Autoload is best-effort — don't block page on DB errors
    st.session_state['gm_autoload_done'] = True


def _autosave_roster():
    """Persist current GM roster state to DB under the reserved autosave slot."""
    try:
        save_autosave_roster(
            user_email=user.get('email', 'test@nilytics.com'),
            season=st.session_state.get('gm_season', 2025),
            roster_data=st.session_state.get('gm_roster', {}),
            slot_assignments=st.session_state.get('gm_slot_assignments', {}),
            off_formation=st.session_state.get('off_formation', 'Pro'),
            def_formation=st.session_state.get('def_formation', '4-3'),
            budget_preset=st.session_state.get('gm_budget_preset', 'Elite P4 Program'),
        )
    except Exception:
        pass  # Autosave is best-effort — don't block UX on DB errors

# ── Sidebar: Budget Setup ──
st.sidebar.markdown("### Budget")

PRESET_BUDGETS = {
    "Elite P4 Program": 30_000_000,
    "Competitive P4": 20_000_000,
    "Mid-Tier P4": 12_000_000,
    "G6 Contender": 6_000_000,
    "G6 Standard": 3_000_000,
    "FCS Program": 1_500_000,
    "Custom": 0,
}

budget_choice = st.sidebar.selectbox("Preset Budget", list(PRESET_BUDGETS.keys()))

if budget_choice == "Custom":
    budget = st.sidebar.number_input("Enter Budget ($)", min_value=500_000,
                                      max_value=100_000_000, value=15_000_000,
                                      step=500_000, format="%d")
else:
    budget = PRESET_BUDGETS[budget_choice]
    st.sidebar.markdown(f"**Budget: {fmt_money(budget)}**")

season = st.sidebar.selectbox("Season", list(range(2025, 2017, -1)), index=0, key="gm_season")

st.sidebar.markdown("---")
st.sidebar.markdown("### Player Pool")
show_all_players = st.sidebar.checkbox("Show all players", value=True, key="gm_show_all",
                                        help="When checked, shows all 3,600+ eligible players. Uncheck to show only players matching your position/tier filters.")

# ── Sidebar: Save / Load Rosters ──
st.sidebar.markdown("---")
st.sidebar.markdown("### Saved Rosters")
user_email = user.get('email', 'test@nilytics.com')

# Initialize active roster tracking
if 'gm_active_roster_id' not in st.session_state:
    st.session_state['gm_active_roster_id'] = None
if 'gm_active_roster_name' not in st.session_state:
    st.session_state['gm_active_roster_name'] = None

# Save current roster
_save_cols = st.sidebar.columns([3, 1])
with _save_cols[0]:
    _save_name = st.text_input(
        "Roster name",
        value=st.session_state.get('gm_active_roster_name', ''),
        placeholder="e.g. My Dream Team",
        label_visibility="collapsed",
        key="gm_save_name_input",
    )
with _save_cols[1]:
    _save_clicked = st.button("💾", key="gm_save_btn", help="Save current roster",
                              disabled=len(st.session_state.get('gm_roster', {})) == 0)

if _save_clicked and _save_name:
    _rid = save_roster(
        user_email=user_email,
        name=_save_name,
        season=season,
        roster_data=st.session_state.get('gm_roster', {}),
        slot_assignments=st.session_state.get('gm_slot_assignments', {}),
        off_formation=st.session_state.get('off_formation', 'Pro'),
        def_formation=st.session_state.get('def_formation', '4-3'),
        budget_preset=budget_choice,
        roster_id=st.session_state.get('gm_active_roster_id'),
    )
    st.session_state['gm_active_roster_id'] = _rid
    st.session_state['gm_active_roster_name'] = _save_name
    st.sidebar.success(f"Saved '{_save_name}'")
    st.rerun()
elif _save_clicked and not _save_name:
    st.sidebar.warning("Enter a name first")

# Load saved rosters list
_saved = list_rosters(user_email)
if _saved:
    for r in _saved:
        _r_cols = st.sidebar.columns([4, 1, 1])
        _is_active = st.session_state.get('gm_active_roster_id') == r['id']
        _label = f"**{r['name']}**" if _is_active else r['name']
        _r_cols[0].markdown(f"{_label}<br><span style='font-size:11px;color:#6b7280;'>{r['season']} · {r['budget_preset']}</span>",
                           unsafe_allow_html=True)
        if _r_cols[1].button("📂", key=f"load_{r['id']}", help="Load this roster"):
            loaded = load_roster(r['id'])
            if loaded:
                # Restore roster state — convert string keys back to int
                raw_roster = loaded['roster_data']
                st.session_state['gm_roster'] = {int(k): v for k, v in raw_roster.items()}
                raw_slots = loaded['slot_assignments']
                st.session_state['gm_slot_assignments'] = raw_slots if isinstance(raw_slots, dict) else {}
                st.session_state['gm_active_roster_id'] = r['id']
                st.session_state['gm_active_roster_name'] = loaded['name']
                st.rerun()
        if _r_cols[2].button("🗑", key=f"del_{r['id']}", help="Delete this roster"):
            delete_roster(r['id'])
            if st.session_state.get('gm_active_roster_id') == r['id']:
                st.session_state['gm_active_roster_id'] = None
                st.session_state['gm_active_roster_name'] = None
            st.rerun()
else:
    st.sidebar.caption("No saved rosters yet. Build a roster and save it.")

# ── Load Data ──
with st.spinner(""):
    if show_all_players:
        df = load_full_player_pool(season)
    else:
        df = load_leaderboard(season)
        if not df.empty:
            df['limited_sample'] = False

if df.empty:
    st.warning(f"No data for {season}.")
    st.stop()


# ── Shared Constants ──
TIER_COLORS = {
    'T1': '#E63B2E', 'T2': '#E8712B', 'T3': '#666', 'T4': '#bbb', 'UR': '#9ca3af',
}
TRAJ_DISPLAY = {
    'BREAKOUT': ('⬆⬆', '#E8712B', '800'),
    'UP':       ('⬆', '#1a8a3f', '700'),
    'STABLE':   ('➡', '#888', '600'),
    'DOWN':     ('⬇', '#E63B2E', '700'),
}
FLAG_CONFIG = {
    'BREAKOUT_CANDIDATE': {'icon': '🚀', 'label': 'Breakout'},
    'HIDDEN_GEM':         {'icon': '💎', 'label': 'Hidden Gem'},
    'REGRESSION_RISK':    {'icon': '📉', 'label': 'Regression'},
    'PORTAL_VALUE':       {'icon': '🔄', 'label': 'Portal Value'},
    'EXPERIENCE_PREMIUM': {'icon': '🎖️', 'label': 'Experienced'},
}

# Position-specific key stats to show as extra columns
POSITION_KEY_STATS = {
    'QB': [
        ('Yards', 'yards', 'passing_stats', ','),
        ('TDs', 'touchdowns', 'passing_stats', ','),
        ('INTs', 'interceptions', 'passing_stats', ','),
        ('Comp%', 'completion_percent', 'passing_stats', '.1f'),
        ('QBR', 'qb_rating', 'passing_stats', '.1f'),
        ('YPA', 'ypa', 'passing_stats', '.1f'),
    ],
    'RB': [
        ('Rush Yds', 'yards', 'rushing_stats', ','),
        ('Rush TDs', 'touchdowns', 'rushing_stats', ','),
        ('YPA', 'ypa', 'rushing_stats', '.1f'),
        ('Rec', 'receptions', 'receiving_stats', ','),
        ('Rec Yds', 'yards', 'receiving_stats', ','),
    ],
    'WR': [
        ('Rec', 'receptions', 'receiving_stats', ','),
        ('Rec Yds', 'yards', 'receiving_stats', ','),
        ('Rec TDs', 'touchdowns', 'receiving_stats', ','),
        ('Tgts', 'targets', 'receiving_stats', ','),
        ('YPRR', 'yprr', 'receiving_stats', '.2f'),
        ('Drop%', 'drop_rate', 'receiving_stats', '.1f'),
    ],
    'TE': [
        ('Rec', 'receptions', 'receiving_stats', ','),
        ('Rec Yds', 'yards', 'receiving_stats', ','),
        ('Rec TDs', 'touchdowns', 'receiving_stats', ','),
        ('PB Grade', 'grades_pass_block', 'blocking_stats', '.1f'),
        ('RB Grade', 'grades_run_block', 'blocking_stats', '.1f'),
    ],
    'OT': [
        ('PB Grade', 'grades_pass_block', 'blocking_stats', '.1f'),
        ('RB Grade', 'grades_run_block', 'blocking_stats', '.1f'),
        ('PBE', 'pbe', 'blocking_stats', '.1f'),
        ('Sacks Allow', 'sacks_allowed', 'blocking_stats', ','),
        ('Press Allow', 'pressures_allowed', 'blocking_stats', ','),
        ('Snaps', 'snap_counts_block', 'blocking_stats', ','),
    ],
    'IOL': [
        ('PB Grade', 'grades_pass_block', 'blocking_stats', '.1f'),
        ('RB Grade', 'grades_run_block', 'blocking_stats', '.1f'),
        ('PBE', 'pbe', 'blocking_stats', '.1f'),
        ('Press Allow', 'pressures_allowed', 'blocking_stats', ','),
        ('Snaps', 'snap_counts_block', 'blocking_stats', ','),
    ],
    'EDGE': [
        ('Sacks', 'sacks', 'defense_stats', ','),
        ('Pressures', 'total_pressures', 'defense_stats', ','),
        ('Hurries', 'hurries', 'defense_stats', ','),
        ('TFLs', 'tackles_for_loss', 'defense_stats', ','),
        ('Tackles', 'tackles', 'defense_stats', ','),
        ('PR Grade', 'grades_pass_rush_defense', 'defense_stats', '.1f'),
    ],
    'IDL': [
        ('Sacks', 'sacks', 'defense_stats', ','),
        ('Pressures', 'total_pressures', 'defense_stats', ','),
        ('TFLs', 'tackles_for_loss', 'defense_stats', ','),
        ('Tackles', 'tackles', 'defense_stats', ','),
        ('Stops', 'stops', 'defense_stats', ','),
        ('RD Grade', 'grades_run_defense', 'defense_stats', '.1f'),
    ],
    'LB': [
        ('Tackles', 'tackles', 'defense_stats', ','),
        ('TFLs', 'tackles_for_loss', 'defense_stats', ','),
        ('Stops', 'stops', 'defense_stats', ','),
        ('INTs', 'interceptions', 'defense_stats', ','),
        ('PBUs', 'pass_break_ups', 'defense_stats', ','),
        ('Cov Grade', 'grades_coverage_defense', 'defense_stats', '.1f'),
    ],
    'CB': [
        ('INTs', 'interceptions', 'defense_stats', ','),
        ('PBUs', 'pass_break_ups', 'defense_stats', ','),
        ('Tgts', 'targets', 'defense_stats', ','),
        ('Catch%', 'catch_rate', 'defense_stats', '.1f'),
        ('Cov Grade', 'grades_coverage_defense', 'defense_stats', '.1f'),
        ('Yds Allow', 'yards', 'defense_stats', ','),
    ],
    'S': [
        ('Tackles', 'tackles', 'defense_stats', ','),
        ('INTs', 'interceptions', 'defense_stats', ','),
        ('PBUs', 'pass_break_ups', 'defense_stats', ','),
        ('Cov Grade', 'grades_coverage_defense', 'defense_stats', '.1f'),
        ('RD Grade', 'grades_run_defense', 'defense_stats', '.1f'),
        ('TFLs', 'tackles_for_loss', 'defense_stats', ','),
    ],
}


def _fmt_stat(val, fmt):
    """Format a stat value for the table."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return '--'
    try:
        if fmt == ',':
            return f"{int(float(val)):,}"
        elif fmt.startswith('.'):
            return f"{float(val):{fmt}}"
        return str(val)
    except (ValueError, TypeError):
        return '--'


def _grade_color(cg):
    if cg >= 90: return '#00aa55'
    elif cg >= 80: return '#2196F3'
    elif cg >= 70: return '#FFB300'
    elif cg >= 60: return '#E8712B'
    else: return '#E63B2E'


def _normalize_pid(pid):
    """Convert player_id to native Python type for reliable session_state persistence."""
    if isinstance(pid, str):
        return pid
    try:
        return int(pid)
    except (ValueError, TypeError):
        return pid


def _add_to_roster(pid, row_dict):
    """Callback: add a player to roster."""
    pid = _normalize_pid(pid)
    # Convert numpy types to native Python for session_state serialization
    clean_dict = {}
    for k, v in row_dict.items():
        try:
            if hasattr(v, 'item'):  # numpy scalar
                clean_dict[k] = v.item()
            else:
                clean_dict[k] = v
        except Exception:
            clean_dict[k] = v
    st.session_state['gm_roster'][pid] = clean_dict
    _autosave_roster()


def _remove_from_roster(pid):
    """Callback: remove a player from roster."""
    pid = _normalize_pid(pid)
    if pid in st.session_state['gm_roster']:
        del st.session_state['gm_roster'][pid]
    # Also clean up any slot assignments referencing this player
    slots = st.session_state.get('gm_slot_assignments', {})
    keys_to_remove = [k for k, v in slots.items() if v == pid]
    for k in keys_to_remove:
        del slots[k]
    _autosave_roster()


def _add_players_from_multiselect(selected_names, name_to_row):
    """Callback: add multiple players from multiselect."""
    for name in selected_names:
        if name in name_to_row:
            row_dict = name_to_row[name]
            pid = _normalize_pid(row_dict.get('player_id', 0))
            _add_to_roster(pid, row_dict)


def _set_market_page(page):
    """Callback: set market page number."""
    st.session_state['gm_market_page'] = page


def _load_stats_for_position(position, season):
    """Load stat tables relevant to a position. Returns dict of table_name -> DataFrame."""
    tables = POSITION_STAT_TABLES.get(position, [])
    stat_data = {}
    for tbl in tables:
        stat_data[tbl] = load_stat_table_for_season(tbl, season)
    return stat_data


def _get_stat_val(pid, stat_key, stat_table, stat_data):
    """Get a single stat value for a player from preloaded stat data."""
    if stat_data and stat_table in stat_data and not stat_data[stat_table].empty:
        sdf = stat_data[stat_table]
        player_row = sdf[sdf['player_id'] == pid]
        if not player_row.empty and stat_key in player_row.columns:
            return player_row.iloc[0].get(stat_key)
    return None


def _render_player_row_html(row, rank, roster_ids, stat_cols=None, stat_data=None):
    """Build a single-row HTML string (no <table>, just inline styled divs) for a player."""
    pid = row.get('player_id', 0)
    pos = row.get('position', '--')
    tier = row.get('tier', 'T4')
    tier_color = TIER_COLORS.get(tier, '#bbb')
    name = row.get('name', '?')
    school = row.get('school', '--')

    cg = float(row['core_grade']) if pd.notna(row.get('core_grade')) else 0
    out = float(row['output_score']) if pd.notna(row.get('output_score')) else 0
    av = row.get('adjusted_value', 0)
    mv = row.get('market_value', 0)
    alpha = row.get('opportunity_score', 0)

    gc = _grade_color(cg)
    oc = '#00aa55' if out >= 90 else '#2196F3' if out >= 80 else '#FFB300' if out >= 70 else '#E8712B' if out >= 60 else '#E63B2E'

    alpha_val = int(float(alpha)) if pd.notna(alpha) else 0
    if alpha_val > 50000:
        alpha_html = f'<span style="color:#1a8a3f;font-weight:700;">+{fmt_money(abs(alpha_val))}</span>'
    elif alpha_val < -50000:
        alpha_html = f'<span style="color:#E63B2E;font-weight:700;">-{fmt_money(abs(alpha_val))}</span>'
    else:
        _neutral_prefix = '+' if alpha_val > 0 else '-' if alpha_val < 0 else ''
        alpha_html = f'<span style="color:#888;">{_neutral_prefix}{fmt_money(abs(alpha_val))}</span>'

    traj = row.get('trajectory_flag', 'STABLE') or 'STABLE'
    traj_icon, traj_color, traj_weight = TRAJ_DISPLAY.get(traj, ('➡', '#888', '600'))

    flags_raw = row.get('flags', '[]')
    try:
        flag_list = json.loads(flags_raw) if isinstance(flags_raw, str) else (flags_raw if isinstance(flags_raw, list) else [])
    except (json.JSONDecodeError, TypeError):
        flag_list = []
    flag_icons = ''.join(
        f'<span title="{FLAG_CONFIG[f]["label"]}">{FLAG_CONFIG[f]["icon"]}</span>'
        for f in flag_list if f in FLAG_CONFIG
    )

    is_on_roster = pid in roster_ids
    is_freshman = row.get('is_freshman', False) or (isinstance(pid, str) and str(pid).startswith('FR2026'))
    roster_mark = '<span class="gm-roster-mark">✓</span>' if is_on_roster else ''
    freshman_badge = '<span style="background:#E8390E;color:#fff;font-size:8px;font-weight:700;padding:1px 4px;border-radius:3px;margin-left:4px;">FR</span>' if is_freshman else ''

    # Build stat cells
    stat_html = ''
    if stat_cols:
        for label, key, tbl, fmt in stat_cols:
            val = _get_stat_val(pid, key, tbl, stat_data)
            stat_html += f'<span class="gm-cell" style="width:58px;text-align:center;font-family:DM Mono,monospace;font-size:11px;">{_fmt_stat(val, fmt)}</span>'

    return (
        f'<div class="gm-row">'
        f'<span class="gm-cell" style="width:28px;color:#999;font-size:11px;">{rank}</span>'
        f'<span class="gm-cell" style="width:150px;font-weight:600;font-size:12px;">{roster_mark}{name}{freshman_badge}</span>'
        f'<span class="gm-cell" style="width:100px;font-size:10px;color:#6B7280;text-transform:uppercase;">{school}</span>'
        f'<span class="gm-cell" style="width:38px;font-size:11px;">{pos}</span>'
        f'<span class="gm-cell" style="width:30px;color:{tier_color};font-weight:700;font-size:11px;">{tier}</span>'
        f'<span class="gm-cell mono" style="width:48px;text-align:center;color:{gc};font-weight:800;font-size:12px;">{cg:.1f}</span>'
        f'<span class="gm-cell mono" style="width:48px;text-align:center;color:{oc};font-weight:800;font-size:12px;">{out:.1f}</span>'
        f'<span class="gm-cell" style="width:32px;text-align:center;color:{traj_color};font-weight:{traj_weight};">{traj_icon}</span>'
        f'<span class="gm-cell mono" style="width:62px;text-align:right;font-size:12px;">{fmt_money(av)}</span>'
        f'<span class="gm-cell mono" style="width:62px;text-align:right;font-size:12px;">{fmt_money(mv) if pd.notna(mv) else "--"}</span>'
        f'<span class="gm-cell mono" style="width:68px;text-align:right;">{alpha_html}</span>'
        f'<span class="gm-cell" style="width:50px;text-align:center;font-size:14px;">{flag_icons}</span>'
        f'{stat_html}'
        f'</div>'
    )


def _get_table_key_version(key_prefix):
    """
    Return a version counter for the dataframe key.  Incremented whenever
    filters change so the widget is recreated and selections are cleared.
    """
    ver_key = f"_gm_tbl_ver_{key_prefix}"
    if ver_key not in st.session_state:
        st.session_state[ver_key] = 0
    return st.session_state[ver_key]


def _check_filters_changed(key_prefix):
    """
    Compare current filter values to the last-seen values stored in
    session_state.  If any changed, bump the table key version so the
    dataframe widget is recreated (clearing row selections).
    """
    current_filters = {
        'pos': st.session_state.get('gm_pos', 'All'),
        'tier': st.session_state.get('gm_tier', 'All'),
        'conf': st.session_state.get('gm_conf', 'All'),
        'school': st.session_state.get('gm_school', 'All'),
        'search': st.session_state.get('gm_search', ''),
        'season': st.session_state.get('gm_season', 2025),
        'freshmen': st.session_state.get('gm_freshmen', False),
        'roster_pos': st.session_state.get('roster_pos_filter', 'All'),
        'sort': st.session_state.get('gm_sort', 'Output (High → Low)'),
        'rows': st.session_state.get('gm_rows_per_page', 50),
        'affordable': st.session_state.get('gm_affordable', False),
        'portal': st.session_state.get('gm_portal', False),
        'flag': st.session_state.get('gm_active_flag_filter', None),
    }
    prev_key = f"_gm_prev_filters_{key_prefix}"
    prev_filters = st.session_state.get(prev_key, None)
    if prev_filters is not None and prev_filters != current_filters:
        ver_key = f"_gm_tbl_ver_{key_prefix}"
        st.session_state[ver_key] = st.session_state.get(ver_key, 0) + 1
        st.session_state['gm_market_page'] = 0  # Reset to page 1 on any filter/sort change
    st.session_state[prev_key] = current_filters


def _render_gm_table(table_df, roster_ids, key_prefix, stat_cols=None, stat_data=None, show_add=True):
    """
    Render a GM-mode table using st.dataframe with row selection for add/remove.
    Select rows then click the action button below to add or remove.
    """
    if table_df.empty:
        st.markdown(
            '<div style="text-align:center;padding:32px 16px;color:#6b7280;font-size:13px;">'
            '🔍 No players match your current filters.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Bug 2 fix: detect filter changes and bump key version ──
    _check_filters_changed(key_prefix)
    table_version = _get_table_key_version(key_prefix)

    # Build display DataFrame
    display_rows = []
    pid_list = []
    for _, row in table_df.iterrows():
        pid = row.get('player_id', 0)
        pid_list.append(pid)
        is_on_roster = pid in roster_ids

        cg = float(row['core_grade']) if pd.notna(row.get('core_grade')) else 0
        out = float(row['output_score']) if pd.notna(row.get('output_score')) else 0
        av = float(row.get('adjusted_value', 0) or 0)
        mv = float(row.get('market_value', 0) or 0)

        alpha_val = int(float(row.get('opportunity_score', 0))) if pd.notna(row.get('opportunity_score')) else 0
        if alpha_val > 0:
            alpha_str = f"+{fmt_money(abs(alpha_val))}"
        elif alpha_val < 0:
            alpha_str = f"-{fmt_money(abs(alpha_val))}"
        else:
            alpha_str = "$0"

        traj = row.get('trajectory_flag', 'STABLE') or 'STABLE'
        traj_map = {'BREAKOUT': '▲▲', 'UP': '▲', 'STABLE': '–', 'DOWN': '▼'}
        traj_icon = traj_map.get(traj, '➡')

        flags_raw = row.get('flags', '[]')
        try:
            flag_list = json.loads(flags_raw) if isinstance(flags_raw, str) else (flags_raw if isinstance(flags_raw, list) else [])
        except (json.JSONDecodeError, TypeError):
            flag_list = []
        flag_icons = ''.join(FLAG_CONFIG[f]['icon'] for f in flag_list if f in FLAG_CONFIG)

        status = '✅' if is_on_roster else ''
        is_limited = bool(row.get('limited_sample', False))
        player_name = row.get('name', '?')
        if is_limited:
            player_name = f"⚠️ {player_name}"

        tier_val = row.get('tier', 'T4')

        # Bug 1 fix: add numeric sort columns alongside formatted display columns
        d = {
            'Status': status,
            'Player': player_name,
            'School': row.get('school', '--'),
            'Pos': row.get('position', '--'),
            'Tier': tier_val,
            'Grade': round(cg, 1),
            'Output': f"{out:.1f}" if not is_limited else '--',
            'Trend': traj_icon if not is_limited else '--',
            'Value': fmt_money(av),
            '_val_num': float(av) if av else 0.0,
            'Mkt': fmt_money(mv) if pd.notna(row.get('market_value')) else '--',
            '_mkt_num': float(mv) if mv else 0.0,
            'Alpha': alpha_str if not is_limited else '--',
            '_alpha_num': float(alpha_val) if not is_limited else 0.0,
            'Flags': flag_icons if not is_limited else '⚠️',
        }

        # Add position-specific stat columns
        if stat_cols:
            for label, key, tbl, fmt in stat_cols:
                val = _get_stat_val(pid, key, tbl, stat_data)
                d[label] = _fmt_stat(val, fmt)

        display_rows.append(d)

    display_df = pd.DataFrame(display_rows)

    col_config = {
        'Status': st.column_config.TextColumn('', width=30),
        'Player': st.column_config.TextColumn('Player', width=130),
        'School': st.column_config.TextColumn('School', width=85),
        'Pos': st.column_config.TextColumn('Pos', width=40),
        'Tier': st.column_config.TextColumn('Tier', width=32),
        'Grade': st.column_config.NumberColumn('Grade', width=50, format="%.1f"),
        'Output': st.column_config.TextColumn('Output', width=50),
        'Trend': st.column_config.TextColumn('Trend', width=32),
        'Value': st.column_config.NumberColumn('Value', width=72, format="$%,d"),
        'Mkt': st.column_config.NumberColumn('Mkt', width=72, format="$%,d"),
        'Alpha': st.column_config.TextColumn('Alpha', width=72),
        'Flags': st.column_config.TextColumn('Flags', width=44),
    }

    # Replace formatted string columns with numeric values for sorting
    if not display_df.empty:
        display_df['Value'] = display_df['_val_num']
        display_df['Mkt'] = display_df['_mkt_num']
        # Keep Alpha as formatted text string (not numeric) to preserve -$110K convention

    # Drop hidden numeric columns
    hidden_cols = ['_val_num', '_mkt_num', '_alpha_num']
    display_df = display_df.drop(columns=[c for c in hidden_cols if c in display_df.columns])

    base_cols = ['Status', 'Player', 'School', 'Pos', 'Tier', 'Grade', 'Output',
                 'Trend', 'Value', 'Mkt', 'Alpha', 'Flags']
    extra_cols = [c for c in display_df.columns if c not in base_cols]
    display_df = display_df[base_cols + extra_cols]

    # Action bar placeholder (above table, filled after we get the selection)
    action_placeholder = st.empty()

    # Render interactive dataframe with row selection
    # Bug 2 fix: key includes version so widget resets when filters change
    event = st.dataframe(
        display_df,
        column_config=col_config,
        column_order=base_cols + extra_cols,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key=f"{key_prefix}_table_v{table_version}",
        height=min(len(display_df) * 32 + 36, 500),
    )

    # Get CURRENT selection (no lag) — filter out None values
    selected_rows = event.selection.rows if event and hasattr(event, 'selection') else []
    selected_rows = [i for i in selected_rows if i is not None]

    if selected_rows:
        sel_pids = [pid_list[i] for i in selected_rows if i < len(pid_list)]
        sel_names = [display_rows[i]['Player'] for i in selected_rows if i < len(display_rows)]
        on_roster = [p for p in sel_pids if p in roster_ids]
        not_on_roster = [p for p in sel_pids if p not in roster_ids]

        with action_placeholder.container():
            ac1, ac2, ac3 = st.columns([5, 2, 2])
            with ac1:
                st.markdown(
                    f'<p style="font-size:12px;color:#6b7280;padding-top:8px;">'
                    f'Selected: <b style="color:#1f2937;">{", ".join(sel_names[:4])}'
                    f'{"..." if len(sel_names) > 4 else ""}</b></p>',
                    unsafe_allow_html=True,
                )
            with ac2:
                if not_on_roster and show_add:
                    if st.button(f"➕ Add {len(not_on_roster)} to Roster", key=f"{key_prefix}_add_sel", type="primary"):
                        for pid in not_on_roster:
                            row_idx = pid_list.index(pid)
                            row_data = table_df.iloc[row_idx].to_dict()
                            _add_to_roster(pid, row_data)
                        st.rerun()
            with ac3:
                if on_roster:
                    if st.button(f"➖ Remove {len(on_roster)} from Roster", key=f"{key_prefix}_rm_sel", type="secondary"):
                        for pid in on_roster:
                            _remove_from_roster(pid)
                        st.rerun()


# ── Roster Summary (Top of Page) ──
roster = st.session_state['gm_roster']
roster_ids = set(roster.keys())

# Calculate roster stats
if roster:
    roster_df = pd.DataFrame(list(roster.values()))
    total_value = roster_df['adjusted_value'].sum()
    total_market = roster_df['market_value'].sum() if 'market_value' in roster_df.columns else 0
    total_alpha = total_value - total_market
    roster_count = len(roster_df)
else:
    total_value = 0
    total_market = 0
    total_alpha = 0
    roster_count = 0

# Budget gauge
budget_remaining = budget - total_market


# ── KPI Cards ──
def _kpi_card(label, value, accent=None):
    border = f"border-left: 4px solid {accent};" if accent else ""
    return f'''<div style="background:#f3f4f6; border:1px solid #e5e7eb; border-radius:10px; padding:16px 20px; {border}">
        <div style="font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#6b7280; margin-bottom:4px;">{label}</div>
        <div style="font-size:24px; font-weight:800; font-family:'DM Mono',monospace; color:#1f2937;">{value}</div>
    </div>'''


# Determine accents
alpha_accent = '#16A34A' if total_alpha > 0 else '#DC2626' if total_alpha < 0 else '#6B7280'
alpha_prefix = '+' if total_alpha > 0 else '-' if total_alpha < 0 else ''
alpha_display = f"{alpha_prefix}{fmt_money(abs(total_alpha))}"

budget_pct_remaining = ((budget_remaining / budget) * 100) if budget > 0 else 0
if budget_remaining < 0:
    budget_accent = '#DC2626'
    budget_label = 'Over Budget'
    budget_display = fmt_money(abs(budget_remaining))
elif budget_pct_remaining > 50:
    budget_accent = '#16A34A'
    budget_label = 'Budget Left'
    budget_display = fmt_money(budget_remaining)
elif budget_pct_remaining > 25:
    budget_accent = '#F97316'
    budget_label = 'Budget Left'
    budget_display = fmt_money(budget_remaining)
else:
    budget_accent = '#DC2626'
    budget_label = 'Budget Left'
    budget_display = fmt_money(budget_remaining)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(_kpi_card("Roster Size", str(roster_count)), unsafe_allow_html=True)
with k2:
    st.markdown(_kpi_card("Team Value", fmt_money(total_value), accent='#16A34A'), unsafe_allow_html=True)
with k3:
    st.markdown(_kpi_card("Market Cost", fmt_money(total_market), accent='#DC2626'), unsafe_allow_html=True)
with k4:
    st.markdown(_kpi_card("Total Alpha", alpha_display, accent=alpha_accent), unsafe_allow_html=True)
with k5:
    st.markdown(_kpi_card(budget_label, budget_display, accent=budget_accent), unsafe_allow_html=True)

# ── Budget Progress Bar ──
if budget > 0:
    pct_used = (total_market / budget * 100) if budget > 0 else 0
    bar_color = '#16A34A' if pct_used < 50 else '#F97316' if pct_used < 75 else '#DC2626'
    st.markdown(f'''
    <div style="background:#e5e7eb; border-radius:6px; height:12px; overflow:hidden; margin:8px 0 4px 0;">
        <div style="background:{bar_color}; height:100%; width:{min(pct_used,100):.1f}%; border-radius:6px; transition:width 0.3s;"></div>
    </div>
    <p style="font-size:12px; color:#6b7280; margin:0 0 20px 0;">{pct_used:.0f}% of {fmt_money(budget)} used</p>
    ''', unsafe_allow_html=True)

st.markdown("<hr style='margin:16px 0 24px 0; border:none; border-top:1px solid #e5e7eb;'>", unsafe_allow_html=True)

# ── Roster View Toggle (with visual grouping labels) ──
st.markdown(
    '<div style="display:flex;gap:24px;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:4px;">'
    '<span style="flex:1;">VIEW</span>'
    '<span style="flex:1.5;">ANALYZE</span>'
    '</div>',
    unsafe_allow_html=True,
)
roster_view = st.radio("Roster View", ["List View", "Depth Chart", "Roster Analysis", "What-If", "Optimizer"], horizontal=True,
                       label_visibility="collapsed", key="gm_view")

if roster_view == "Roster Analysis":
    # ── ROSTER GAP ANALYSIS + SPENDING DASHBOARD ──
    st.markdown("### Roster Analysis")

    # 85-man template: ideal roster composition
    ROSTER_TEMPLATE = {
        'QB': {'target': 3, 'label': 'Quarterbacks'},
        'RB': {'target': 4, 'label': 'Running Backs'},
        'WR': {'target': 8, 'label': 'Wide Receivers'},
        'TE': {'target': 4, 'label': 'Tight Ends'},
        'OT': {'target': 6, 'label': 'Offensive Tackles'},
        'IOL': {'target': 6, 'label': 'Interior O-Line'},
        'EDGE': {'target': 6, 'label': 'Edge Rushers'},
        'IDL': {'target': 6, 'label': 'Interior D-Line'},
        'LB': {'target': 6, 'label': 'Linebackers'},
        'CB': {'target': 8, 'label': 'Cornerbacks'},
        'S': {'target': 5, 'label': 'Safeties'},
    }

    if not roster:
        st.info("Add players to your roster to see gap analysis and spending breakdown.")
    else:
        roster_df_gap = pd.DataFrame(list(roster.values()))
        pos_counts_gap = roster_df_gap['position'].value_counts().to_dict()

        # ── Gap Analysis ──
        st.markdown('<p class="section-header" style="font-size:12px;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.08em;border-bottom:2px solid #E8390E;padding-bottom:6px;margin-bottom:12px;'
                    'color:#6b7280;">Position Gap Analysis</p>', unsafe_allow_html=True)

        gap_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">'
        critical_needs = []
        for pos, cfg in ROSTER_TEMPLATE.items():
            have = pos_counts_gap.get(pos, 0)
            target = cfg['target']
            diff = have - target
            pct = min(have / target * 100, 100) if target > 0 else 100

            if diff >= 0:
                bar_color = '#16A34A'
                status = f'<span style="color:#16A34A;font-weight:700;">✓ Full</span>'
            elif diff >= -1:
                bar_color = '#F97316'
                status = f'<span style="color:#F97316;font-weight:700;">Need {abs(diff)}</span>'
            else:
                bar_color = '#DC2626'
                status = f'<span style="color:#DC2626;font-weight:700;">Need {abs(diff)}</span>'
                critical_needs.append(f"{pos} ({abs(diff)})")

            gap_html += (
                f'<div style="background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                f'<span style="font-size:12px;font-weight:700;color:#1f2937;">{pos}</span>'
                f'<span style="font-size:11px;">{status}</span>'
                f'</div>'
                f'<div style="font-size:11px;color:#6b7280;margin-bottom:4px;">{have}/{target} {cfg["label"]}</div>'
                f'<div style="background:#e5e7eb;border-radius:3px;height:6px;overflow:hidden;">'
                f'<div style="background:{bar_color};height:100%;width:{pct:.0f}%;border-radius:3px;"></div>'
                f'</div></div>'
            )
        gap_html += '</div>'
        st.markdown(gap_html, unsafe_allow_html=True)

        if critical_needs:
            st.warning(f"**Critical needs:** {', '.join(critical_needs)}")

        total_on_roster = len(roster_df_gap)
        st.caption(f"Roster: {total_on_roster}/85 · "
                   f"{'Over' if total_on_roster > 85 else str(85 - total_on_roster) + ' spots remaining'}")

        st.markdown("---")

        # ── C3: Position Group Spending Dashboard ──
        st.markdown('<p class="section-header" style="font-size:12px;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.08em;border-bottom:2px solid #E8390E;padding-bottom:6px;margin-bottom:12px;'
                    'color:#6b7280;">Spending by Position Group</p>', unsafe_allow_html=True)

        # Aggregate spending per position
        spend_data = []
        for pos in ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']:
            pos_players = roster_df_gap[roster_df_gap['position'] == pos]
            if pos_players.empty:
                continue
            pos_mkt = pos_players['market_value'].fillna(0).sum()
            pos_val = pos_players['adjusted_value'].fillna(0).sum()
            pos_alpha = pos_val - pos_mkt
            pos_count = len(pos_players)
            avg_grade = pos_players['core_grade'].mean() if 'core_grade' in pos_players.columns else 0
            spend_data.append({
                'Position': pos,
                'Players': pos_count,
                'Avg Grade': round(float(avg_grade), 1) if pd.notna(avg_grade) else 0,
                'Total Value': int(pos_val),
                'Total Mkt': int(pos_mkt),
                'Alpha': int(pos_alpha),
                '% of Budget': round(pos_mkt / budget * 100, 1) if budget > 0 else 0,
            })

        if spend_data:
            spend_df = pd.DataFrame(spend_data)

            # Visual bar chart of spending
            chart_df = spend_df.set_index('Position')[['Total Mkt', 'Total Value']].rename(
                columns={'Total Mkt': 'Market Cost', 'Total Value': 'Production Value'}
            ) / 1000
            st.bar_chart(chart_df, use_container_width=True)
            st.caption("Values in $K")

            # Table
            display_spend = spend_df.copy()
            display_spend['Total Value'] = display_spend['Total Value'].apply(lambda x: fmt_money(x))
            display_spend['Total Mkt'] = display_spend['Total Mkt'].apply(lambda x: fmt_money(x))
            display_spend['Alpha'] = display_spend['Alpha'].apply(lambda x: f"+{fmt_money(abs(x))}" if x > 0 else f"-{fmt_money(abs(x))}" if x < 0 else "$0")
            display_spend['% of Budget'] = display_spend['% of Budget'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display_spend, use_container_width=True, hide_index=True)

            # Highlight biggest spend and best value
            spend_df_sorted = pd.DataFrame(spend_data).sort_values('Total Mkt', ascending=False)
            top_spend = spend_df_sorted.iloc[0]
            best_alpha = pd.DataFrame(spend_data).sort_values('Alpha', ascending=False).iloc[0]

            _insight_cols = st.columns(2)
            with _insight_cols[0]:
                st.markdown(
                    f'<div style="background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:12px;">'
                    f'<span style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Biggest Spend</span><br>'
                    f'<span style="font-size:16px;font-weight:700;color:#1f2937;">{top_spend["Position"]}</span> — '
                    f'<span style="font-family:DM Mono,monospace;color:#F97316;">{fmt_money(top_spend["Total Mkt"])}</span>'
                    f' ({top_spend["Players"]} players)</div>',
                    unsafe_allow_html=True,
                )
            with _insight_cols[1]:
                _alpha_color = '#16A34A' if best_alpha['Alpha'] > 0 else '#DC2626'
                st.markdown(
                    f'<div style="background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:12px;">'
                    f'<span style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Best Value Unit</span><br>'
                    f'<span style="font-size:16px;font-weight:700;color:#1f2937;">{best_alpha["Position"]}</span> — '
                    f'<span style="font-family:DM Mono,monospace;color:{_alpha_color};">{"+" if best_alpha["Alpha"] > 0 else "-" if best_alpha["Alpha"] < 0 else ""}{fmt_money(abs(best_alpha["Alpha"]))} alpha</span>'
                    f' (avg {best_alpha["Avg Grade"]:.1f} grade)</div>',
                    unsafe_allow_html=True,
                )

elif roster_view == "Depth Chart":
    # ── DEPTH CHART VIEW ──
    st.markdown("### Depth Chart")

    DEFENSE_FORMATIONS = {
        "4-3": {
            "rows": [
                {"label": "Secondary", "slots": [("CB", "CB1"), ("S", "FS"), ("S", "SS"), ("CB", "CB2")]},
                {"label": "Linebackers", "slots": [("LB", "WLB"), ("LB", "MLB"), ("LB", "SLB")]},
                {"label": "D-Line", "slots": [("EDGE", "DE"), ("IDL", "DT"), ("IDL", "DT"), ("EDGE", "DE")]},
            ]
        },
        "3-4": {
            "rows": [
                {"label": "Secondary", "slots": [("CB", "CB1"), ("S", "FS"), ("S", "SS"), ("CB", "CB2")]},
                {"label": "Linebackers", "slots": [("EDGE", "OLB"), ("LB", "ILB"), ("LB", "ILB"), ("EDGE", "OLB")]},
                {"label": "D-Line", "slots": [("IDL", "DE"), ("IDL", "NT"), ("IDL", "DE")]},
            ]
        },
        "4-2": {
            "rows": [
                {"label": "Secondary", "slots": [("CB", "CB1"), ("S", "FS"), ("S", "SS"), ("CB", "CB2")]},
                {"label": "Linebackers", "slots": [("LB", "LB"), ("LB", "LB")]},
                {"label": "D-Line", "slots": [("EDGE", "DE"), ("IDL", "DT"), ("IDL", "DT"), ("EDGE", "DE")]},
            ]
        },
        "3-3 Stack": {
            "rows": [
                {"label": "Secondary", "slots": [("CB", "CB1"), ("S", "FS"), ("S", "SS"), ("CB", "CB2")]},
                {"label": "Linebackers", "slots": [("LB", "LB"), ("LB", "LB"), ("LB", "LB")]},
                {"label": "D-Line", "slots": [("EDGE", "DE"), ("IDL", "NT"), ("EDGE", "DE")]},
            ]
        },
    }

    OFFENSE_FORMATIONS = {
        "Pro": {
            "rows": [
                {"label": "Receivers", "slots": [("WR", "WR"), ("TE", "TE")]},
                {"label": "O-Line", "slots": [("OT", "LT"), ("IOL", "LG"), ("IOL", "C"), ("IOL", "RG"), ("OT", "RT")]},
                {"label": "QB", "slots": [("QB", "QB")]},
                {"label": "Backfield", "slots": [("RB", "HB"), ("TE", "FB")]},
            ]
        },
        "Spread": {
            "rows": [
                {"label": "Receivers", "slots": [("WR", "WR"), ("WR", "WR"), ("WR", "WR"), ("WR", "WR")]},
                {"label": "O-Line", "slots": [("OT", "LT"), ("IOL", "LG"), ("IOL", "C"), ("IOL", "RG"), ("OT", "RT")]},
                {"label": "QB", "slots": [("QB", "QB")]},
                {"label": "Backfield", "slots": [("RB", "RB")]},
            ]
        },
        "Singleback": {
            "rows": [
                {"label": "Receivers", "slots": [("WR", "WR"), ("WR", "WR"), ("TE", "TE")]},
                {"label": "O-Line", "slots": [("OT", "LT"), ("IOL", "LG"), ("IOL", "C"), ("IOL", "RG"), ("OT", "RT")]},
                {"label": "QB", "slots": [("QB", "QB")]},
                {"label": "Backfield", "slots": [("RB", "RB")]},
            ]
        },
        "Empty": {
            "rows": [
                {"label": "Receivers", "slots": [("WR", "WR"), ("WR", "WR"), ("WR", "WR"), ("WR", "WR"), ("TE", "TE")]},
                {"label": "O-Line", "slots": [("OT", "LT"), ("IOL", "LG"), ("IOL", "C"), ("IOL", "RG"), ("OT", "RT")]},
                {"label": "QB", "slots": [("QB", "QB")]},
            ]
        },
    }

    fc1, fc2 = st.columns(2)
    with fc1:
        def_formation = st.selectbox("Defense Formation", list(DEFENSE_FORMATIONS.keys()), key="def_formation")
    with fc2:
        off_formation = st.selectbox("Offense Formation", list(OFFENSE_FORMATIONS.keys()), key="off_formation")

    if not roster:
        st.markdown(
            '<div style="text-align:center;padding:48px 24px;background:#f6f8fa;border:1px dashed #e5e7eb;border-radius:12px;margin:16px 0;">'
            '<div style="font-size:48px;margin-bottom:12px;">🏟️</div>'
            '<div style="font-size:18px;font-weight:700;color:#1f2937;margin-bottom:8px;">Your depth chart is empty</div>'
            '<div style="font-size:13px;color:#6b7280;max-width:400px;margin:0 auto;">'
            'Add players from the <strong style="color:#E8390E;">Player Market</strong> below to start building your depth chart.'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        roster_df = pd.DataFrame(list(roster.values()))

        # ── Position count summary strip ──
        pos_counts = roster_df['position'].value_counts().to_dict()
        pos_order = ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']
        count_chips = []
        for p in pos_order:
            cnt = pos_counts.get(p, 0)
            if cnt > 0:
                count_chips.append(
                    f'<span style="display:inline-block;background:#f6f8fa;border:1px solid #e5e7eb;'
                    f'border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;margin:2px 3px;'
                    f'color:#1f2937;">{p} <span style="color:#6b7280;">{cnt}</span></span>'
                )
        # Add total chip at the end
        count_chips.append(
            f'<span style="display:inline-block;padding:2px 10px;margin:2px;border-radius:12px;'
            f'font-size:11px;font-weight:700;background:#E8390E;color:#fff;">TOTAL {len(roster_df)}</span>'
        )
        st.markdown(
            f'<div style="padding:6px 0 10px 0;display:flex;flex-wrap:wrap;align-items:center;gap:2px;">'
            f'<span style="font-size:11px;color:#6b7280;font-weight:600;margin-right:8px;">'
            f'ROSTER ({len(roster_df)}/85)</span>'
            f'{"".join(count_chips)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        def _depth_card_html(p, is_starter=True):
            """Render a compact dark-mode depth chart player card as HTML."""
            name = p.get('name', '?')
            parts = name.split()
            short = f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else name
            cg = float(p.get('core_grade', 0)) if pd.notna(p.get('core_grade')) else 0
            av = p.get('adjusted_value', 0) or 0
            tier = p.get('tier', 'T4')
            gc = _grade_color(cg)
            tc = {'T1': '#E8390E', 'T2': '#F97316', 'T3': '#3B82F6', 'T4': '#6B7280', 'UR': '#9ca3af'}.get(tier, '#6B7280')

            if not is_starter:
                return (
                    f'<div style="padding:4px 8px 4px 14px;font-size:11px;color:#6b7280;'
                    f'border-left:2px solid #e5e7eb;margin:1px 0;display:flex;align-items:center;gap:6px;">'
                    f'<span style="color:#9ca3af;font-size:9px;">└</span>'
                    f'<span style="font-weight:600;color:#6b7280;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{short}</span>'
                    f'<span style="font-family:DM Mono,monospace;color:{gc};font-size:10px;">{cg:.1f}</span>'
                    f'<span style="font-family:DM Mono,monospace;color:#9ca3af;font-size:10px;">{fmt_money(av)}</span>'
                    f'</div>'
                )

            return (
                f'<div style="background:#f9fafb;border:1px solid #d1d5db;border-left:4px solid {tc};'
                f'border-radius:6px;padding:8px 10px;margin-bottom:2px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">'
                f'<span style="font-weight:700;color:#1f2937;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:70%;">{short}</span>'
                f'<span style="font-weight:700;color:{tc};font-size:9px;letter-spacing:0.03em;">{tier}</span>'
                f'</div>'
                f'<div style="display:flex;gap:10px;font-family:DM Mono,monospace;font-size:10px;color:#6b7280;">'
                f'<span><b style="color:{gc};">{cg:.1f}</b></span>'
                f'<span style="color:#1f2937;font-weight:600;">{fmt_money(av)}</span>'
                f'</div>'
                f'</div>'
            )

        def _empty_slot_html():
            return (
                '<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:6px;'
                'padding:14px 8px;text-align:center;color:#9ca3af;">'
                '<div style="font-size:18px;margin-bottom:2px;">+</div>'
                '<div style="font-size:10px;font-style:italic;">Empty</div>'
                '</div>'
            )

        def _unit_grade_badge(grade):
            """Return an HTML badge for a unit average grade."""
            if grade is None:
                return ''
            gc = _grade_color(grade)
            return (f'<span style="font-family:DM Mono,monospace;font-size:12px;font-weight:700;'
                    f'color:{gc};background:rgba(255,255,255,0.04);border:1px solid {gc}33;'
                    f'border-radius:4px;padding:2px 8px;margin-left:8px;">{grade:.1f}</span>')

        def _render_depth_unit(formation_config, roster_df, unit_label, prefix):
            """Render a depth chart unit with auto-assignment and backup stacking."""
            st.markdown(
                f'<div style="text-align:center;font-size:13px;font-weight:800;text-transform:uppercase;'
                f'letter-spacing:0.1em;color:#6b7280;padding:10px 0 6px 0;">{unit_label}</div>',
                unsafe_allow_html=True
            )

            # Group roster by position, sorted by output_score descending
            roster_by_pos = {}
            for _, p in roster_df.iterrows():
                pos = p.get('position', '--')
                roster_by_pos.setdefault(pos, []).append(p)
            for pos_key in roster_by_pos:
                roster_by_pos[pos_key].sort(
                    key=lambda p: float(p.get('output_score', 0)) if pd.notna(p.get('output_score')) else 0,
                    reverse=True
                )

            # Pre-compute: for each position, how many starter slots exist and
            # which slot index (0-based) each column represents
            pos_slot_indices = {}  # {pos_key: [(row_idx, col_idx), ...]}
            for ri, row_cfg in enumerate(formation_config["rows"]):
                for ci, (pos_key, slot_label) in enumerate(row_cfg["slots"]):
                    pos_slot_indices.setdefault(pos_key, []).append((ri, ci))

            # Pre-assign: distribute players across slots for each position
            # Starters fill slots in order, backups are distributed round-robin
            pos_slot_players = {}  # {pos_key: {slot_num: {'starter': player, 'backups': [players]}}}
            for pos_key, slots in pos_slot_indices.items():
                eligible = roster_by_pos.get(pos_key, [])
                n_slots = len(slots)
                assignment = {i: {'starter': None, 'backups': []} for i in range(n_slots)}

                # Check for manual starter overrides
                for si in range(n_slots):
                    override_key = f"{prefix}_{pos_key}_{si}_starter"
                    override_pid = st.session_state.get(override_key)
                    if override_pid:
                        # Find this player in eligible list
                        for p in eligible:
                            pid = p.get('player_id', 0)
                            if isinstance(pid, (int, float)) and int(pid) == int(override_pid):
                                assignment[si]['starter'] = p
                                break

                # Fill remaining starter slots with best available (not already assigned)
                assigned_pids = {int(a['starter'].get('player_id', 0)) for a in assignment.values() if a['starter'] is not None}
                remaining = [p for p in eligible if int(p.get('player_id', 0)) not in assigned_pids]

                for si in range(n_slots):
                    if assignment[si]['starter'] is None and remaining:
                        assignment[si]['starter'] = remaining.pop(0)

                # Distribute backups round-robin across slots
                slot_idx = 0
                for bp in remaining:
                    assignment[slot_idx % n_slots]['backups'].append(bp)
                    slot_idx += 1

                pos_slot_players[pos_key] = assignment

            # Track which slot number we're on for each position
            pos_slot_counter = {}

            for row_cfg in formation_config["rows"]:
                row_label = row_cfg["label"]
                row_slots = row_cfg["slots"]

                # Compute row unit grade from starters in this row
                _row_grades = []
                _temp_counter = dict(pos_slot_counter)  # peek ahead
                for _pos_key, _slot_label in row_slots:
                    _sn = _temp_counter.get(_pos_key, 0)
                    _temp_counter[_pos_key] = _sn + 1
                    _a = pos_slot_players.get(_pos_key, {}).get(_sn, {})
                    _s = _a.get('starter') if isinstance(_a, dict) else None
                    if _s is not None:
                        _cg = float(_s.get('core_grade', 0)) if pd.notna(_s.get('core_grade')) else 0
                        if _cg > 0:
                            _row_grades.append(_cg)
                _row_avg = sum(_row_grades) / len(_row_grades) if _row_grades else None
                _badge = _unit_grade_badge(_row_avg)

                st.markdown(
                    f'<div style="display:flex;align-items:center;justify-content:center;gap:6px;'
                    f'font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;'
                    f'letter-spacing:0.06em;padding:4px 0 2px 0;">'
                    f'{row_label}{_badge}</div>',
                    unsafe_allow_html=True,
                )

                # Constrain single-slot rows (QB, RB) to avoid full-width stretch
                n_slots = len(row_slots)
                if n_slots <= 2:
                    _pad_l, _content, _pad_r = st.columns([1, 2, 1]) if n_slots == 1 else (None, None, None)
                    if n_slots == 1:
                        with _content:
                            cols = [_content]
                    else:
                        _pad_l2, _c1, _c2, _pad_r2 = st.columns([1, 1.5, 1.5, 1])
                        cols = [_c1, _c2]
                else:
                    cols = st.columns(n_slots)

                for ci, (pos_key, slot_label) in enumerate(row_slots):
                    with cols[ci]:
                        # Slot header label
                        st.markdown(
                            f'<div style="text-align:center;font-size:9px;font-weight:800;'
                            f'text-transform:uppercase;color:#6b7280;background:#f6f8fa;padding:2px 6px;'
                            f'border-radius:3px;margin-bottom:3px;letter-spacing:0.05em;">{slot_label}</div>',
                            unsafe_allow_html=True
                        )

                        slot_num = pos_slot_counter.get(pos_key, 0)
                        pos_slot_counter[pos_key] = slot_num + 1

                        assignment = pos_slot_players.get(pos_key, {}).get(slot_num, {'starter': None, 'backups': []})
                        starter = assignment['starter']
                        backups = assignment['backups']

                        if starter is not None:
                            html = _depth_card_html(starter, is_starter=True)

                            # Backup cards
                            for bi, bp in enumerate(backups):
                                html += _depth_card_html(bp, is_starter=False)

                            st.markdown(html, unsafe_allow_html=True)

                            # Action row: swap starter + remove buttons
                            all_slot_players = [starter] + backups
                            if backups:
                                bp_names = {int(b.get('player_id', 0)): b.get('name', '?') for b in backups}
                                _act_cols = st.columns([3, 1, 1])
                                with _act_cols[0]:
                                    promote_key = f"{prefix}_{pos_key}_{slot_num}_promote"
                                    selected = st.selectbox(
                                        "Promote",
                                        options=[None] + list(bp_names.keys()),
                                        format_func=lambda x: "↕ Swap starter" if x is None else f"↑ {bp_names.get(x, '?')}",
                                        key=promote_key,
                                        label_visibility="collapsed",
                                    )
                                    if selected is not None:
                                        override_key = f"{prefix}_{pos_key}_{slot_num}_starter"
                                        st.session_state[override_key] = int(selected)
                                        st.rerun()
                                with _act_cols[1]:
                                    _rm_pid = st.selectbox(
                                        "Remove",
                                        options=[None] + [int(p.get('player_id', 0)) for p in all_slot_players],
                                        format_func=lambda x: "✕ Drop" if x is None else f"✕ {roster.get(x, {}).get('name', '?')[:12]}",
                                        key=f"{prefix}_{pos_key}_{slot_num}_remove",
                                        label_visibility="collapsed",
                                    )
                                    if _rm_pid is not None:
                                        _remove_from_roster(_rm_pid)
                                        st.rerun()
                                with _act_cols[2]:
                                    pass
                            else:
                                # Just a remove button for the starter
                                _starter_pid = int(starter.get('player_id', 0))
                                if st.button("✕ Drop", key=f"{prefix}_{pos_key}_{slot_num}_drop",
                                             help=f"Remove {starter.get('name', '?')} from roster"):
                                    _remove_from_roster(_starter_pid)
                                    st.rerun()
                        else:
                            st.markdown(_empty_slot_html(), unsafe_allow_html=True)

        # Render Defense
        _render_depth_unit(DEFENSE_FORMATIONS[def_formation], roster_df, "Defense", "DEF")

        st.markdown(
            '<div style="height:3px;background:linear-gradient(90deg, #e5e7eb, #E8390E, #e5e7eb);margin:12px 0;border-radius:2px;"></div>',
            unsafe_allow_html=True
        )

        # Render Offense
        _render_depth_unit(OFFENSE_FORMATIONS[off_formation], roster_df, "Offense", "OFF")

        # Show unassigned players (not matching any formation slot position)
        all_formation_positions = set()
        for r in DEFENSE_FORMATIONS[def_formation]["rows"]:
            for pk, _ in r["slots"]:
                all_formation_positions.add(pk)
        for r in OFFENSE_FORMATIONS[off_formation]["rows"]:
            for pk, _ in r["slots"]:
                all_formation_positions.add(pk)

        unassigned = roster_df[~roster_df['position'].isin(all_formation_positions)]
        if not unassigned.empty:
            st.markdown(
                '<div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;'
                'letter-spacing:0.08em;margin-top:12px;padding:4px 0;">Unassigned</div>',
                unsafe_allow_html=True
            )
            ua_html = ''
            for _, p in unassigned.iterrows():
                name = p.get('name', '?')
                pos = p.get('position', '--')
                cg = float(p.get('core_grade', 0)) if pd.notna(p.get('core_grade')) else 0
                gc = _grade_color(cg)
                ua_html += (
                    f'<span style="display:inline-block;background:#f3f4f6;border:1px solid #e5e7eb;'
                    f'border-radius:4px;padding:3px 8px;font-size:11px;margin:2px;">'
                    f'<b style="color:#1f2937;">{name}</b> '
                    f'<span style="color:#6b7280;">{pos}</span> '
                    f'<span style="font-family:DM Mono,monospace;color:{gc};">{cg:.1f}</span>'
                    f'</span>'
                )
            st.markdown(ua_html, unsafe_allow_html=True)

        st.markdown("---")
        _exp_col_dc, _clr_col_dc = st.columns(2)
        with _exp_col_dc:
            export_roster_csv(roster, budget)
        with _clr_col_dc:
            if st.button("⚠️ Clear Entire Roster", type="primary", key="clear_dc"):
                st.session_state['gm_roster'] = {}
                st.session_state['gm_slot_assignments'] = {}
                _autosave_roster()
                st.rerun()

elif roster_view == "Optimizer":
    # ── BUDGET ALLOCATION OPTIMIZER (D6) ──
    st.markdown("### Budget Allocation Optimizer")
    st.caption("Find the best possible roster within your budget using position needs and player rankings.")

    # Position needs configuration
    st.markdown("**Configure Position Needs**")
    _opt_cols = st.columns(6)
    _default_needs = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 1, 'OT': 2, 'IOL': 2,
                      'EDGE': 2, 'IDL': 2, 'LB': 2, 'CB': 2, 'S': 2}
    _position_list = list(_default_needs.keys())
    _needs = {}
    for i, _pos in enumerate(_position_list):
        with _opt_cols[i % 6]:
            _have = len([p for p in roster.values() if p.get('position') == _pos]) if roster else 0
            _needs[_pos] = st.number_input(
                f"{_pos} (have {_have})", min_value=0, max_value=10,
                value=max(0, _default_needs[_pos] - _have),
                key=f"opt_need_{_pos}",
            )

    _total_needed = sum(_needs.values())
    _opt_budget = budget_remaining if roster else budget

    st.markdown(f"**Slots to fill:** {_total_needed} · **Available budget:** {fmt_money(max(0, int(_opt_budget)))}")

    _opt_strategy = st.radio(
        "Optimization Strategy",
        ["Maximize Output Score", "Maximize Value (Alpha)", "Balanced (Output × Alpha)"],
        horizontal=True, key="opt_strategy",
    )

    if st.button("🔧 Run Optimizer", key="run_optimizer", type="primary"):
        if _total_needed == 0:
            st.info("All positions are filled. Adjust needs above to find additional players.")
        elif _opt_budget <= 0:
            st.error("No budget remaining. Free up cap space first.")
        else:
            with st.spinner("Finding optimal roster allocation..."):
                # Greedy optimizer: for each position, find the best players within budget
                _roster_ids_set = set(str(k) for k in roster.keys()) if roster else set()
                _remaining_budget = max(0, _opt_budget)
                _picks = []

                # Sort positions by scarcity (fewer available = pick first)
                _pos_pool_sizes = {}
                for _pos, _need in _needs.items():
                    if _need == 0:
                        continue
                    _pool = df[
                        (df['position'] == _pos) &
                        (~df['player_id'].astype(str).isin(_roster_ids_set))
                    ]
                    _pos_pool_sizes[_pos] = len(_pool)

                _sorted_positions = sorted(
                    [(p, n) for p, n in _needs.items() if n > 0],
                    key=lambda x: _pos_pool_sizes.get(x[0], 0)
                )

                # Reserve proportional budget per position based on typical market rates
                _pos_avg_costs = {}
                for _pos, _ in _sorted_positions:
                    _pool = df[(df['position'] == _pos) & (~df['player_id'].astype(str).isin(_roster_ids_set))]
                    _pos_avg_costs[_pos] = _pool['market_value'].fillna(0).median() if not _pool.empty else 0

                _total_est = sum(_pos_avg_costs.get(p, 0) * n for p, n in _sorted_positions)
                _budget_scale = _remaining_budget / _total_est if _total_est > 0 else 1

                for _pos, _need in _sorted_positions:
                    _pool = df[
                        (df['position'] == _pos) &
                        (~df['player_id'].astype(str).isin(_roster_ids_set))
                    ].copy()

                    if _pool.empty:
                        continue

                    # Budget allocation for this position
                    _pos_budget = _pos_avg_costs.get(_pos, 0) * _need * _budget_scale
                    _pos_budget = min(_pos_budget, _remaining_budget)

                    # Score players based on strategy
                    if _opt_strategy == "Maximize Output Score":
                        _pool['_opt_score'] = _pool['output_score'].fillna(0)
                    elif _opt_strategy == "Maximize Value (Alpha)":
                        _pool['_opt_score'] = _pool['opportunity_score'].fillna(0)
                    else:
                        # Balanced: normalize both and combine
                        _os_max = _pool['output_score'].max() or 1
                        _alpha_max = _pool['opportunity_score'].max() or 1
                        _pool['_opt_score'] = (
                            _pool['output_score'].fillna(0) / _os_max * 50 +
                            _pool['opportunity_score'].fillna(0) / _alpha_max * 50
                        )

                    # Filter affordable players
                    _affordable = _pool[_pool['market_value'].fillna(0) <= _remaining_budget].copy()
                    if _affordable.empty:
                        continue

                    _affordable = _affordable.sort_values('_opt_score', ascending=False)

                    _picked_for_pos = 0
                    for _, _candidate in _affordable.iterrows():
                        if _picked_for_pos >= _need:
                            break
                        _cand_mkt = float(_candidate.get('market_value', 0) or 0)
                        if _cand_mkt <= _remaining_budget:
                            _picks.append(_candidate.to_dict())
                            _remaining_budget -= _cand_mkt
                            _roster_ids_set.add(str(_candidate['player_id']))
                            _picked_for_pos += 1

                if _picks:
                    _picks_df = pd.DataFrame(_picks)
                    _total_cost = _picks_df['market_value'].fillna(0).sum()
                    _total_val = _picks_df['adjusted_value'].fillna(0).sum()

                    _opt_alpha = int(_total_val - _total_cost)
                    _opt_alpha_str = f"+{fmt_money(abs(_opt_alpha))}" if _opt_alpha >= 0 else f"-{fmt_money(abs(_opt_alpha))}"
                    st.success(f"Found **{len(_picks)} players** for {fmt_money(int(_total_cost))} "
                               f"(Value: {fmt_money(int(_total_val))}, Alpha: {_opt_alpha_str})")

                    _opt_display = _picks_df[['name', 'position', 'school', 'tier', 'core_grade',
                                               'output_score', 'adjusted_value', 'market_value']].copy()
                    _opt_display.columns = ['Name', 'Pos', 'School', 'Tier', 'Grade', 'Output', 'Value', 'Mkt']
                    _opt_display['Grade'] = _opt_display['Grade'].round(1)
                    _opt_display['Output'] = _opt_display['Output'].round(1)
                    _opt_display['Value'] = _opt_display['Value'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
                    _opt_display['Mkt'] = _opt_display['Mkt'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
                    st.dataframe(_opt_display, use_container_width=True, hide_index=True)

                    # Add all to roster button
                    if st.button("➕ Add All to Roster", key="opt_add_all", type="primary"):
                        for _, _pick in _picks_df.iterrows():
                            _pid = str(int(_pick['player_id']))
                            if _pid not in st.session_state.get('gm_roster', {}):
                                st.session_state['gm_roster'][_pid] = _pick.to_dict()
                        _autosave_roster()
                        st.rerun()
                else:
                    st.warning("Could not find players that fit within your remaining budget.")

elif roster_view == "What-If":
    # ── WHAT-IF SCENARIO BUILDER (D5) ──
    st.markdown("### What-If Scenario Builder")
    st.caption("Simulate roster changes, budget shifts, and market inflation to see how they impact your team.")

    if not roster:
        st.info("Add players to your roster first, then come back to run scenarios.")
    else:
        roster_df = pd.DataFrame(list(roster.values()))
        _current_total_val = roster_df['adjusted_value'].fillna(0).astype(float).sum()
        _current_total_mkt = roster_df['market_value'].fillna(0).astype(float).sum()
        _current_total_alpha = _current_total_val - _current_total_mkt
        _current_count = len(roster_df)

        # --- Scenario selector ---
        _scenario = st.selectbox(
            "Choose a scenario",
            ["Lose a Player", "Budget Change", "Market Inflation/Deflation", "Position Upgrade"],
            key="whatif_scenario",
        )

        if _scenario == "Lose a Player":
            st.markdown("**What happens if you lose a key player?**")
            _player_names = {str(pid): p.get('name', '?') + f" ({p.get('position', '?')})"
                            for pid, p in roster.items()}
            _selected_pid = st.selectbox("Select player to remove", list(_player_names.keys()),
                                         format_func=lambda x: _player_names[x], key="whatif_lose_player")

            if _selected_pid and _selected_pid in roster:
                _lost = roster[_selected_pid]
                _lost_val = float(_lost.get('adjusted_value', 0) or 0)
                _lost_mkt = float(_lost.get('market_value', 0) or 0)
                _lost_pos = _lost.get('position', '?')
                _lost_name = _lost.get('name', '?')
                _lost_grade = float(_lost.get('core_grade', 0) or 0)

                _new_total_val = _current_total_val - _lost_val
                _new_total_mkt = _current_total_mkt - _lost_mkt

                # Before/After visual comparison card
                _new_alpha = _new_total_val - _new_total_mkt
                st.markdown(
                    f'<div style="display:flex;gap:16px;margin:12px 0;">'
                    f'<div style="flex:1;background:#f6f8fa;border:1px solid #e5e7eb;border-radius:8px;padding:16px;text-align:center;">'
                    f'<div style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Before</div>'
                    f'<div style="font-size:20px;font-weight:800;color:#1f2937;margin:4px 0;">{fmt_money(int(_current_total_val))}</div>'
                    f'<div style="font-size:12px;color:#6b7280;">Team Value \u00b7 {_current_count} players</div>'
                    f'<div style="font-size:14px;font-family:DM Mono,monospace;color:{"#16A34A" if _current_total_alpha > 0 else "#DC2626"};">'
                    f'Alpha: {"+" if _current_total_alpha > 0 else "-" if _current_total_alpha < 0 else ""}{fmt_money(abs(int(_current_total_alpha)))}</div></div>'
                    f'<div style="display:flex;align-items:center;font-size:24px;color:#6b7280;">\u2192</div>'
                    f'<div style="flex:1;background:#f6f8fa;border:1px solid {"#DC2626" if _lost_val > 0 else "#e5e7eb"};border-radius:8px;padding:16px;text-align:center;">'
                    f'<div style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">After (without {_lost_name})</div>'
                    f'<div style="font-size:20px;font-weight:800;color:#1f2937;margin:4px 0;">{fmt_money(int(_new_total_val))}</div>'
                    f'<div style="font-size:12px;color:#6b7280;">Team Value \u00b7 {_current_count - 1} players</div>'
                    f'<div style="font-size:14px;font-family:DM Mono,monospace;color:{"#16A34A" if _new_alpha > 0 else "#DC2626"};">'
                    f'Alpha: {"+" if _new_alpha > 0 else "-" if _new_alpha < 0 else ""}{fmt_money(abs(int(_new_alpha)))}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                _wi1, _wi2, _wi3, _wi4 = st.columns(4)
                _wi1.metric("Roster Value", fmt_money(int(_new_total_val)),
                            delta=f"-{fmt_money(int(_lost_val))}", delta_color="inverse")
                _wi2.metric("Market Cost", fmt_money(int(_new_total_mkt)),
                            delta=f"-{fmt_money(int(_lost_mkt))}", delta_color="normal")
                _wi3.metric("Players", _current_count - 1, delta="-1")
                _freed = int(_lost_mkt)
                _wi4.metric("Budget Freed", fmt_money(_freed))

                # Show what you could get with that freed budget at the same position
                st.markdown(f"**Replacement options at {_lost_pos}** (within freed budget of {fmt_money(_freed)})")
                _replacements = df[
                    (df['position'] == _lost_pos) &
                    (~df['player_id'].isin([int(k) for k in roster.keys() if str(k).isdigit()])) &
                    (df['market_value'].fillna(0) <= _freed * 1.1)
                ].sort_values('output_score', ascending=False).head(10)

                if _replacements.empty:
                    st.info(f"No available {_lost_pos} players within budget.")
                else:
                    _rep_display = _replacements[['name', 'school', 'tier', 'core_grade', 'output_score',
                                                   'adjusted_value', 'market_value']].copy()
                    _rep_display.columns = ['Name', 'School', 'Tier', 'Grade', 'Output', 'Value', 'Mkt']
                    _rep_display['Value'] = _rep_display['Value'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
                    _rep_display['Mkt'] = _rep_display['Mkt'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
                    _rep_display['Grade'] = _rep_display['Grade'].round(1)
                    _rep_display['Output'] = _rep_display['Output'].round(1)
                    st.dataframe(_rep_display, use_container_width=True, hide_index=True)

        elif _scenario == "Budget Change":
            st.markdown("**How does a budget increase or decrease affect your flexibility?**")
            _new_budget = st.slider("Adjusted Budget ($)", min_value=500_000, max_value=50_000_000,
                                     value=budget, step=500_000, format="$%d", key="whatif_budget")
            _budget_delta = _new_budget - budget
            _new_remaining = _new_budget - int(_current_total_mkt)

            _budget_delta_str = f"+{fmt_money(abs(_budget_delta))}" if _budget_delta >= 0 else f"-{fmt_money(abs(_budget_delta))}"
            _wb1, _wb2, _wb3 = st.columns(3)
            _wb1.metric("New Budget", fmt_money(_new_budget), delta=_budget_delta_str)
            _wb2.metric("Current Spend", fmt_money(int(_current_total_mkt)))
            _wb3.metric("Remaining", fmt_money(_new_remaining), delta=_budget_delta_str)

            if _new_remaining > 0:
                # Show positions with gaps that could be filled
                _pos_counts = roster_df['position'].value_counts()
                _ideal_counts = {'QB': 2, 'RB': 3, 'WR': 5, 'TE': 2, 'OT': 4, 'IOL': 4,
                                 'EDGE': 4, 'IDL': 3, 'LB': 4, 'CB': 4, 'S': 3}
                _gaps = []
                for _pos, _ideal in _ideal_counts.items():
                    _have = int(_pos_counts.get(_pos, 0))
                    if _have < _ideal:
                        _gap = _ideal - _have
                        _avg_cost = df[df['position'] == _pos]['market_value'].fillna(0).mean()
                        _gaps.append({'Position': _pos, 'Have': _have, 'Need': _ideal,
                                      'Gap': _gap, 'Avg Cost': int(_avg_cost),
                                      'Est Fill Cost': int(_avg_cost * _gap)})
                if _gaps:
                    _gap_df = pd.DataFrame(_gaps).sort_values('Est Fill Cost', ascending=False)
                    _gap_df['Avg Cost'] = _gap_df['Avg Cost'].apply(fmt_money)
                    _gap_df['Est Fill Cost'] = _gap_df['Est Fill Cost'].apply(fmt_money)
                    st.markdown("**Positions you could fill with extra budget:**")
                    st.dataframe(_gap_df, use_container_width=True, hide_index=True)
            else:
                st.error(f"You're **over budget** by {fmt_money(abs(_new_remaining))}. Consider removing players.")

        elif _scenario == "Market Inflation/Deflation":
            st.markdown("**What if NIL market rates shift across the board?**")
            _inflation = st.slider("Market Rate Change (%)", min_value=-30, max_value=50,
                                    value=0, step=5, format="%d%%", key="whatif_inflation")
            _multiplier = 1 + (_inflation / 100)

            _inflated_mkt = _current_total_mkt * _multiplier
            _mkt_delta = _inflated_mkt - _current_total_mkt
            _inflated_remaining = budget - int(_inflated_mkt)

            # Before/After visual comparison card
            st.markdown(
                f'<div style="display:flex;gap:16px;margin:12px 0;">'
                f'<div style="flex:1;background:#f6f8fa;border:1px solid #e5e7eb;border-radius:8px;padding:16px;text-align:center;">'
                f'<div style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Current Market</div>'
                f'<div style="font-size:20px;font-weight:800;color:#1f2937;margin:4px 0;">{fmt_money(int(_current_total_mkt))}</div>'
                f'<div style="font-size:12px;color:#6b7280;">Budget Left: {fmt_money(budget_remaining)}</div></div>'
                f'<div style="display:flex;align-items:center;font-size:24px;color:#6b7280;">\u2192</div>'
                f'<div style="flex:1;background:#f6f8fa;border:1px solid {"#DC2626" if _inflated_remaining < 0 else "#e5e7eb"};border-radius:8px;padding:16px;text-align:center;">'
                f'<div style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">At {_inflation:+d}% Inflation</div>'
                f'<div style="font-size:20px;font-weight:800;color:#1f2937;margin:4px 0;">{fmt_money(int(_inflated_mkt))}</div>'
                f'<div style="font-size:12px;color:{"#DC2626" if _inflated_remaining < 0 else "#6b7280"};">Budget Left: {fmt_money(_inflated_remaining)}</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            _mi1, _mi2, _mi3 = st.columns(3)
            _mkt_delta_int = int(_mkt_delta)
            _mkt_delta_str = f"+{fmt_money(abs(_mkt_delta_int))}" if _mkt_delta_int >= 0 else f"-{fmt_money(abs(_mkt_delta_int))}"
            _mi1.metric("Projected Market Cost", fmt_money(int(_inflated_mkt)),
                        delta=_mkt_delta_str, delta_color="inverse")
            _mi2.metric("Budget Remaining", fmt_money(_inflated_remaining))
            _val_vs_mkt = int(_current_total_val - _inflated_mkt)
            _val_vs_mkt_str = f"+{fmt_money(abs(_val_vs_mkt))}" if _val_vs_mkt >= 0 else f"-{fmt_money(abs(_val_vs_mkt))}"
            _mi3.metric("Value vs Market", _val_vs_mkt_str)

            # Show per-position impact
            _pos_impact = []
            for _pos in roster_df['position'].unique():
                _pos_df = roster_df[roster_df['position'] == _pos]
                _pos_mkt = _pos_df['market_value'].fillna(0).astype(float).sum()
                _pos_new = _pos_mkt * _multiplier
                _pos_impact.append({
                    'Position': _pos,
                    'Players': len(_pos_df),
                    'Current Mkt': fmt_money(int(_pos_mkt)),
                    f'At {_inflation:+d}%': fmt_money(int(_pos_new)),
                    'Change': fmt_money(int(_pos_new - _pos_mkt)),
                })
            if _pos_impact:
                st.dataframe(pd.DataFrame(_pos_impact), use_container_width=True, hide_index=True)

            if _inflation > 0 and _inflated_remaining < 0:
                st.warning(f"A {_inflation}% market inflation would put you **{fmt_money(abs(_inflated_remaining))} over budget**. "
                           "Consider locking in deals now or targeting undervalued players.")

        elif _scenario == "Position Upgrade":
            st.markdown("**Find an upgrade at a specific position.**")
            _upgrade_pos = st.selectbox("Position to upgrade", POSITIONS[1:], key="whatif_upgrade_pos")

            _current_at_pos = roster_df[roster_df['position'] == _upgrade_pos]
            if _current_at_pos.empty:
                st.info(f"You have no {_upgrade_pos} on your roster. Add one from the Player Market.")
            else:
                _worst = _current_at_pos.sort_values('output_score').iloc[0]
                _worst_score = float(_worst.get('output_score', 0) or 0)
                _worst_mkt = float(_worst.get('market_value', 0) or 0)
                _worst_name = _worst.get('name', '?')

                st.markdown(f"**Weakest {_upgrade_pos}:** {_worst_name} (Output: {_worst_score:.1f}, Mkt: {fmt_money(int(_worst_mkt))})")
                st.markdown(f"If you drop {_worst_name}, you free {fmt_money(int(_worst_mkt))} + remaining budget = "
                            f"**{fmt_money(int(_worst_mkt + budget_remaining))} available**")

                _upgrade_budget = _worst_mkt + max(0, budget_remaining)
                _upgrades = df[
                    (df['position'] == _upgrade_pos) &
                    (~df['player_id'].isin([int(k) for k in roster.keys() if str(k).isdigit()])) &
                    (df['output_score'] > _worst_score) &
                    (df['market_value'].fillna(0) <= _upgrade_budget * 1.1)
                ].sort_values('output_score', ascending=False).head(10)

                if _upgrades.empty:
                    st.info("No upgrades available within budget.")
                else:
                    _up_display = _upgrades[['name', 'school', 'tier', 'core_grade', 'output_score',
                                              'adjusted_value', 'market_value']].copy()
                    _up_display.columns = ['Name', 'School', 'Tier', 'Grade', 'Output', 'Value', 'Mkt']
                    _up_display['Δ Output'] = (_up_display['Output'] - _worst_score).round(1)
                    _up_display['Value'] = _up_display['Value'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
                    _up_display['Mkt'] = _up_display['Mkt'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
                    _up_display['Grade'] = _up_display['Grade'].round(1)
                    _up_display['Output'] = _up_display['Output'].round(1)
                    st.dataframe(_up_display, use_container_width=True, hide_index=True)

else:
    # ── LIST VIEW ──
    st.markdown("### Your Roster")

    if not roster:
        st.markdown(
            '<div style="text-align:center;padding:48px 24px;background:#f6f8fa;border:1px dashed #e5e7eb;border-radius:12px;margin:16px 0;">'
            '<div style="font-size:48px;margin-bottom:12px;">📋</div>'
            '<div style="font-size:18px;font-weight:700;color:#1f2937;margin-bottom:8px;">No players on your roster yet</div>'
            '<div style="font-size:13px;color:#6b7280;max-width:400px;margin:0 auto;">'
            'Search the <strong style="color:#E8390E;">Player Market</strong> below and add players to start building your team.'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        roster_df = pd.DataFrame(list(roster.values()))

        # Position filter for roster view
        roster_positions = sorted(roster_df['position'].unique().tolist())
        roster_pos_filter = st.selectbox("Filter Position", ["All"] + roster_positions, key="roster_pos_filter")

        if roster_pos_filter != "All":
            display_roster = roster_df[roster_df['position'] == roster_pos_filter]
        else:
            display_roster = roster_df

        if display_roster.empty:
            st.markdown(
                '<div style="text-align:center;padding:24px;color:#6b7280;font-size:13px;">'
                'No players rostered at this position yet.</div>',
                unsafe_allow_html=True,
            )
        else:
            display_roster = display_roster.sort_values('output_score', ascending=False).reset_index(drop=True)

            stat_cols = None
            stat_data = None
            if roster_pos_filter != "All" and roster_pos_filter in POSITION_KEY_STATS:
                stat_cols = POSITION_KEY_STATS[roster_pos_filter]
                stat_data = _load_stats_for_position(roster_pos_filter, season)

            _render_gm_table(display_roster, roster_ids, "roster", stat_cols, stat_data, show_add=False)

        st.markdown("---")

        # Roster analysis
        st.markdown("### Roster Analysis")
        if total_alpha > 0:
            st.success(f"Your roster is **undervalued** by {fmt_money(total_alpha)}. "
                       f"You're getting {fmt_money(total_alpha)} more production than market price.")
        elif total_alpha < -100000:
            st.warning(f"Your roster is **overvalued** by {fmt_money(abs(total_alpha))}. "
                       f"You're overpaying relative to production.")
        else:
            st.info("Your roster is **fairly valued** -- market cost matches production value.")

        if budget_remaining < 0:
            st.error(f"You're **over budget** by {fmt_money(abs(budget_remaining))}. "
                     "Remove players or increase your budget.")

        st.markdown("---")
        _exp_col, _clr_col = st.columns(2)
        with _exp_col:
            export_roster_csv(roster, budget)
        with _clr_col:
            if st.button("⚠️ Clear Entire Roster", type="primary", key="clear_list"):
                st.session_state['gm_roster'] = {}
                st.session_state['gm_slot_assignments'] = {}
                _autosave_roster()
                st.rerun()


# ══════════════════════════════════════════════════
# ── Player Market (Search & Add) — always visible ──
# ══════════════════════════════════════════════════
st.markdown("---")

# ── Player Market header + Prospect toggle (prominent) ──
pm_left, pm_right = st.columns([3, 2])
with pm_left:
    st.markdown("### Player Market")
with pm_right:
    include_freshmen = st.toggle(
        "Include 2025/2026 Prospects",
        value=False,
        key="gm_freshmen",
        help="Add ESPN 300 recruits (2025 & 2026 classes) to the player pool with projected valuations based on recruit grade and ranking.",
    )

# Build conference and school lists from the data
conferences = ['All'] + sorted(df['conference'].dropna().unique().tolist())
schools = ['All'] + sorted(df['school'].dropna().unique().tolist())

s1, s2, s3, s4, s5 = st.columns([2, 0.8, 0.6, 1, 1])
search_name = s1.text_input("Search", placeholder="Search by name...", key="gm_search")
filter_pos = s2.selectbox("Position", POSITIONS, key="gm_pos")
filter_tier = s3.selectbox("Tier", ['All', 'T1', 'T2', 'T3', 'T4'], key="gm_tier")
filter_conf = s4.selectbox("Conference", conferences, key="gm_conf")
filter_school = s5.selectbox("School", schools, key="gm_school")

# Filter the data
market_df = df.copy()
if search_name and len(search_name) >= 2:
    market_df = market_df[market_df['name'].str.contains(search_name, case=False, na=False)]
if filter_pos != 'All':
    market_df = market_df[market_df['position'] == filter_pos]
if filter_tier != 'All':
    market_df = market_df[market_df['tier'] == filter_tier]
if filter_conf != 'All':
    market_df = market_df[market_df['conference'] == filter_conf]
if filter_school != 'All':
    market_df = market_df[market_df['school'] == filter_school]

# Smart filters row
_filt_col1, _filt_col2, _filt_col3 = st.columns([1, 1, 3])
with _filt_col1:
    affordable_only = st.checkbox("Affordable only", key="gm_affordable",
                                   help="Show only players whose Market Value fits within your remaining budget")
with _filt_col2:
    portal_targets = st.checkbox("Portal Targets", key="gm_portal",
                                  help="G6/FCS players with T1/T2 output — undervalued transfer targets")
if affordable_only and 'market_value' in market_df.columns:
    market_df = market_df[market_df['market_value'].fillna(0) <= budget_remaining]
if portal_targets:
    _portal_mask = (
        (market_df['market'].isin(['G6', 'FCS'])) &
        (market_df['tier'].isin(['T1', 'T2'])) &
        (market_df['output_score'].fillna(0) >= 65)
    )
    if 'flags' in market_df.columns:
        _portal_flag_mask = market_df['flags'].apply(
            lambda x: 'PORTAL_VALUE' in (json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else []))
            if pd.notna(x) else False
        )
        _portal_mask = _portal_mask | _portal_flag_mask
    market_df = market_df[_portal_mask]

# ── Flag filter buttons ──
if 'gm_active_flag_filter' not in st.session_state:
    st.session_state['gm_active_flag_filter'] = None

# Count flags in the current (filtered) market_df
_gm_flag_counts = {}
if 'flags' in market_df.columns:
    for _, _row in market_df.iterrows():
        _flags_raw = _row.get('flags', '[]')
        try:
            _flag_list = json.loads(_flags_raw) if isinstance(_flags_raw, str) else (_flags_raw if isinstance(_flags_raw, list) else [])
        except (json.JSONDecodeError, TypeError):
            _flag_list = []
        for _f in _flag_list:
            _gm_flag_counts[_f] = _gm_flag_counts.get(_f, 0) + 1

_gm_flag_cols = st.columns(len(FLAG_CONFIG) + 1)
with _gm_flag_cols[0]:
    _all_active = st.session_state['gm_active_flag_filter'] is None
    if st.button(f"All ({len(market_df):,})", key="gm_flag_all", use_container_width=True,
                 type="primary" if _all_active else "secondary"):
        st.session_state['gm_active_flag_filter'] = None
        st.rerun()

for _i, (_flag_key, _config) in enumerate(FLAG_CONFIG.items(), 1):
    _count = _gm_flag_counts.get(_flag_key, 0)
    _is_active = st.session_state['gm_active_flag_filter'] == _flag_key
    with _gm_flag_cols[_i]:
        if st.button(f"{_config['icon']} {_config['label']} ({_count})", key=f"gm_flag_{_flag_key}",
                     use_container_width=True, type="primary" if _is_active else "secondary"):
            st.session_state['gm_active_flag_filter'] = _flag_key
            st.rerun()

# Apply flag filter
_gm_active_flag = st.session_state.get('gm_active_flag_filter')
if _gm_active_flag and 'flags' in market_df.columns:
    market_df = market_df[market_df['flags'].apply(
        lambda x: _gm_active_flag in (json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else []))
        if pd.notna(x) else False
    )]

# ── Append Prospects if toggled ──
if include_freshmen:
    prospects = load_all_prospects([2025, 2026])
    if prospects:
        fresh_df = pd.DataFrame(prospects)
        # Apply same filters
        if search_name and len(search_name) >= 2:
            fresh_df = fresh_df[fresh_df['name'].str.contains(search_name, case=False, na=False)]
        if filter_pos != 'All':
            fresh_df = fresh_df[fresh_df['position'] == filter_pos]
        if filter_tier != 'All':
            fresh_df = fresh_df[fresh_df['tier'] == filter_tier]
        if filter_school != 'All':
            fresh_df = fresh_df[fresh_df['school'] == filter_school]
        # Merge — prospects go after current players
        if not fresh_df.empty:
            # Add missing columns to fresh_df to match market_df
            for col in market_df.columns:
                if col not in fresh_df.columns:
                    fresh_df[col] = None
            # Keep only matching columns
            fresh_df = fresh_df[[c for c in market_df.columns if c in fresh_df.columns]]
            market_df = pd.concat([market_df, fresh_df], ignore_index=True)
    st.markdown(
        '<p style="font-size:11px;color:#E8390E;font-weight:600;">🌟 Showing 2025/2026 prospects '
        '(projected values based on ESPN 300 Grade)</p>',
        unsafe_allow_html=True,
    )

# Sort by output_score
market_df = market_df.sort_values('output_score', ascending=False).reset_index(drop=True)

if market_df.empty:
    st.markdown(
        '<div style="text-align:center;padding:32px 16px;color:#6b7280;font-size:13px;">'
        '🔍 No players match your search. Try adjusting your filters.</div>',
        unsafe_allow_html=True,
    )
else:
    # ── Quick-Add Multiselect ──
    available_for_add = market_df[~market_df['player_id'].isin(roster_ids)]
    name_to_row = {}
    multiselect_options = []
    for _, row in available_for_add.iterrows():
        name = row.get('name', '?')
        pos = row.get('position', '--')
        school = row.get('school', '--')
        out_s = float(row.get('output_score', 0)) if pd.notna(row.get('output_score')) else 0
        display_label = f"{name} ({pos}, {school}, {out_s:.1f})"
        multiselect_options.append(display_label)
        name_to_row[display_label] = row.to_dict()

    quick_add = st.multiselect(
        "Quick Add Players",
        options=multiselect_options,
        default=[],
        placeholder="Search and select players to add...",
        key="gm_quick_add",
    )

    if quick_add:
        qa_col1, qa_col2 = st.columns([4, 1])
        with qa_col2:
            st.button(
                f"Add {len(quick_add)} Player{'s' if len(quick_add) != 1 else ''}",
                key="gm_qa_btn",
                on_click=_add_players_from_multiselect,
                args=(quick_add, name_to_row),
                type="primary",
            )

    # ── Global Sort ──
    _sort_options = {
        'Output (High → Low)': ('output_score', False),
        'Value (High → Low)': ('adjusted_value', False),
        'Value (Low → High)': ('adjusted_value', True),
        'Mkt (High → Low)': ('market_value', False),
        'Mkt (Low → High)': ('market_value', True),
        'Alpha (Best Value)': ('opportunity_score', False),
        'Alpha (Most Overvalued)': ('opportunity_score', True),
        'Grade (High → Low)': ('core_grade', False),
    }
    _sort_col1, _sort_col2, _sort_col3 = st.columns([1.2, 0.5, 3.3])
    with _sort_col1:
        _sort_choice = st.selectbox("Sort by", list(_sort_options.keys()), key="gm_sort",
                                     label_visibility="collapsed")
    with _sort_col2:
        PAGE_SIZE = st.selectbox("Rows", [25, 50, 100, 200], index=1, key="gm_rows_per_page",
                                  label_visibility="collapsed")
    _sort_field, _sort_asc = _sort_options[_sort_choice]
    if _sort_field in market_df.columns:
        market_df = market_df.sort_values(_sort_field, ascending=_sort_asc, na_position='last').reset_index(drop=True)

    # ── Pagination ──
    total_players = len(market_df)
    total_pages = max(1, math.ceil(total_players / PAGE_SIZE))

    current_page = st.session_state.get('gm_market_page', 0)
    if current_page >= total_pages:
        current_page = 0
        st.session_state['gm_market_page'] = 0

    start_idx = current_page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_players)
    page_df = market_df.iloc[start_idx:end_idx].reset_index(drop=True)

    st.markdown(
        f'<p style="font-size:12px;color:#6b7280;">Showing {start_idx + 1}–{end_idx} of {total_players} players (Page {current_page + 1}/{total_pages})</p>',
        unsafe_allow_html=True
    )

    # Load position stats if specific position selected
    market_stat_cols = None
    market_stat_data = None
    if filter_pos != 'All' and filter_pos in POSITION_KEY_STATS:
        market_stat_cols = POSITION_KEY_STATS[filter_pos]
        market_stat_data = _load_stats_for_position(filter_pos, season)

    _render_gm_table(page_df, roster_ids, "mkt", market_stat_cols, market_stat_data, show_add=True)

    # ── Pagination Controls ──
    if total_pages > 1:
        nav_cols = st.columns([1, 1, 3, 1, 1])
        with nav_cols[0]:
            st.button("First", key="pg_first", on_click=_set_market_page, args=(0,),
                       disabled=(current_page == 0))
        with nav_cols[1]:
            st.button("Prev", key="pg_prev", on_click=_set_market_page, args=(max(0, current_page - 1),),
                       disabled=(current_page == 0))
        with nav_cols[2]:
            st.markdown(
                f'<p style="text-align:center;font-size:13px;font-weight:600;color:#6b7280;padding-top:6px;">'
                f'Page {current_page + 1} of {total_pages}</p>',
                unsafe_allow_html=True
            )
        with nav_cols[3]:
            st.button("Next", key="pg_next", on_click=_set_market_page, args=(min(total_pages - 1, current_page + 1),),
                       disabled=(current_page >= total_pages - 1))
        with nav_cols[4]:
            st.button("Last", key="pg_last", on_click=_set_market_page, args=(total_pages - 1,),
                       disabled=(current_page >= total_pages - 1))

# ── Footer ──
render_footer()
