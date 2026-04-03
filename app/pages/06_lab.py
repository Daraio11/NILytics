"""
NILytics — Valuation Lab
Custom weight adjustment system. Lets users redefine what matters for each position,
then recomputes the full scoring pipeline in-memory to see how valuations change.
"""
import streamlit as st
import pandas as pd
import json

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scoring.core_grade import DEFAULT_WEIGHTS, WEIGHT_LABELS
from scoring.custom_recompute import recompute_position
from app.data import load_leaderboard, load_all_position_stats_for_season
from app.components.card_front import fmt_money
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Valuation Lab", page_icon="🧪", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

# Page-specific CSS
st.markdown("""
<style>
/* Slider styling */
.stSlider > div > div > div > div {
    background: #E8390E !important;
}
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {
    font-size: 11px !important;
}

/* Weight category card */
.weight-category {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.weight-label {
    font-size: 13px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 2px;
}
.weight-default {
    font-size: 11px;
    color: #6b7280;
}

/* Comparison table */
.lab-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }

/* Tier change badges */
.tier-up { color: #16a34a; font-weight: 700; }
.tier-down { color: #dc2626; font-weight: 700; }
.tier-same { color: #6b7280; }

/* Delta values */
.delta-pos { color: #16a34a; font-weight: 700; }
.delta-neg { color: #dc2626; font-weight: 700; }
.delta-zero { color: #6b7280; }

/* Section headers */
.lab-section {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-bottom: 2px solid #E8390E;
    padding-bottom: 6px;
    margin-bottom: 12px;
    color: #6b7280;
}

/* Reduce whitespace */
hr { margin: 0.4rem 0 !important; }
.stButton > button { min-height: 0 !important; }

/* Weight total indicator */
.weight-total {
    font-size: 18px;
    font-weight: 800;
    font-family: 'DM Mono', monospace;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
}
.weight-ok { background: rgba(63,185,80,0.10); color: #16a34a; }
.weight-bad { background: rgba(248,81,73,0.10); color: #dc2626; }

/* Mono class */
.mono { font-family: 'DM Mono', 'SF Mono', 'Fira Code', monospace; }

/* Sort arrows */
.sort-arrows { font-size: 8px; color: #6b7280; margin-left: 4px; letter-spacing: -1px; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='lab')

user = check_auth()
render_user_sidebar()

# ── Header ──
st.markdown("""
<div style="margin-bottom:8px;">
    <span style="font-size:24px;font-weight:800;color:#1f2937;">Valuation Lab</span>
    <span style="font-size:13px;color:#6b7280;margin-left:12px;">Adjust what matters. See how values change.</span>
</div>
""", unsafe_allow_html=True)

st.caption("Redefine the weight categories for any position's Core Grade, then see how every player's "
           "value changes in real-time. Same frozen tier cutoffs. Same value ranges. Different priorities.")

# ── Controls Row ──
ctrl1, ctrl2 = st.columns([1, 1])
with ctrl1:
    positions = list(DEFAULT_WEIGHTS.keys())
    selected_pos = st.selectbox("Position", positions, index=positions.index('WR'), key="lab_pos")
with ctrl2:
    season = st.selectbox("Season", list(range(2025, 2017, -1)), index=0, key="lab_season")

st.markdown("---")

# ── Weight Sliders ──
defaults = DEFAULT_WEIGHTS[selected_pos]
labels = WEIGHT_LABELS[selected_pos]
categories = list(defaults.keys())

st.markdown(f'<p class="lab-section">Core Grade Weights — {selected_pos}</p>', unsafe_allow_html=True)

# Initialize session state for weights if needed
state_key = f"lab_weights_{selected_pos}"
if state_key not in st.session_state:
    st.session_state[state_key] = {k: int(v * 100) for k, v in defaults.items()}

# Render sliders
weights_pct = {}
slider_cols = st.columns(min(len(categories), 4))
for i, cat in enumerate(categories):
    default_pct = int(defaults[cat] * 100)
    current = st.session_state[state_key].get(cat, default_pct)
    with slider_cols[i % len(slider_cols)]:
        st.markdown(
            f'<div class="weight-category">'
            f'<div class="weight-label">{labels[cat]}</div>'
            f'<div class="weight-default">Default: {default_pct}%</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        val = st.slider(
            labels[cat],
            min_value=0, max_value=100,
            value=current,
            step=5,
            key=f"slider_{selected_pos}_{cat}",
            label_visibility="collapsed",
        )
        weights_pct[cat] = val
        st.session_state[state_key][cat] = val

# Total indicator
total_pct = sum(weights_pct.values())
total_class = "weight-ok" if total_pct == 100 else "weight-bad"
total_icon = "✓" if total_pct == 100 else "✗"

tcol1, tcol2, tcol3 = st.columns([2, 1, 2])
with tcol2:
    st.markdown(
        f'<div class="weight-total {total_class}">{total_icon} {total_pct}%</div>',
        unsafe_allow_html=True,
    )

# Reset button
bcol1, bcol2, bcol3 = st.columns([2, 1, 2])
with bcol2:
    if st.button("Reset to Defaults", use_container_width=True, key="reset_weights"):
        st.session_state[state_key] = {k: int(v * 100) for k, v in defaults.items()}
        st.rerun()

if total_pct != 100:
    st.warning(f"Weights must sum to 100% (currently {total_pct}%). Adjust sliders before running.")
    render_footer()
    st.stop()

st.markdown("---")

# ── Recalculate Button ──
custom_weights = {k: v / 100.0 for k, v in weights_pct.items()}
is_default = all(abs(custom_weights[k] - defaults[k]) < 0.001 for k in categories)

if is_default:
    st.info("Weights match the defaults. Adjust the sliders above to see how different priorities change valuations.")

run_btn = st.button(
    "Recalculate Valuations" if not is_default else "Run with Default Weights",
    type="primary",
    use_container_width=True,
    key="run_lab",
)

if run_btn:
    with st.spinner(""):
        # Load leaderboard for original values
        leaderboard = load_leaderboard(season)
        if leaderboard.empty:
            st.error(f"No leaderboard data for {season}.")
            st.stop()

        # Filter to selected position
        pos_df = leaderboard[leaderboard['position'] == selected_pos].copy()
        if pos_df.empty:
            st.error(f"No {selected_pos} players found for {season}.")
            st.stop()

        # Load raw stats for this position
        raw_stats = load_all_position_stats_for_season(selected_pos, season)

        # Build player_stats list for recomputation
        player_stats = []
        for _, row in pos_df.iterrows():
            pid = row['player_id']
            stats_dict = raw_stats.get(pid, {
                'passing': None, 'receiving': None, 'rushing': None,
                'blocking': None, 'defense': None,
            })

            player_stats.append({
                'player_id': pid,
                'name': row.get('name', '?'),
                'school': row.get('school', '?'),
                'market': row.get('market', 'P4'),
                'conference': row.get('conference', ''),
                'position': selected_pos,
                'passing': stats_dict.get('passing'),
                'receiving': stats_dict.get('receiving'),
                'rushing': stats_dict.get('rushing'),
                'blocking': stats_dict.get('blocking'),
                'defense': stats_dict.get('defense'),
                'original_core_grade': float(row.get('core_grade', 0)) if pd.notna(row.get('core_grade')) else 0,
                'original_output_score': float(row.get('output_score', 0)) if pd.notna(row.get('output_score')) else 0,
                'original_tier': row.get('tier', 'T4'),
                'original_adjusted_value': float(row.get('adjusted_value', 0)) if pd.notna(row.get('adjusted_value')) else 0,
                'original_market_value': float(row.get('market_value', 0)) if pd.notna(row.get('market_value')) else 0,
            })

        # Run recomputation
        results = recompute_position(
            position=selected_pos,
            custom_weights=custom_weights,
            player_stats=player_stats,
            season=season,
        )

    if not results:
        st.warning("No players could be graded with the available stats.")
        render_footer()
        st.stop()

    # Store results in session state for display
    st.session_state['lab_results'] = results
    st.session_state['lab_results_pos'] = selected_pos
    st.session_state['lab_is_default'] = is_default

# ── Display Results ──
if 'lab_results' in st.session_state and st.session_state.get('lab_results_pos') == selected_pos:
    results = st.session_state['lab_results']
    is_default = st.session_state.get('lab_is_default', True)

    results_df = pd.DataFrame(results)

    # ── Summary KPIs ──
    n_players = len(results_df)
    tier_ups = len(results_df[results_df['tier_change'] == 'UP'])
    tier_downs = len(results_df[results_df['tier_change'] == 'DOWN'])
    avg_grade_delta = results_df['grade_delta'].mean()
    avg_value_delta = results_df['value_delta'].mean()

    # Biggest movers
    biggest_gainer = results_df.loc[results_df['value_delta'].idxmax()] if not results_df.empty else None
    biggest_loser = results_df.loc[results_df['value_delta'].idxmin()] if not results_df.empty else None

    st.markdown("---")
    st.markdown(f'<p class="lab-section">Results — {selected_pos} ({n_players} players)</p>',
                unsafe_allow_html=True)

    # KPI row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Players Scored", n_players)
    with k2:
        st.metric("Tier Upgrades", f"{tier_ups}", delta=f"{tier_ups} moved up" if tier_ups > 0 else None)
    with k3:
        st.metric("Tier Downgrades", f"{tier_downs}", delta=f"{tier_downs} moved down" if tier_downs > 0 else None,
                  delta_color="inverse")
    with k4:
        delta_prefix = "+" if avg_grade_delta > 0 else ""
        st.metric("Avg Grade Delta", f"{delta_prefix}{avg_grade_delta:.1f}")
    with k5:
        st.metric("Avg Value Delta", fmt_money(avg_value_delta))

    # Biggest movers callout
    if biggest_gainer is not None and biggest_gainer['value_delta'] > 10000:
        st.markdown(
            f'<div style="border:2px solid #16a34a;background:rgba(63,185,80,0.08);border-radius:8px;'
            f'padding:10px 16px;margin:8px 0;">'
            f'<span style="color:#16a34a;font-weight:700;">Biggest Winner:</span> '
            f'<span style="font-weight:600;">{biggest_gainer["name"]}</span> '
            f'({biggest_gainer.get("school","?")})'
            f' — Value {fmt_money(biggest_gainer["original_adjusted_value"])} → '
            f'{fmt_money(biggest_gainer["custom_adjusted_value"])} '
            f'<span style="color:#16a34a;font-weight:700;">(+{fmt_money(biggest_gainer["value_delta"])})</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if biggest_loser is not None and biggest_loser['value_delta'] < -10000:
        st.markdown(
            f'<div style="border:2px solid #dc2626;background:rgba(248,81,73,0.08);border-radius:8px;'
            f'padding:10px 16px;margin:8px 0;">'
            f'<span style="color:#dc2626;font-weight:700;">Biggest Loser:</span> '
            f'<span style="font-weight:600;">{biggest_loser["name"]}</span> '
            f'({biggest_loser.get("school","?")})'
            f' — Value {fmt_money(biggest_loser["original_adjusted_value"])} → '
            f'{fmt_money(biggest_loser["custom_adjusted_value"])} '
            f'<span style="color:#dc2626;font-weight:700;">({fmt_money(biggest_loser["value_delta"])})</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Sort options ──
    sort_options = {
        "Value Delta (biggest gains first)": ('value_delta', False),
        "Value Delta (biggest drops first)": ('value_delta', True),
        "Custom Value (highest first)": ('custom_adjusted_value', False),
        "Original Value (highest first)": ('original_adjusted_value', False),
        "Grade Delta": ('grade_delta', False),
        "Custom Core Grade": ('custom_core_grade', False),
    }
    sort_choice = st.selectbox("Sort by", list(sort_options.keys()), key="lab_sort")
    sort_col, sort_asc = sort_options[sort_choice]
    results_df = results_df.sort_values(sort_col, ascending=sort_asc).reset_index(drop=True)

    # ── Filter: show only tier changes ──
    show_tier_changes = st.checkbox("Show only players with tier changes", key="lab_tier_filter")
    if show_tier_changes:
        results_df = results_df[results_df['tier_change'] != 'SAME']
        if results_df.empty:
            st.info("No players changed tiers with these weights.")
            render_footer()
            st.stop()

    # ── Build comparison table ──
    TIER_COLORS = {'T1': '#E63B2E', 'T2': '#E8712B', 'T3': '#666', 'T4': '#bbb'}
    arrows = '<span class="sort-arrows">▲▼</span>'

    rows_html = []
    for rank, (_, r) in enumerate(results_df.iterrows(), 1):
        name = r.get('name', '?')
        school = r.get('school', '?')
        market = r.get('market', 'P4')

        # Original values
        orig_grade = r.get('original_core_grade', 0)
        orig_output = r.get('original_output_score', 0)
        orig_tier = r.get('original_tier', 'T4')
        orig_value = r.get('original_adjusted_value', 0)

        # Custom values
        cust_grade = r.get('custom_core_grade', 0)
        cust_output = r.get('custom_output_score', 0)
        cust_tier = r.get('custom_tier', 'T4')
        cust_value = r.get('custom_adjusted_value', 0)

        # Deltas
        grade_d = r.get('grade_delta', 0)
        value_d = r.get('value_delta', 0)
        tier_ch = r.get('tier_change', 'SAME')

        # Grade delta color
        if grade_d > 1:
            gd_html = f'<span class="delta-pos">+{grade_d:.1f}</span>'
        elif grade_d < -1:
            gd_html = f'<span class="delta-neg">{grade_d:.1f}</span>'
        else:
            gd_html = f'<span class="delta-zero">{grade_d:+.1f}</span>'

        # Value delta
        if value_d > 10000:
            vd_html = f'<span class="delta-pos">+{fmt_money(abs(value_d))}</span>'
        elif value_d < -10000:
            vd_html = f'<span class="delta-neg">-{fmt_money(abs(value_d))}</span>'
        else:
            vd_html = f'<span class="delta-zero">{fmt_money(value_d)}</span>'

        # Tier change
        orig_tc = TIER_COLORS.get(orig_tier, '#bbb')
        cust_tc = TIER_COLORS.get(cust_tier, '#bbb')
        if tier_ch == 'UP':
            tier_html = (f'<span style="color:{orig_tc};font-weight:700;">{orig_tier}</span>'
                        f' → <span style="color:{cust_tc};font-weight:700;">{cust_tier}</span>'
                        f' <span class="tier-up">▲</span>')
        elif tier_ch == 'DOWN':
            tier_html = (f'<span style="color:{orig_tc};font-weight:700;">{orig_tier}</span>'
                        f' → <span style="color:{cust_tc};font-weight:700;">{cust_tier}</span>'
                        f' <span class="tier-down">▼</span>')
        else:
            tier_html = f'<span style="color:{orig_tc};font-weight:700;">{orig_tier}</span>'

        # Grade color
        def _gc(g):
            if g >= 90: return '#00aa55'
            elif g >= 80: return '#2196F3'
            elif g >= 70: return '#FFB300'
            elif g >= 60: return '#E8712B'
            else: return '#E63B2E'

        rows_html.append(
            f'<tr>'
            f'<td style="text-align:left;">{rank}</td>'
            f'<td style="text-align:left;font-weight:600;font-size:12px;">{name}</td>'
            f'<td style="text-align:left;font-size:10px;color:#6b7280;text-transform:uppercase;">{school}</td>'
            f'<td style="text-align:left;font-size:11px;color:#6b7280;">{market}</td>'
            f'<td style="text-align:center;"><span class="mono" style="color:{_gc(orig_grade)};font-weight:800;font-size:12px;">{orig_grade:.1f}</span></td>'
            f'<td style="text-align:center;"><span class="mono" style="color:{_gc(cust_grade)};font-weight:800;font-size:12px;">{cust_grade:.1f}</span></td>'
            f'<td style="text-align:center;">{gd_html}</td>'
            f'<td style="text-align:center;">{tier_html}</td>'
            f'<td style="text-align:right;font-family:DM Mono,monospace;font-size:12px;">{fmt_money(orig_value)}</td>'
            f'<td style="text-align:right;font-family:DM Mono,monospace;font-size:12px;">{fmt_money(cust_value)}</td>'
            f'<td style="text-align:right;">{vd_html}</td>'
            f'</tr>'
        )

    table_html = (
        '<div class="lab-table-wrap">'
        '<table class="pff-table" style="table-layout:fixed;width:100%;">'
        '<colgroup>'
        '<col style="width:30px;">'    # #
        '<col style="width:14%;">'     # Player
        '<col style="width:10%;">'     # School
        '<col style="width:40px;">'    # Market
        '<col style="width:65px;">'    # Orig Grade
        '<col style="width:65px;">'    # Custom Grade
        '<col style="width:55px;">'    # Grade Δ
        '<col style="width:100px;">'   # Tier
        '<col style="width:72px;">'    # Orig Value
        '<col style="width:72px;">'    # Custom Value
        '<col style="width:76px;">'    # Value Δ
        '</colgroup>'
        '<thead><tr>'
        f'<th>#</th>'
        f'<th>Player {arrows}</th>'
        f'<th>School</th>'
        f'<th>Mkt</th>'
        f'<th style="text-align:center;">Orig Grade</th>'
        f'<th style="text-align:center;">New Grade</th>'
        f'<th style="text-align:center;">Grade Δ</th>'
        f'<th style="text-align:center;">Tier</th>'
        f'<th style="text-align:right;">Orig Value</th>'
        f'<th style="text-align:right;">New Value</th>'
        f'<th style="text-align:right;">Value Δ</th>'
        '</tr></thead>'
        '<tbody>' + ''.join(rows_html) + '</tbody>'
        '</table></div>'
    )

    st.markdown(table_html, unsafe_allow_html=True)

    # Player count
    st.caption(f"Showing {len(results_df)} of {n_players} {selected_pos} players")

# ── Footer ──
render_footer()
