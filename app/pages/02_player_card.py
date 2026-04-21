"""
NILytics — Player Card (Baseball Card Detail Page)
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import (load_player_info, load_player_history, load_comps,
                       load_leaderboard, load_player_stats, load_position_percentiles,
                       get_player_note, save_player_note, get_transfer_status)
from app.components.card_front import render_card_front_st, fmt_money
from app.components.card_back import render_card_back
from app.components.stats_display import render_player_stats
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.components.exports import export_player_card_csv
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Player Search", page_icon="🏈", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inject fonts (after CSS so font-face rules layer correctly)
inject_fonts()

# Page-specific styles
st.markdown("""
<style>
/* Player header */
.player-header-name {
    font-size: 28px;
    font-weight: 800;
    line-height: 1.2;
    margin: 0;
    display: inline-block;
    color: #1f2937;
}
.player-header-meta {
    font-size: 14px;
    color: #6b7280;
    margin: 4px 0 0 0;
}
.tier-pill {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    vertical-align: middle;
    margin-left: 12px;
    position: relative;
    top: -2px;
}
.trend-badge {
    display: inline-block;
    font-size: 12px;
    padding: 3px 12px;
    border-radius: 999px;
    font-weight: 600;
    margin-top: 6px;
}
.trend-badge.traj-breakout { background: #16a34a; color: #ffffff; }
.trend-badge.traj-up       { background: #16a34a; color: #ffffff; }
.trend-badge.traj-down     { background: #dc2626; color: #ffffff; }
.trend-badge.traj-stable   { background: #f3f4f6; border: 1px solid #d1d5db; color: #374151; font-weight: 600; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 80px 20px;
    border: 2px dashed #d1d5db;
    border-radius: 12px;
    margin-top: 24px;
}

/* Section header (reaffirm the theme style) */
.section-header {
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid #E8390E;
    padding-bottom: 6px;
    margin-bottom: 12px;
    color: #6b7280;
}

/* Comparable player rows */
.comp-row {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 6px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    transition: background 0.15s ease;
    gap: 16px;
}
.comp-row:hover {
    background: #f9fafb;
}
.comp-name {
    font-weight: 600;
    font-size: 14px;
    color: #1f2937;
    flex: 1;
}
.comp-detail {
    font-size: 13px;
    color: #6b7280;
}

/* Search result rows */
.search-result-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 14px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 4px;
    background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.search-result-row:hover {
    background: #f9fafb;
    border-color: #d1d5db;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10);
}

/* Season selector tidy-up */
div[data-testid="stSelectbox"] > label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}

/* Compact player card layout */
div[data-testid="stMetric"] {
    padding: 10px 14px !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 22px !important;
}
div[data-testid="stMetric"] label {
    font-size: 10px !important;
}
.stMarkdown hr {
    margin: 0.75rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='player_card')

# Auth
user = check_auth()
render_user_sidebar()

# Get player ID from session or sidebar/query search
player_id = st.session_state.get('selected_player_id', None)
season = st.session_state.get('selected_season', 2025)

# Handle query param navigation (from leaderboard links)
qp = st.query_params
if 'pid' in qp:
    try:
        pid = int(qp['pid'])
        st.session_state['selected_player_id'] = pid
        player_id = pid
        st.query_params.clear()
    except (ValueError, TypeError):
        pass

# ── Main search bar (always visible at top) ──
search = st.text_input(
    "Search players",
    placeholder="Search by player name (e.g. Diego Pavia)...",
    label_visibility="collapsed",
    key="player_search_main",
)

if search and len(search) >= 2:
    df = load_leaderboard(season)
    if not df.empty:
        matches = df[df['name'].str.contains(search, case=False, na=False)].head(10)
        if not matches.empty:
            for _, row in matches.iterrows():
                pid = row['player_id']
                name = row['name']
                pos = row['position']
                school = row['school']
                tier = row.get('tier', '')
                output = float(row.get('output_score', 0)) if pd.notna(row.get('output_score')) else 0
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f'<div class="search-result-row">'
                        f'<span style="font-weight:600;font-size:14px;color:#1f2937;">{name}</span>'
                        f'<span style="font-size:12px;color:#6b7280;">{pos} · {school}</span>'
                        f'<span style="font-size:12px;color:#6b7280;">{tier}</span>'
                        f'<span style="font-size:12px;color:#6b7280;">Output {output:.1f}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if st.button("View →", key=f"search_nav_{pid}", type="primary"):
                        st.session_state['selected_player_id'] = pid
                        player_id = pid
                        # Clear the search box so the dropdown doesn't persist
                        if 'player_search_main' in st.session_state:
                            del st.session_state['player_search_main']
                        st.rerun()
        else:
            st.info(f'No players match "{search}".')

# Sidebar — back to leaderboard
st.sidebar.markdown(
    '<a href="/leaderboard" target="_self" style="display:inline-block;margin-bottom:12px;'
    'padding:8px 16px;border-radius:8px;background:#f3f4f6;border:1px solid #e5e7eb;'
    'color:#1f2937;font-size:13px;font-weight:600;text-decoration:none;">'
    '&larr; Back to Leaderboard</a>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# ── EMPTY STATE ──
if player_id is None:
    st.markdown('''
    <div class="empty-state" style="padding:40px 20px;">
        <div style="font-size:36px; margin-bottom:12px;">🔍</div>
        <h3 style="font-size:18px; font-weight:600; margin:0 0 6px 0; color:#1f2937;">Search for a Player</h3>
        <p style="color:#6b7280; margin:0; font-size:14px;">Type a name in the search bar above or click a player on the Leaderboard</p>
    </div>
    ''', unsafe_allow_html=True)
    render_footer()
    st.stop()

# ── LOAD PLAYER DATA ──
with st.spinner("Building player profile..."):
    player = load_player_info(player_id)
    if player is None:
        st.error(f"Player {player_id} not found.")
        render_footer()
        st.stop()

    scores_df, signals_df = load_player_history(player_id)

    if scores_df.empty:
        st.warning(f"No scores found for {player.get('name', player_id)}.")
        render_footer()
        st.stop()

    # Determine which season to show — prefer most recent season with data
    available = sorted(scores_df['season'].unique(), reverse=True)
    if season in scores_df['season'].values:
        latest_scores = scores_df[scores_df['season'] == season].iloc[0].to_dict()
    else:
        # Default to most recent season available for this player
        season = int(available[0])
        latest_scores = scores_df[scores_df['season'] == season].iloc[0].to_dict()
    latest_season = latest_scores['season']

    if not signals_df.empty and latest_season in signals_df['season'].values:
        latest_signals = signals_df[signals_df['season'] == latest_season].iloc[0].to_dict()
    else:
        latest_signals = {'market_value': 0, 'opportunity_score': 0, 'trajectory_flag': 'STABLE', 'flags': '[]'}

# ── PLAYER HEADER with inline season selector ──
_header_left, _header_right = st.columns([3, 1])
with _header_right:
    if len(scores_df) > 1:
        available_seasons = sorted(scores_df['season'].unique(), reverse=True)
        season_strs = [str(int(s)) for s in available_seasons]
        default_idx = list(available_seasons).index(latest_season) if latest_season in available_seasons else 0
        selected_str = st.selectbox("Season", season_strs, index=default_idx, key="pc_season")
        selected = int(selected_str)
        if selected != latest_season:
            latest_scores = scores_df[scores_df['season'] == selected].iloc[0].to_dict()
            latest_season = selected
            if not signals_df.empty and selected in signals_df['season'].values:
                latest_signals = signals_df[signals_df['season'] == selected].iloc[0].to_dict()
            else:
                latest_signals = {'market_value': 0, 'opportunity_score': 0, 'trajectory_flag': 'STABLE', 'flags': '[]'}
    else:
        st.markdown(f'<div style="text-align:right;padding-top:12px;font-size:13px;color:#6b7280;">Season: {int(latest_season)}</div>', unsafe_allow_html=True)

with _header_left:
    _name = player.get('name', 'Unknown')
    _pos = player.get('position', '?')
    _school = player.get('school', '?')
    _conference = player.get('conference', '')
    _market = player.get('market', '')
    _tier = latest_scores.get('tier', 'T4')
    _trajectory = latest_signals.get('trajectory_flag', 'STABLE')

    TIER_COLORS = {'T1': '#E8390E', 'T2': '#F97316', 'T3': '#3B82F6', 'T4': '#6B7280'}
    TIER_TEXT   = {'T1': '#fff',    'T2': '#fff',    'T3': '#fff',    'T4': '#fff'}
    TIER_LABELS = {'T1': 'TIER 1',  'T2': 'TIER 2',  'T3': 'TIER 3',  'T4': 'TIER 4'}
    TRAJ_LABELS = {
        'BREAKOUT': 'Breakout',
        'UP': 'Trending Up',
        'DOWN': 'Trending Down',
        'STABLE': 'Stable',
    }
    TRAJ_CSS = {
        'BREAKOUT': 'traj-breakout',
        'UP': 'traj-up',
        'DOWN': 'traj-down',
        'STABLE': 'traj-stable',
    }

    _tier_bg = TIER_COLORS.get(_tier, '#d0d0d0')
    _tier_fg = TIER_TEXT.get(_tier, '#666')
    _tier_label = TIER_LABELS.get(_tier, _tier)
    _traj_label = TRAJ_LABELS.get(_trajectory, 'Stable')
    _traj_css = TRAJ_CSS.get(_trajectory, 'traj-stable')

    # Build meta line — school is a clickable link to the team page
    _school_url = _school.replace(" ", "%20") if _school else ""
    _school_link = (
        f'<a href="/team?school={_school_url}" target="_self" '
        f'title="View {_school} roster" '
        f'style="color:inherit;text-decoration:none;border-bottom:1px dotted rgba(0,0,0,0.25);">{_school}</a>'
    ) if _school and _school != '?' else _school
    meta_parts = [p for p in [_pos, _school_link, _conference, _market] if p]

    # Transfer history for this player
    _transfers = get_transfer_status(player_id)
    _transfer_badge = ''
    if _transfers:
        _latest_xfer = _transfers[0]
        _xfer_tooltip = (f"Transferred from {_latest_xfer.get('from_school', '?')} "
                        f"to {_latest_xfer.get('to_school', '?')} ahead of {_latest_xfer.get('season', '?')} season")
        _transfer_badge = (
            f'<span title="{_xfer_tooltip}" '
            f'style="display:inline-block;background:#fef3c7;color:#92400e;font-size:11px;'
            f'font-weight:700;padding:3px 10px;border-radius:999px;margin-left:8px;'
            f'border:1px solid #fcd34d;letter-spacing:0.04em;cursor:help;">'
            f'🔁 TRANSFER</span>'
        )

    st.markdown(
        f'<p class="player-header-name">{_name}'
        f'<span class="tier-pill" style="background:{_tier_bg};color:{_tier_fg};" title="Tier based on Output Score percentile ranking">{_tier_label}</span>'
        f'{_transfer_badge}</p>'
        f'<p class="player-header-meta">{" &middot; ".join(meta_parts)}</p>'
        f'<span class="trend-badge {_traj_css}" title="Season-over-season trajectory trend">{_traj_label}</span>',
        unsafe_allow_html=True,
    )

# Historical data badge
_most_recent = int(sorted(scores_df['season'].unique(), reverse=True)[0])
if latest_season != _most_recent:
    st.markdown(
        f'<div style="background:#fef3c7;border:1px solid #fde047;color:#92400e;padding:8px 16px;border-radius:8px;'
        f'font-size:13px;margin-bottom:8px;">'
        f'📅 Viewing <b>{int(latest_season)}</b> historical data · '
        f'<a href="#" onclick="return false;" style="color:#92400e;text-decoration:underline;">Switch to {_most_recent} →</a>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── FRONT OF CARD (score metrics row — header rendered above) ──
_most_recent_season = int(sorted(scores_df['season'].unique(), reverse=True)[0])
render_card_front_st(player, latest_scores, latest_signals, st, skip_header=True,
                     season=int(latest_season), most_recent_season=_most_recent_season)

st.markdown(
    '<div style="text-align:right;margin-top:4px;margin-bottom:-8px;">'
    '<span style="font-size:12px;color:#6b7280;">How are these calculated? → </span>'
    '<a href="/methodology" target="_self" style="font-size:12px;color:#E8390E;font-weight:600;text-decoration:none;">Methodology</a>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ── PLAYER NOTES & TAGS ──
_user_email = user.get('email', 'test@nilytics.com')
_existing_note = get_player_note(player_id, _user_email)

STATUS_OPTIONS = ['Watching', 'Targeting', 'In Negotiation', 'Signed', 'Passed', 'Do Not Pursue']
STATUS_COLORS = {
    'Watching': '#6B7280', 'Targeting': '#3B82F6', 'In Negotiation': '#F97316',
    'Signed': '#16A34A', 'Passed': '#8b949e', 'Do Not Pursue': '#DC2626',
}
TAG_PRESETS = ['High Character', 'Academic Risk', 'Injury History', 'Portal Watch',
               'Staff Favorite', 'Top Priority', 'Budget Friendly', 'SEC Only',
               'Family Concerns', 'Visited Campus']

with st.expander("Notes & Tags", expanded=bool(_existing_note and _existing_note.get('note'))):
    _nc1, _nc2 = st.columns([3, 1])
    with _nc1:
        _note_text = st.text_area(
            "Notes",
            value=_existing_note.get('note', '') if _existing_note else '',
            placeholder="Add private notes about this player...",
            height=80,
            key="player_note_text",
            label_visibility="collapsed",
        )
    with _nc2:
        _current_status = _existing_note.get('status', 'Watching').title() if _existing_note else 'Watching'
        _status_idx = STATUS_OPTIONS.index(_current_status) if _current_status in STATUS_OPTIONS else 0
        _note_status = st.selectbox("Status", STATUS_OPTIONS, index=_status_idx, key="player_note_status")
        _sc = STATUS_COLORS.get(_note_status, '#6B7280')
        st.markdown(f'<span style="display:inline-block;background:{_sc}22;color:{_sc};border:1px solid {_sc};'
                    f'border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;">{_note_status}</span>',
                    unsafe_allow_html=True)

    _existing_tags = _existing_note.get('tags', []) if _existing_note else []
    _note_tags = st.multiselect("Tags", TAG_PRESETS, default=_existing_tags, key="player_note_tags",
                                 placeholder="Add tags...")

    if st.button("Save Notes", key="save_note", type="primary"):
        save_player_note(player_id, _user_email, _note_text, _note_tags, _note_status.lower())
        st.success("Notes saved")
        st.rerun()

st.markdown("---")

# ── KEY STATS with percentile highlighting ──
position = player.get('position', '?')

player_stats = load_player_stats(player_id, position, int(latest_season))
percentile_data = load_position_percentiles(position, int(latest_season))

if player_stats:
    st.markdown('<p class="section-header">Key Stats</p>', unsafe_allow_html=True)
    render_player_stats(player_stats, position, percentile_data)
else:
    st.info("No detailed stats available for this player/season.")

st.markdown("---")

# ── BACK OF CARD (Career History, Charts, Comps) ──
comps = load_comps(
    position=position,
    output_score=float(latest_scores.get('output_score', 50)),
    season=latest_season,
    player_id=player_id,
)

render_card_back(player, scores_df, signals_df, comps)

# ── CONTRACT PROJECTION ──
if len(scores_df) >= 1:
    seasons_played = len(scores_df)
    # NCAA allows 5 years of eligibility (with COVID extra year = 6 max)
    max_eligibility = 6
    est_remaining = max(0, max_eligibility - seasons_played)

    if est_remaining > 0:
        current_value = float(latest_scores.get('adjusted_value', 0))
        current_mkt = float(latest_signals.get('market_value', 0))
        trajectory = latest_signals.get('trajectory_flag', 'STABLE')

        # Growth rate based on trajectory
        growth_rates = {'BREAKOUT': 0.25, 'UP': 0.10, 'STABLE': 0.0, 'DOWN': -0.15}
        growth = growth_rates.get(trajectory, 0.0)

        # Project year-by-year
        proj_years = min(est_remaining, 3)  # Show up to 3 years
        proj_values = []
        proj_mkts = []
        cumulative = 0
        for yr in range(1, proj_years + 1):
            pv = current_value * ((1 + growth) ** yr)
            pm = current_mkt * ((1 + growth * 0.5) ** yr)  # market adjusts slower
            proj_values.append(pv)
            proj_mkts.append(pm)
            cumulative += pm

        st.markdown("---")
        st.markdown('<p class="section-header">Contract Projection</p>', unsafe_allow_html=True)
        st.caption(f"Based on {seasons_played} seasons played · ~{est_remaining} years of eligibility remaining · "
                   f"Trajectory: {trajectory.title()}")

        # Projection table — proper HTML table with borders
        _year_headers = ''.join(f'<th style="padding:8px 14px;text-align:center;font-size:13px;font-weight:700;color:#1f2937;">Year {yr + 1}</th>' for yr in range(proj_years))
        _value_cells = ''.join(f'<td style="padding:8px 14px;text-align:center;font-size:14px;font-weight:700;color:#374151;font-family:DM Mono,monospace;">{fmt_money(proj_values[yr])}</td>' for yr in range(proj_years))
        _mkt_cells = ''.join(f'<td style="padding:8px 14px;text-align:center;font-size:14px;font-weight:600;color:#6b7280;font-family:DM Mono,monospace;">{fmt_money(proj_mkts[yr])}</td>' for yr in range(proj_years))

        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;margin-bottom:8px;">'
            f'<thead><tr style="border-bottom:2px solid #e5e7eb;">'
            f'<th style="padding:8px 14px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase;"></th>'
            f'{_year_headers}</tr></thead>'
            f'<tbody>'
            f'<tr style="border-bottom:1px solid #e5e7eb;">'
            f'<td style="padding:8px 14px;font-size:12px;color:#6b7280;font-weight:600;">Proj. Value</td>'
            f'{_value_cells}</tr>'
            f'<tr style="border-bottom:1px solid #e5e7eb;">'
            f'<td style="padding:8px 14px;font-size:12px;color:#6b7280;font-weight:600;">Proj. Mkt Cost</td>'
            f'{_mkt_cells}</tr>'
            f'</tbody></table>',
            unsafe_allow_html=True,
        )

        # Total contract estimate
        total_contract = cumulative
        st.markdown(
            f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px 16px;margin-top:8px;">'
            f'<span style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Est. {proj_years}-Year Contract Value</span><br>'
            f'<span style="font-size:22px;font-weight:800;font-family:DM Mono,monospace;color:#1f2937;">'
            f'{fmt_money(total_contract)}</span>'
            f'<span style="font-size:12px;color:#6b7280;margin-left:8px;">based on {trajectory.lower()} trajectory</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── CLICKABLE COMPARABLE PLAYERS ──
if comps is not None and not comps.empty:
    st.markdown("---")
    st.markdown('<p class="section-header">Navigate to a Comparable Player</p>', unsafe_allow_html=True)

    for idx, comp_row in comps.iterrows():
        comp_name = comp_row.get('name', '?')
        comp_school = comp_row.get('school', '?')
        comp_output = comp_row.get('output_score', 0)
        comp_tier = comp_row.get('tier', 'T4')
        comp_value = comp_row.get('adjusted_value', 0)
        comp_pid = comp_row.get('player_id', None)

        # Format Alpha (opportunity_score)
        comp_alpha = comp_row.get('opportunity_score', 0)
        comp_alpha_val = int(float(comp_alpha)) if pd.notna(comp_alpha) else 0
        if comp_alpha_val > 0:
            alpha_html = f'<span style="color:#22c55e;font-weight:700;font-size:13px;">+{fmt_money(abs(comp_alpha_val))}</span>'
        elif comp_alpha_val < 0:
            alpha_html = f'<span style="color:#ef4444;font-weight:700;font-size:13px;">-{fmt_money(abs(comp_alpha_val))}</span>'
        else:
            alpha_html = f'<span style="color:#8b949e;font-size:13px;">$0</span>'

        col_info, col_btn = st.columns([5, 1])
        with col_info:
            st.markdown(
                f'<div class="comp-row">'
                f'<span class="comp-name">{comp_name}</span>'
                f'<span class="comp-detail">{comp_school}</span>'
                f'<span class="comp-detail">Output {float(comp_output):.1f}</span>'
                f'<span class="comp-detail">{comp_tier}</span>'
                f'<span class="comp-detail">{fmt_money(comp_value)}</span>'
                f'<span class="comp-detail">Alpha {alpha_html}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if comp_pid and st.button("View", key=f"comp_nav_{comp_pid}_{idx}"):
                st.session_state['selected_player_id'] = comp_pid
                st.rerun()

# ── Compare Players ──
st.markdown("---")

# Initialize compare list
if 'compare_players' not in st.session_state:
    st.session_state['compare_players'] = {}

_cmp_cols = st.columns([1, 1, 3])
_already_added = player_id in st.session_state['compare_players']
with _cmp_cols[0]:
    if _already_added:
        if st.button("Remove from Compare", key="remove_compare"):
            del st.session_state['compare_players'][player_id]
            st.rerun()
    else:
        if st.button("Add to Compare", key="add_compare", type="primary",
                     disabled=len(st.session_state['compare_players']) >= 4):
            st.session_state['compare_players'][player_id] = {
                'name': player.get('name', '?'),
                'position': player.get('position', '?'),
                'school': player.get('school', '?'),
                'conference': player.get('conference', ''),
                'market': player.get('market', ''),
                'tier': latest_scores.get('tier', 'T4'),
                'core_grade': float(latest_scores.get('core_grade', 0)),
                'output_score': float(latest_scores.get('output_score', 0)),
                'adjusted_value': float(latest_scores.get('adjusted_value', 0)),
                'market_value': float(latest_signals.get('market_value', 0)),
                'opportunity_score': float(latest_signals.get('opportunity_score', 0)),
                'trajectory_flag': latest_signals.get('trajectory_flag', 'STABLE'),
                'flags': latest_signals.get('flags', '[]'),
            }
            st.rerun()
with _cmp_cols[1]:
    if st.session_state['compare_players']:
        if st.button("Clear Compare", key="clear_compare"):
            st.session_state['compare_players'] = {}
            st.rerun()
with _cmp_cols[2]:
    if st.session_state['compare_players']:
        _names = [p['name'] for p in st.session_state['compare_players'].values()]
        _col_a, _col_b = st.columns([3, 1])
        with _col_a:
            st.caption(f"Comparing: {', '.join(_names)} ({len(_names)}/4)")
        with _col_b:
            if st.button("Full View →", key="goto_compare_page", use_container_width=True):
                st.switch_page("pages/11_compare.py")

# Render comparison table if 2+ players
if len(st.session_state['compare_players']) >= 2:
    st.markdown('<p class="section-header">Side-by-Side Comparison</p>', unsafe_allow_html=True)

    cmp_data = st.session_state['compare_players']
    cmp_pids = list(cmp_data.keys())
    n = len(cmp_pids)

    TIER_COLORS_CMP = {'T1': '#E8390E', 'T2': '#F97316', 'T3': '#3B82F6', 'T4': '#6B7280'}
    TRAJ_COLORS_CMP = {'UP': '#16A34A', 'BREAKOUT': '#16A34A', 'DOWN': '#DC2626', 'STABLE': '#6B7280'}

    # Build rows: each metric as a row, each player as a column
    metrics = [
        ('Position', lambda p: p['position']),
        ('School', lambda p: p['school']),
        ('Conference', lambda p: p['conference']),
        ('Market', lambda p: p['market']),
        ('Tier', lambda p: p['tier']),
        ('Core Grade', lambda p: f"{p['core_grade']:.1f}"),
        ('Output Score', lambda p: f"{p['output_score']:.1f}"),
        ('Value', lambda p: fmt_money(p['adjusted_value'])),
        ('Mkt Value', lambda p: fmt_money(p['market_value'])),
        ('Alpha', lambda p: fmt_money(p['opportunity_score'])),
        ('Trajectory', lambda p: p['trajectory_flag'].title()),
    ]

    # Header row
    header_cols = st.columns([1.2] + [1] * n)
    header_cols[0].markdown("**Metric**")
    for i, pid in enumerate(cmp_pids):
        p = cmp_data[pid]
        _tc = TIER_COLORS_CMP.get(p['tier'], '#6B7280')
        header_cols[i + 1].markdown(
            f"**{p['name']}**<br>"
            f"<span style='font-size:11px;color:{_tc};font-weight:700;'>{p['tier']}</span>",
            unsafe_allow_html=True,
        )

    # Metric rows
    for label, fn in metrics:
        row_cols = st.columns([1.2] + [1] * n)
        row_cols[0].markdown(f"<span style='font-size:12px;color:#6b7280;'>{label}</span>",
                             unsafe_allow_html=True)
        # Find best value for highlighting (numeric metrics)
        vals = []
        for pid in cmp_pids:
            vals.append(fn(cmp_data[pid]))

        for i, pid in enumerate(cmp_pids):
            val = fn(cmp_data[pid])
            # Highlight best for key numeric metrics
            is_best = False
            if label in ('Core Grade', 'Output Score', 'Value', 'Alpha'):
                try:
                    num_vals = []
                    for v in vals:
                        cleaned = v.replace('$', '').replace(',', '').replace('+', '')
                        num_vals.append(float(cleaned))
                    is_best = (float(val.replace('$', '').replace(',', '').replace('+', '')) == max(num_vals))
                except (ValueError, AttributeError):
                    pass
            elif label == 'Mkt Value':
                try:
                    num_vals = []
                    for v in vals:
                        cleaned = v.replace('$', '').replace(',', '').replace('+', '')
                        num_vals.append(float(cleaned))
                    is_best = (float(val.replace('$', '').replace(',', '').replace('+', '')) == min(num_vals))
                except (ValueError, AttributeError):
                    pass

            style = "font-weight:700;color:#1f2937;" if is_best else "color:#6b7280;"
            row_cols[i + 1].markdown(
                f"<span style='font-size:13px;{style}'>{val}</span>",
                unsafe_allow_html=True,
            )

    # Navigate buttons
    nav_cols = st.columns([1.2] + [1] * n)
    nav_cols[0].markdown("")
    for i, pid in enumerate(cmp_pids):
        if nav_cols[i + 1].button("View Card", key=f"cmp_nav_{pid}"):
            st.session_state['selected_player_id'] = pid
            st.rerun()

# ── Add to GM Roster / Recruiting Class ──
st.markdown("---")
_add_cols = st.columns([1, 1, 3])
with _add_cols[0]:
    if st.button("➕ Add to GM Roster", key="add_to_gm", type="primary"):
        if 'gm_roster' not in st.session_state:
            st.session_state['gm_roster'] = {}
        # Use int key to match gm_mode's convention
        _pid_int = int(player_id)
        if _pid_int not in st.session_state['gm_roster']:
            st.session_state['gm_roster'][_pid_int] = {
                'player_id': _pid_int,
                'name': player.get('name', '?'),
                'position': player.get('position', '?'),
                'school': player.get('school', '?'),
                'conference': player.get('conference', ''),
                'market': player.get('market', ''),
                'tier': latest_scores.get('tier', 'T4'),
                'core_grade': latest_scores.get('core_grade', 0),
                'output_score': latest_scores.get('output_score', 0),
                'adjusted_value': latest_scores.get('adjusted_value', 0),       # production worth
                'market_value': latest_signals.get('market_value', 0),          # market rate
                'opportunity_score': latest_signals.get('opportunity_score', 0),
                'trajectory_flag': latest_signals.get('trajectory_flag', 'STABLE'),
                'flags': latest_signals.get('flags', '[]'),
            }
            # Persist to DB so the roster survives refresh
            try:
                from app.data import save_autosave_roster
                save_autosave_roster(
                    user_email=user.get('email', 'test@nilytics.com'),
                    season=int(latest_season) if latest_season else 2025,
                    roster_data=st.session_state['gm_roster'],
                    slot_assignments=st.session_state.get('gm_slot_assignments', {}),
                    off_formation=st.session_state.get('off_formation', 'Pro'),
                    def_formation=st.session_state.get('def_formation', '4-3'),
                    budget_preset=st.session_state.get('gm_budget_preset', 'Elite P4 Program'),
                )
            except Exception:
                pass
            st.success(f"Added {player.get('name', '?')} to GM Roster!")
        else:
            st.info(f"{player.get('name', '?')} is already on your GM Roster.")
with _add_cols[1]:
    if st.button("➕ Add to Recruiting Class", key="add_to_rc"):
        if 'recruit_class' not in st.session_state:
            st.session_state['recruit_class'] = {}
        _pid_str = str(player_id)
        if _pid_str not in st.session_state['recruit_class']:
            st.session_state['recruit_class'][_pid_str] = {
                'player_id': player_id,
                'name': player.get('name', '?'),
                'position': player.get('position', '?'),
                'school': player.get('school', '?'),
                'tier': latest_scores.get('tier', 'T4'),
                'core_grade': latest_scores.get('core_grade', 0),
                'output_score': latest_scores.get('output_score', 0),
                'adjusted_value': latest_scores.get('adjusted_value', 0),
                'market_value': latest_scores.get('adjusted_value', 0),
                'opportunity_score': latest_signals.get('opportunity_score', 0),
                'trajectory_flag': latest_signals.get('trajectory_flag', 'STABLE'),
                'flags': latest_signals.get('flags', '[]'),
                '_source': 'player_card',
            }
            st.success(f"Added {player.get('name', '?')} to Recruiting Class!")
        else:
            st.info(f"{player.get('name', '?')} is already in your Recruiting Class.")

# ── Export ──
st.markdown("---")
export_player_card_csv(player, scores_df, signals_df)

# ── Footer ──
render_footer()
