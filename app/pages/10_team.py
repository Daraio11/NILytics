"""
NILytics — Team / School Roster View
Full roster intelligence from the GM's perspective: every player on the team
(50-80 per school, not just eligible scorers), with filters for projecting
next-season return, graduating SRs, and transfers-out.
"""
import streamlit as st
import pandas as pd
import json

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import (load_leaderboard, load_team_roster,
                       get_team_departures, mark_player_departed, unmark_player_departed,
                       clear_team_departures)
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
.depth-row {
    background: #fafbfc;
    color: #6b7280;
    font-style: italic;
}
.status-pill {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='team')
user = check_auth()
render_user_sidebar()
user_email = user.get('email', 'test@nilytics.com')

# ── Resolve target school (query param OR selectbox) ──
qp = st.query_params
qp_school = qp.get('school', None) if 'school' in qp else None

season = st.session_state.get('team_season', 2025)

# Load the full leaderboard once to derive the school list (fast — already cached)
with st.spinner("Loading season data..."):
    df_lb = load_leaderboard(season)

if df_lb.empty:
    st.info("No data for this season yet.")
    render_footer()
    st.stop()

schools_available = sorted(df_lb['school'].dropna().unique().tolist())

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

# ── Load the FULL roster (all players with any stats, not just eligible) ──
with st.spinner(f"Loading {selected_school} roster..."):
    df = load_team_roster(selected_school, season_sel)

if df.empty:
    st.info(f"No roster data for {selected_school} in {season_sel}.")
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
    f'<div style="margin-left:auto;font-size:12px;color:#d1d5db;">{season_sel} Season · {len(df)} rostered</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Roster Build Mode (Projection Toggle) ──
# Persist manual departures in DB so GMs don't lose their work on refresh.
_dep_cache_key = f'dep_cache_{selected_school}_{season_sel}'
if _dep_cache_key not in st.session_state:
    try:
        st.session_state[_dep_cache_key] = get_team_departures(user_email, selected_school, season_sel)
    except Exception:
        st.session_state[_dep_cache_key] = set()
departures = st.session_state[_dep_cache_key]

_m1, _m2, _m3 = st.columns([2, 2, 2])
with _m1:
    mode = st.radio(
        "Roster Mode",
        ["Full Roster", f"Projected {season_sel + 1} Returners"],
        horizontal=True,
        label_visibility="collapsed",
        key=f"mode_{selected_school}_{season_sel}",
    )
projecting = mode.startswith("Projected")
with _m2:
    if projecting:
        st.caption(
            f"🔮 Projecting **{season_sel + 1}**: hides players with 4+ seasons of stats (likely graduating) "
            "plus any you've marked 🚪 departed."
        )
    else:
        st.caption(f"📋 Showing the full **{season_sel}** roster as-played.")
with _m3:
    _dep_count = len(departures)
    if _dep_count > 0:
        if st.button(f"Restore all {_dep_count} departure{'s' if _dep_count != 1 else ''}",
                     key="clear_departures", use_container_width=True):
            try:
                clear_team_departures(user_email, selected_school, season_sel)
            except Exception:
                pass
            st.session_state[_dep_cache_key] = set()
            st.rerun()

# Apply projection filter: hide manual departures AND anyone with 4+ seasons of stats
def _is_returning(row):
    pid = int(row.get('player_id'))
    if pid in departures:
        return False
    sp = int(row.get('seasons_played', 1) or 1)
    if sp >= 4:
        return False
    return True

if projecting:
    df = df[df.apply(_is_returning, axis=1)].copy()

# Split eligible vs depth for KPI computation (use eligible for value aggregates)
eligible_df = df[df['eligibility_status'] == 'eligible'].copy()

# ── KPI Cards ──
roster_size = len(df)
depth_count = int((df['eligibility_status'] == 'depth').sum())
eligible_count = roster_size - depth_count

avg_grade = eligible_df['core_grade'].dropna().mean() if not eligible_df.empty else 0
total_value = eligible_df['adjusted_value'].dropna().sum() if not eligible_df.empty else 0
total_market = eligible_df['market_value'].dropna().sum() if not eligible_df.empty else 0
total_alpha = eligible_df['opportunity_score'].dropna().sum() if not eligible_df.empty else 0

best_unit = "—"
if not eligible_df.empty and 'position' in eligible_df.columns:
    pos_avg = eligible_df.groupby('position')['core_grade'].mean().dropna().sort_values(ascending=False)
    if not pos_avg.empty:
        best_unit = f"{pos_avg.index[0]} ({pos_avg.iloc[0]:.1f})"

t1_count = int((eligible_df['tier'] == 'T1').sum()) if 'tier' in eligible_df.columns else 0
t2_count = int((eligible_df['tier'] == 'T2').sum()) if 'tier' in eligible_df.columns else 0

_k1, _k2, _k3, _k4, _k5 = st.columns(5)
with _k1:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Total Rostered</div>'
        f'<div class="value">{roster_size}</div>'
        f'<div class="sub">{eligible_count} scored · {depth_count} depth</div></div>',
        unsafe_allow_html=True,
    )
with _k2:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Avg Core Grade</div>'
        f'<div class="value">{avg_grade:.1f}</div>'
        f'<div class="sub">T1: {t1_count} · T2: {t2_count}</div></div>',
        unsafe_allow_html=True,
    )
with _k3:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Total Value</div>'
        f'<div class="value" style="color:#16a34a;">{fmt_money(int(total_value) if pd.notna(total_value) else 0)}</div>'
        f'<div class="sub">Production worth</div></div>',
        unsafe_allow_html=True,
    )
with _k4:
    st.markdown(
        f'<div class="team-kpi"><div class="label">Total Market Cost</div>'
        f'<div class="value" style="color:#dc2626;">{fmt_money(int(total_market) if pd.notna(total_market) else 0)}</div>'
        f'<div class="sub">What NIL pays</div></div>',
        unsafe_allow_html=True,
    )
with _k5:
    _alpha_int = int(total_alpha) if pd.notna(total_alpha) else 0
    _alpha_color = '#16a34a' if _alpha_int > 0 else '#dc2626' if _alpha_int < 0 else '#6b7280'
    _alpha_label = 'Undervalued' if _alpha_int > 0 else 'Overvalued' if _alpha_int < 0 else 'Fair'
    _alpha_sign = '+' if _alpha_int > 0 else ''
    st.markdown(
        f'<div class="team-kpi"><div class="label">Team Alpha</div>'
        f'<div class="value" style="color:{_alpha_color};">{_alpha_sign}{fmt_money(_alpha_int)}</div>'
        f'<div class="sub">{_alpha_label} · Best: {best_unit}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ── Positional Breakdown ──
st.markdown("### Positional Breakdown")

if 'position' in df.columns:
    def _pos_agg(gdf):
        return pd.Series({
            'count': len(gdf),
            'eligible': int((gdf['eligibility_status'] == 'eligible').sum()),
            'avg_grade': gdf['core_grade'].dropna().mean() if gdf['core_grade'].notna().any() else float('nan'),
            'total_val': gdf['adjusted_value'].dropna().sum(),
            'total_alpha': gdf['opportunity_score'].dropna().sum(),
        })

    pos_stats = (df.groupby('position')
                 .apply(_pos_agg, include_groups=False)
                 .reset_index()
                 .sort_values('count', ascending=False))

    pos_cols = st.columns(4)
    for i, (_, r) in enumerate(pos_stats.iterrows()):
        with pos_cols[i % 4]:
            _avg_g = r['avg_grade'] if pd.notna(r['avg_grade']) else 0
            _alpha = r['total_alpha'] if pd.notna(r['total_alpha']) else 0
            _alpha_c = '#16a34a' if _alpha > 0 else '#dc2626' if _alpha < 0 else '#6b7280'
            _alpha_sign = '+' if _alpha > 0 else ''
            _depth_note = f'{int(r["count"]) - int(r["eligible"])} depth' if r["count"] > r["eligible"] else ''
            st.markdown(
                f'<div class="pos-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                f'<span class="pos-label">{r["position"]}</span>'
                f'<span class="pos-count">{int(r["count"])}</span></div>'
                f'<div style="font-size:11px;color:#6b7280;margin-top:4px;">'
                f'Avg Grade <b style="color:#111827;">{_avg_g:.1f}</b>'
                + (f' · <span style="color:#9ca3af;">{_depth_note}</span>' if _depth_note else '')
                + '</div>'
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
    _top_perf = eligible_df.nlargest(5, 'core_grade') if not eligible_df.empty else pd.DataFrame()
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
                f'<div><span style="font-weight:700;color:#111827;">{float(r.get("core_grade", 0) or 0):.1f}</span>'
                f' <span style="background:{_tc};color:#fff;font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;margin-left:6px;">{_tier}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No scored players yet.")

with _tp2:
    st.markdown("### Moneyball Picks")
    st.caption("Most undervalued (positive Alpha) on the roster")
    _under = eligible_df[eligible_df['opportunity_score'].fillna(0) > 0].nlargest(5, 'opportunity_score') if not eligible_df.empty else pd.DataFrame()
    if not _under.empty:
        for _, r in _under.iterrows():
            _alpha = int(float(r.get('opportunity_score', 0) or 0))
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
st.caption(
    f"{roster_size} players total — {eligible_count} have eligibility-scored grades, "
    f"{depth_count} are depth/unscored. Click a name for their full card; click the 🚪 to mark a player as departed."
)

# Filter row
_f1, _f2, _f3, _f4 = st.columns([1.5, 1.5, 1.5, 2])
with _f1:
    pos_options = ['All'] + sorted(df['position'].dropna().unique().tolist())
    _pos_filter = st.selectbox("Position", pos_options, key="team_pos_filter")
with _f2:
    tier_options = ['All', 'T1', 'T2', 'T3', 'T4', 'Unscored']
    _tier_filter = st.selectbox("Tier", tier_options, key="team_tier_filter")
with _f3:
    elig_options = ['All', 'Eligible only', 'Depth only']
    _elig_filter = st.selectbox("Status", elig_options, key="team_elig_filter")
with _f4:
    sort_options = {
        'Snaps (High → Low)': ('snaps', False),
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
if _tier_filter == 'Unscored':
    roster_df = roster_df[roster_df['eligibility_status'] == 'depth']
elif _tier_filter != 'All':
    roster_df = roster_df[roster_df['tier'] == _tier_filter]
if _elig_filter == 'Eligible only':
    roster_df = roster_df[roster_df['eligibility_status'] == 'eligible']
elif _elig_filter == 'Depth only':
    roster_df = roster_df[roster_df['eligibility_status'] == 'depth']

_sort_col, _sort_asc = sort_options[_sort_choice]
if _sort_col in roster_df.columns:
    roster_df = roster_df.sort_values(_sort_col, ascending=_sort_asc, na_position='last')

# Roster table with per-row "mark departed" button.
# Use streamlit columns (not HTML) so we get working buttons.
_hdr = st.columns([0.35, 2.2, 0.6, 0.5, 0.55, 0.6, 0.6, 0.9, 0.8, 0.9, 0.4])
for _c, _label in zip(_hdr, ['', 'Player', 'Pos', 'Tier', 'Snaps', 'Grade', 'Output', 'Value', 'Mkt', 'Alpha', '']):
    _c.markdown(f'<span style="font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">{_label}</span>', unsafe_allow_html=True)

for _, row in roster_df.iterrows():
    pid = int(row['player_id'])
    name = row.get('name', '?')
    pos = row.get('position', '?')
    tier = row.get('tier', '—') or '—'
    snaps = int(row.get('snaps', 0) or 0)
    core = row.get('core_grade')
    output = row.get('output_score')
    av = row.get('adjusted_value')
    mv = row.get('market_value')
    opp = row.get('opportunity_score')
    seasons_played = int(row.get('seasons_played', 1) or 1)
    est_class = row.get('est_class', 'FR')
    is_depth = row.get('eligibility_status') == 'depth'
    is_xfer = row.get('transferred', False)
    is_likely_grad = seasons_played >= 4

    _tc = TIER_COLORS.get(tier, '#9ca3af')

    cols = st.columns([0.35, 2.2, 0.6, 0.5, 0.55, 0.6, 0.6, 0.9, 0.8, 0.9, 0.4])

    # Class hint chip (estimated from seasons_played since class_year is NULL in our data)
    _cy_color = {'FR': '#3b82f6', 'SO': '#10b981', 'JR': '#f59e0b', 'SR': '#ef4444',
                 'GS': '#8b5cf6'}.get(est_class, '#9ca3af')
    _cy_tip = f"{seasons_played} season{'s' if seasons_played != 1 else ''} of stats — estimated {est_class}"
    _cy_chip = (f'<span title="{_cy_tip}" style="background:{_cy_color}22;color:{_cy_color};font-size:9px;'
                f'font-weight:700;padding:1px 5px;border-radius:3px;margin-left:4px;cursor:help;">'
                f'~{est_class}</span>')
    _xfer_chip = ('<span title="Transferred in this season" style="cursor:help;font-size:10px;margin-left:4px;">🔁</span>'
                  if is_xfer else '')
    _depth_chip = ('<span style="background:#f3f4f6;color:#6b7280;font-size:9px;font-weight:700;'
                   'padding:1px 4px;border-radius:3px;margin-left:4px;">DEPTH</span>'
                   if is_depth else '')
    _grad_chip = ('<span title="4+ seasons of stats — likely graduating" '
                  'style="background:#fef3c7;color:#92400e;font-size:9px;font-weight:700;'
                  'padding:1px 4px;border-radius:3px;margin-left:4px;cursor:help;">⏰ LIKELY GRAD</span>'
                  if is_likely_grad else '')

    cols[0].markdown(f'<span style="font-size:14px;">{"🎯" if is_depth else ""}</span>', unsafe_allow_html=True)
    cols[1].markdown(
        f'<a href="/player_card?pid={pid}" target="_self" '
        f'style="color:#1f2937;font-weight:600;text-decoration:none;font-size:13px;">{name}</a>'
        + _cy_chip + _xfer_chip + _depth_chip + _grad_chip,
        unsafe_allow_html=True,
    )
    cols[2].markdown(f'<span style="font-size:12px;color:#6b7280;">{pos}</span>', unsafe_allow_html=True)
    cols[3].markdown(
        f'<span style="background:{_tc};color:#fff;font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;">{tier}</span>'
        if tier != '—' else '<span style="color:#d1d5db;font-size:12px;">—</span>',
        unsafe_allow_html=True,
    )
    cols[4].markdown(f'<span style="font-size:12px;color:#6b7280;">{snaps:,}</span>', unsafe_allow_html=True)
    cols[5].markdown(
        f'<span style="font-weight:700;font-size:13px;">{float(core):.1f}</span>' if pd.notna(core)
        else '<span style="color:#d1d5db;font-size:12px;">—</span>',
        unsafe_allow_html=True,
    )
    cols[6].markdown(
        f'<span style="font-size:12px;">{float(output):.1f}</span>' if pd.notna(output)
        else '<span style="color:#d1d5db;font-size:12px;">—</span>',
        unsafe_allow_html=True,
    )
    cols[7].markdown(
        f'<span style="font-size:12px;color:#16a34a;">{fmt_money(av)}</span>' if pd.notna(av)
        else '<span style="color:#d1d5db;font-size:12px;">—</span>',
        unsafe_allow_html=True,
    )
    cols[8].markdown(
        f'<span style="font-size:12px;color:#6b7280;">{fmt_money(mv)}</span>' if pd.notna(mv)
        else '<span style="color:#d1d5db;font-size:12px;">—</span>',
        unsafe_allow_html=True,
    )
    if pd.notna(opp):
        _opp_int = int(float(opp))
        _opp_color = '#16a34a' if _opp_int > 0 else '#dc2626' if _opp_int < 0 else '#6b7280'
        _opp_sign = '+' if _opp_int > 0 else ('-' if _opp_int < 0 else '')
        cols[9].markdown(
            f'<span style="font-weight:700;font-size:12px;color:{_opp_color};">{_opp_sign}{fmt_money(abs(_opp_int))}</span>',
            unsafe_allow_html=True,
        )
    else:
        cols[9].markdown('<span style="color:#d1d5db;font-size:12px;">—</span>', unsafe_allow_html=True)

    # Mark-as-departed toggle — persists to DB
    is_departed = pid in departures
    if cols[10].button('🚪' if not is_departed else '↩️', key=f'dep_{pid}',
                       help='Mark departed (graduated / transfer out / etc.) — saved across sessions'
                       if not is_departed
                       else 'Restore this player to your projection'):
        try:
            if is_departed:
                unmark_player_departed(user_email, selected_school, season_sel, pid)
                departures.discard(pid)
            else:
                mark_player_departed(user_email, selected_school, season_sel, pid)
                departures.add(pid)
            st.session_state[_dep_cache_key] = departures
        except Exception:
            pass
        st.rerun()

render_footer()
