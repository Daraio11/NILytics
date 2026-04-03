"""
NILytics — My Board / Watchlist
Aggregated view of all players you've tagged with Notes & Tags.
Sorted by status, showing grade, Alpha, tier, and notes.
"""
import streamlit as st
import pandas as pd

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import load_leaderboard, get_all_user_notes
from app.components.card_front import fmt_money, TIER_COLORS
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — My Board", page_icon="🏈", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

# Page-specific CSS
st.markdown("""
<style>
.board-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.board-card:hover { border-color: #d1d5db; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.status-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
.board-tag {
    display: inline-block;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 10px;
    color: #6b7280;
    margin-right: 4px;
}
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='board')
user = check_auth()
render_user_sidebar()

st.markdown("## My Board")
st.caption("All players you've tagged with Notes & Tags, organized by status.")

_user_email = user.get('email', 'test@nilytics.com')

# Load notes and player data
with st.spinner(""):
    notes = get_all_user_notes(_user_email)

if not notes:
    st.markdown(
        '<div style="text-align:center;padding:48px 24px;background:#f9fafb;border:1px dashed #d1d5db;border-radius:12px;margin:16px 0;">'
        '<div style="font-size:48px;margin-bottom:12px;">📋</div>'
        '<div style="font-size:18px;font-weight:700;color:#1f2937;margin-bottom:8px;">Your board is empty</div>'
        '<div style="font-size:13px;color:#6b7280;max-width:400px;margin:0 auto;">'
        'Visit a Player Card and use <strong style="color:#E8390E;">My Notes & Tags</strong> to start tracking players. '
        'Set their status to Watching, Targeting, In Negotiation, etc.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    render_footer()
    st.stop()

# Load leaderboard to enrich notes with current player data
with st.spinner(""):
    try:
        lb_df = load_leaderboard(2025)
    except Exception:
        lb_df = pd.DataFrame()

# Build enriched board
STATUS_ORDER = ['Targeting', 'In Negotiation', 'Watching', 'Signed', 'Passed', 'Do Not Pursue']
STATUS_COLORS = {
    'watching': '#6B7280', 'targeting': '#3B82F6', 'in negotiation': '#F97316',
    'signed': '#16A34A', 'passed': '#8b949e', 'do not pursue': '#DC2626',
    'in_negotiation': '#F97316', 'do_not_pursue': '#DC2626',
}

# Filter controls
_fc1, _fc2 = st.columns([1, 4])
_status_options = ['All'] + STATUS_ORDER
_filter_status = _fc1.selectbox("Filter Status", _status_options, key="board_status_filter")

# KPI summary
_status_counts = {}
for n in notes:
    s = (n.get('status', 'watching') or 'watching').replace('_', ' ').title()
    _status_counts[s] = _status_counts.get(s, 0) + 1

_kpi_cols = st.columns(min(len(_status_counts) + 1, 7))
_kpi_cols[0].metric("Total Players", len(notes))
for i, (s, c) in enumerate(sorted(_status_counts.items(), key=lambda x: STATUS_ORDER.index(x[0]) if x[0] in STATUS_ORDER else 99)):
    if i + 1 < len(_kpi_cols):
        _sc = STATUS_COLORS.get(s.lower().replace(' ', '_'), '#8b949e')
        _kpi_cols[i + 1].markdown(
            f'<div style="text-align:center;">'
            f'<div style="font-size:11px;color:{_sc};text-transform:uppercase;font-weight:600;">{s}</div>'
            f'<div style="font-size:20px;font-weight:800;color:#1f2937;">{c}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# Group notes by status
_grouped = {}
for n in notes:
    status = (n.get('status', 'watching') or 'watching').replace('_', ' ').title()
    if _filter_status != 'All' and status != _filter_status:
        continue
    if status not in _grouped:
        _grouped[status] = []
    _grouped[status].append(n)

# Render by status group
for status in STATUS_ORDER:
    if status not in _grouped:
        continue
    group = _grouped[status]
    _sc = STATUS_COLORS.get(status.lower().replace(' ', '_'), '#8b949e')

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin:16px 0 8px 0;">'
        f'<span class="status-pill" style="background:{_sc}22;color:{_sc};border:1px solid {_sc};">{status}</span>'
        f'<span style="font-size:12px;color:#6b7280;">{len(group)} player{"s" if len(group) != 1 else ""}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for n in group:
        pid = n.get('player_id')
        note_text = n.get('note', '')
        tags = n.get('tags', []) or []
        updated = n.get('updated_at', '')[:10] if n.get('updated_at') else ''

        # Enrich from leaderboard
        _player_data = {}
        if not lb_df.empty and pid:
            _match = lb_df[lb_df['player_id'] == pid]
            if not _match.empty:
                _player_data = _match.iloc[0].to_dict()

        _name = _player_data.get('name', f'Player #{pid}')
        _pos = _player_data.get('position', '?')
        _school = _player_data.get('school', '?')
        _tier = _player_data.get('tier', '?')
        _grade = float(_player_data.get('core_grade', 0) or 0)
        _output = float(_player_data.get('output_score', 0) or 0)
        _val = int(float(_player_data.get('adjusted_value', 0) or 0))
        _mkt = int(float(_player_data.get('market_value', 0) or 0))
        _alpha = _val - _mkt

        # Grade color
        if _grade >= 90:
            _gc = '#00aa55'
        elif _grade >= 80:
            _gc = '#2196F3'
        elif _grade >= 70:
            _gc = '#FFB300'
        else:
            _gc = '#8b949e'

        # Alpha color
        _ac = '#16A34A' if _alpha > 0 else '#DC2626' if _alpha < -10000 else '#8b949e'
        _alpha_str = f"+{fmt_money(abs(_alpha))}" if _alpha > 0 else f"-{fmt_money(abs(_alpha))}" if _alpha < 0 else "$0"

        # Tag chips
        _tags_html = ''.join(f'<span class="board-tag">{t}</span>' for t in tags)

        # Note preview
        _note_preview = note_text[:120] + '...' if len(note_text) > 120 else note_text

        st.markdown(
            f'<div class="board-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="display:flex;align-items:center;gap:12px;">'
            f'<a href="/player_card?pid={pid}" target="_self" style="text-decoration:none;">'
            f'<span style="font-weight:700;font-size:14px;color:#1f2937;cursor:pointer;">{_name}</span></a>'
            f'<span style="font-size:12px;color:#6b7280;">{_pos} · {_school}</span>'
            f'<span style="font-size:11px;font-weight:700;color:{TIER_COLORS.get(_tier, "#8b949e")};">{_tier}</span>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:16px;font-family:DM Mono,monospace;font-size:12px;">'
            f'<span style="color:{_gc};font-weight:700;">{_grade:.1f}</span>'
            f'<span>{fmt_money(_val)}</span>'
            f'<span>{fmt_money(_mkt)}</span>'
            f'<span style="color:{_ac};font-weight:700;">{_alpha_str}</span>'
            f'</div></div>'
            + (f'<div style="font-size:12px;color:#6b7280;margin-top:6px;font-style:italic;">{_note_preview}</div>' if _note_preview else '')
            + (f'<div style="margin-top:4px;">{_tags_html}</div>' if _tags_html else '')
            + (f'<div style="font-size:10px;color:#9ca3af;margin-top:4px;">Updated {updated}</div>' if updated else '')
            + '</div>',
            unsafe_allow_html=True,
        )

# Handle any ungrouped statuses
for status, group in _grouped.items():
    if status not in STATUS_ORDER:
        _sc = STATUS_COLORS.get(status.lower().replace(' ', '_'), '#8b949e')
        st.markdown(f'<div style="margin:16px 0 8px 0;"><span class="status-pill" style="background:{_sc}22;color:{_sc};">{status}</span></div>', unsafe_allow_html=True)
        for n in group:
            pid = n.get('player_id')
            st.markdown(f'Player #{pid} — {n.get("note", "")[:80]}')

render_footer()
