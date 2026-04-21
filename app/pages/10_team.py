"""
NILytics — Team / School Roster View
Aggregated roster intelligence for a single school: KPIs, positional
breakdown, full roster with sort/filter, and top performers.
"""
import streamlit as st
import pandas as pd
import json

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import load_leaderboard
from app.components.card_front import fmt_money, TIER_COLORS
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Team", page_icon="🏈", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

# Page-specific CSS
st.markdown("""
<style>
.team-kpi {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: left;
}
.team-kpi .label {
    font-size: 10px;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.team-kpi .value {
    font-size: 26px;
    font-weight: 800;
    color: #1f2937;
    line-height: 1.1;
}
.team-kpi .sub {
    font-size: 11px;
    color: #9ca3af;
    margin-top: 2px;
}
.pos-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.pos-card .pos-label {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.pos-card .pos-count {
    font-size: 18px;
    font-weight: 800;
    color: #111827;
}
.roster-row {
    padding: 6px 10px;
    border-bottom: 1px solid #f3f4f6;
    font-size: 13px;
}
.roster-row:hover { background: #fafafa; }
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='team')
user = check_auth()
render_user_sidebar()

# ── Resolve target school (query param OR selectbox) ──
qp = st.query_params
qp_school = qp.get('school', None) if 'school' in qp else None

season = st.session_state.get('team_season', 2025)

# Load full leaderboard for the season so we can derive the school list + stats
with st.spinner("Loading season data..."):
    df_all = load_leaderboard(season)

if df_all.empty:
    st.info("No data for this season yet.")
    render_footer()
    st.stop()

schools_available = sorted(df_all['school'].dropna().unique().tolist())

# Default school: query param > session > first SEC alphabetically
default_school = qp_school or st.session_state.get('team_school', None)
if default_school not in schools_available:
    default_school = schools_available[0] if schools_available else None

# ── Header row: School picker + season selector ──
_h1, _h2, _h3 = st.columns([3, 1, 1])
with _h1:
    selected_school = st.selectbox(
        "School", schools_available,
        index=schools_available.index(default_school) if default_school in schools_available else 0,
        key="team_school_select",
    )
    st.session_state['team_school'] = selected_school
    if qp_school and qp_school != selected_school:
        st.query_params.clear()
with _h2:
    season_sel = st.selectbox("Season", [2025, 2024, 2023], key="team_season_select")
    if season_sel != season:
        st.session_state['team_season'] = season_sel
        st.rerun()
with _h3:
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("← Leaderboard", use_container_width=True, key="team_back_lb"):
        st.switch_page("pages/01_leaderboard.py")

# ── Filter dataset to this school ──
df = df_all[df_all['school'] == selected_school].copy()

if df.empty:
    st.info(f"No eligible players for {selected_school} in {season_sel}.")
    render_footer()
    st.stop()

conference = df['conference'].dropna().iloc[0] if 'conference' in df.columns and not df['conference'].dropna().empty else '—'
market = df['market'].dropna().iloc[0] if 'market' in df.columns and not df['market'].dropna().empty else '—'

# ── Team header banner ──
st.markdown(
    f'<div style="padding:14px 18px;background:#111827;color:#ffffff;border-radius:12px;'
    f'margin:8px 0 16px 0;display:flex;align-items:center;gap:16px;">'
    f'<div style="font-size:24px;font-weight:800;letter-spacing:0.02em;">{selected_school}</div>'
    f'<div style="font-size:12px;background:rgba(255,255,255,0.12);color:#ffffff;'
    f'padding:3px 10px;border-radius:999px;font-weight:700;letter-spacing:0.06em;">{conference} · {market}</div>'
    f'<div style="margin-left:auto;font-size:12px;color:#d1d5db;">{season_sel} Season</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI Cards ──
roster_size = len(df)
avg_grade = df['core_grade'].fillna(0).mean() if 'core_grade' in df.columns else 0
total_value = df['adjusted_value'].fillna(0).sum() if 'adjusted_value' in df.columns else 0
total_market = df['market_value'].fillna(0).sum() if 'market_value' in df.columns else 0
total_alpha = df['opportunity_score'].fillna(0).sum() if 'opportunity_score' in df.columns else 0

# Top position identified for "Best Unit"
best_unit = "—"
if not df.empty and 'core_grade' in df.columns and 'position' in df.columns:
    pos_avg = df.groupby('position')['core_grade'].mean().sort_values(ascending=False)
    if not pos_avg.empty:
        best_unit = f"{pos_avg.index[0]} ({pos_avg.iloc[0]:.1f})"

# Tier counts
t1_count = len(df[df['tier'] == 'T1']) if 'tier' in df.columns else 0
t2_count = len(df[df['tier'] == 'T2']) if 'tier' in df.columns else 0

_k1, _k2, _k3, _k4, _k5 = st.columns(5)
with _k1:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Eligible Roster</div>'
        f'<div class="value">{roster_size}</div>'
        f'<div class="sub">T1: {t1_count} · T2: {t2_count}</div></div>',
        unsafe_allow_html=True,
    )
with _k2:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Avg Core Grade</div>'
        f'<div class="value">{avg_grade:.1f}</div>'
        f'<div class="sub">Team-wide PFF composite</div></div>',
        unsafe_allow_html=True,
    )
with _k3:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Total Value</div>'
        f'<div class="value" style="color:#16a34a;">{fmt_money(int(total_value))}</div>'
        f'<div class="sub">Production worth</div></div>',
        unsafe_allow_html=True,
    )
with _k4:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Total Market Cost</div>'
        f'<div class="value" style="color:#dc2626;">{fmt_money(int(total_market))}</div>'
        f'<div class="sub">What NIL pays</div></div>',
        unsafe_allow_html=True,
    )
with _k5:
    _alpha_color = '#16a34a' if total_alpha > 0 else '#dc2626' if total_alpha < 0 else '#6b7280'
    _alpha_label = 'Undervalued' if total_alpha > 0 else 'Overvalued' if total_alpha < 0 else 'Fair'
    _alpha_sign = '+' if total_alpha > 0 else ''
    st.markdown(
        f'<div class="team-kpi"><div class="label">Team Alpha</div>'
        f'<div class="value" style="color:{_alpha_color};">{_alpha_sign}{fmt_money(int(total_alpha))}</div>'
        f'<div class="sub">{_alpha_label} · Best: {best_unit}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ── Positional Breakdown ──
st.markdown("### Positional Breakdown")

# Group by position
if 'position' in df.columns:
    pos_stats = (
        df.groupby('position')
        .agg(
            count=('player_id', 'count'),
            avg_grade=('core_grade', 'mean'),
            total_val=('adjusted_value', 'sum'),
            total_mkt=('market_value', 'sum'),
            total_alpha=('opportunity_score', 'sum'),
        )
        .reset_index()
        .sort_values('avg_grade', ascending=False)
    )
    pos_stats['avg_grade'] = pos_stats['avg_grade'].fillna(0)

    # Render pos cards in a responsive grid: 4 per row
    pos_cols = st.columns(4)
    for i, (_, r) in enumerate(pos_stats.iterrows()):
        with pos_cols[i % 4]:
            _avg_g = r['avg_grade']
            _alpha = r['total_alpha'] or 0
            _alpha_c = '#16a34a' if _alpha > 0 else '#dc2626' if _alpha < 0 else '#6b7280'
            _alpha_sign = '+' if _alpha > 0 else ''
            st.markdown(
                f'<div class="pos-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                f'<span class="pos-label">{r["position"]}</span>'
                f'<span class="pos-count">{int(r["count"])}</span></div>'
                f'<div style="font-size:11px;color:#6b7280;margin-top:4px;">'
                f'Avg Grade <b style="color:#111827;">{_avg_g:.1f}</b></div>'
                f'<div style="font-size:11px;color:{_alpha_c};margin-top:2px;">'
                f'Alpha <b>{_alpha_sign}{fmt_money(int(_alpha))}</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if (i + 1) % 4 == 0 and i + 1 < len(pos_stats):
            pos_cols = st.columns(4)

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ── Top Performers + Hidden Gems side by side ──
_tp1, _tp2 = st.columns(2)

with _tp1:
    st.markdown("### Top Performers")
    st.caption("Highest Core Grade on the roster")
    _top_perf = df.nlargest(5, 'core_grade') if 'core_grade' in df.columns else pd.DataFrame()
    if not _top_perf.empty:
        for _, r in _top_perf.iterrows():
            _tier = r.get('tier', 'T4')
            _tc = TIER_COLORS.get(_tier, '#6b7280')
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:8px 12px;background:#ffffff;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:6px;">'
                f'<div><a href="/player_card?pid={int(r["player_id"])}" target="_self" '
                f'style="color:#1f2937;font-weight:700;font-size:13px;text-decoration:none;">{r["name"]}</a>'
                f' <span style="color:#6b7280;font-size:12px;">{r.get("position", "?")}</span></div>'
                f'<div><span style="font-weight:700;color:#111827;">{float(r.get("core_grade", 0)):.1f}</span>'
                f' <span style="background:{_tc};color:#fff;font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;margin-left:6px;">{_tier}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No grades available.")

with _tp2:
    st.markdown("### Moneyball Picks")
    st.caption("Most undervalued (positive Alpha) on the roster")
    _under = df[df['opportunity_score'].fillna(0) > 0].nlargest(5, 'opportunity_score') if 'opportunity_score' in df.columns else pd.DataFrame()
    if not _under.empty:
        for _, r in _under.iterrows():
            _alpha = int(float(r.get('opportunity_score', 0)))
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:8px 12px;background:#ffffff;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:6px;">'
                f'<div><a href="/player_card?pid={int(r["player_id"])}" target="_self" '
                f'style="color:#1f2937;font-weight:700;font-size:13px;text-decoration:none;">{r["name"]}</a>'
                f' <span style="color:#6b7280;font-size:12px;">{r.get("position", "?")}</span></div>'
                f'<div style="font-weight:700;color:#16a34a;">+{fmt_money(_alpha)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No undervalued players identified.")

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── Full Roster Table ──
st.markdown("### Full Roster")
st.caption(f"All {roster_size} eligible {selected_school} players — click a name for the full card")

# Filter row
_f1, _f2, _f3 = st.columns([2, 2, 2])
with _f1:
    pos_options = ['All'] + sorted(df['position'].dropna().unique().tolist())
    _pos_filter = st.selectbox("Position", pos_options, key="team_pos_filter")
with _f2:
    tier_options = ['All', 'T1', 'T2', 'T3', 'T4']
    _tier_filter = st.selectbox("Tier", tier_options, key="team_tier_filter")
with _f3:
    sort_options = {
        'Core Grade (High → Low)': ('core_grade', False),
        'Output (High → Low)': ('output_score', False),
        'Alpha (Best → Worst)': ('opportunity_score', False),
        'Alpha (Worst → Best)': ('opportunity_score', True),
        'Value (High → Low)': ('adjusted_value', False),
        'Market (High → Low)': ('market_value', False),
    }
    _sort_choice = st.selectbox("Sort by", list(sort_options.keys()), key="team_sort")

roster_df = df.copy()
if _pos_filter != 'All':
    roster_df = roster_df[roster_df['position'] == _pos_filter]
if _tier_filter != 'All':
    roster_df = roster_df[roster_df['tier'] == _tier_filter]

_sort_col, _sort_asc = sort_options[_sort_choice]
if _sort_col in roster_df.columns:
    roster_df = roster_df.sort_values(_sort_col, ascending=_sort_asc, na_position='last')

# Build table HTML
rows_html = []
for _, row in roster_df.iterrows():
    pid = int(row['player_id'])
    name = row.get('name', '?')
    pos = row.get('position', '?')
    tier = row.get('tier', 'T4')
    _tc = TIER_COLORS.get(tier, '#6b7280')
    core = float(row.get('core_grade', 0)) if pd.notna(row.get('core_grade')) else 0
    out = float(row.get('output_score', 0)) if pd.notna(row.get('output_score')) else 0
    av = row.get('adjusted_value', 0)
    mv = row.get('market_value', 0)
    opp = row.get('opportunity_score', 0)

    try:
        opp_val = int(float(opp)) if pd.notna(opp) else 0
    except (ValueError, TypeError):
        opp_val = 0
    if opp_val > 0:
        alpha_html = f'<span style="color:#16a34a;font-weight:700;">+{fmt_money(abs(opp_val))}</span>'
    elif opp_val < 0:
        alpha_html = f'<span style="color:#dc2626;font-weight:700;">-{fmt_money(abs(opp_val))}</span>'
    else:
        alpha_html = '<span style="color:#6b7280;">$0</span>'

    # Flags
    flags_raw = row.get('flags', '[]')
    try:
        flag_list = json.loads(flags_raw) if isinstance(flags_raw, str) else (flags_raw if isinstance(flags_raw, list) else [])
    except (json.JSONDecodeError, TypeError):
        flag_list = []
    FLAG_ICON = {'BREAKOUT_CANDIDATE': '🚀', 'HIDDEN_GEM': '💎', 'REGRESSION_RISK': '📉',
                 'PORTAL_VALUE': '🔄', 'EXPERIENCE_PREMIUM': '🎖️'}
    flag_icons = ''.join(FLAG_ICON.get(f, '') for f in flag_list)

    rows_html.append(
        f'<tr style="border-bottom:1px solid #f3f4f6;">'
        f'<td style="padding:8px 10px;"><a href="/player_card?pid={pid}" target="_self" '
        f'style="color:#1f2937;font-weight:600;text-decoration:none;">{name}</a></td>'
        f'<td style="padding:8px 10px;font-size:12px;color:#6b7280;">{pos}</td>'
        f'<td style="padding:8px 10px;"><span style="background:{_tc};color:#fff;font-size:10px;'
        f'font-weight:700;padding:2px 6px;border-radius:3px;">{tier}</span></td>'
        f'<td style="padding:8px 10px;text-align:right;font-weight:700;">{core:.1f}</td>'
        f'<td style="padding:8px 10px;text-align:right;">{out:.1f}</td>'
        f'<td style="padding:8px 10px;text-align:right;font-size:12px;color:#16a34a;">{fmt_money(av)}</td>'
        f'<td style="padding:8px 10px;text-align:right;font-size:12px;color:#6b7280;">{fmt_money(mv)}</td>'
        f'<td style="padding:8px 10px;text-align:right;">{alpha_html}</td>'
        f'<td style="padding:8px 10px;text-align:center;font-size:14px;">{flag_icons}</td>'
        f'</tr>'
    )

table_html = (
    '<table style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
    '<thead>'
    '<tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;">'
    '<th style="padding:10px;text-align:left;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Player</th>'
    '<th style="padding:10px;text-align:left;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Pos</th>'
    '<th style="padding:10px;text-align:left;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Tier</th>'
    '<th style="padding:10px;text-align:right;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Grade</th>'
    '<th style="padding:10px;text-align:right;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Output</th>'
    '<th style="padding:10px;text-align:right;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Value</th>'
    '<th style="padding:10px;text-align:right;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Mkt</th>'
    '<th style="padding:10px;text-align:right;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Alpha</th>'
    '<th style="padding:10px;text-align:center;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Flags</th>'
    '</tr></thead><tbody>' + ''.join(rows_html) + '</tbody></table>'
)
st.markdown(table_html, unsafe_allow_html=True)

render_footer()
