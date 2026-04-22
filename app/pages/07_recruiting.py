"""
NILytics — Recruiting Class Builder (D7)
Build incoming classes from signees + portal acquisitions with projected valuations.
"""
import json
import streamlit as st
import pandas as pd

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import load_leaderboard
from app.components.card_front import fmt_money
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar
from scoring.freshman_valuation import load_all_prospects


def fmt_money_short(val):
    """Format money in abbreviated form for compact display."""
    val = int(val) if val else 0
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    elif abs(val) >= 1_000:
        return f"${val/1_000:,.0f}K"
    else:
        return f"${val:,}"


st.set_page_config(page_title="NILytics — Recruiting", page_icon="🏈", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

# ── Page CSS ──
st.markdown("""
<style>
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
    width: 0 !important; height: 0 !important; overflow: hidden !important;
    margin: 0 !important; padding: 0 !important;
}
.stRadio > div[role="radiogroup"] > label[data-checked="true"],
.stRadio > div[role="radiogroup"] > label:has(input:checked) {
    background: #E8390E !important; color: #FFFFFF !important;
    border-radius: 6px !important; font-weight: 700 !important;
}
.stRadio > div[role="radiogroup"] > label[data-checked="true"] p,
.stRadio > div[role="radiogroup"] > label[data-checked="true"] span,
.stRadio > div[role="radiogroup"] > label:has(input:checked) p,
.stRadio > div[role="radiogroup"] > label:has(input:checked) span {
    color: #FFFFFF !important;
}
.mono { font-family: 'DM Mono', 'SF Mono', 'Fira Code', monospace; }
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='recruiting')
user = check_auth()
render_user_sidebar()

st.markdown("## Recruiting Class Builder")
st.markdown('<p style="font-size:14px;color:#6b7280;margin-top:-8px;">Combine incoming signees and transfer portal targets into a single recruiting class projection.</p>', unsafe_allow_html=True)

# ── Session state for recruiting class ──
if 'recruit_class' not in st.session_state:
    st.session_state['recruit_class'] = {}  # pid -> player_dict

recruit_class = st.session_state['recruit_class']

# ── Budget ──
BUDGET_PRESETS = {
    'Blue Blood ($12M+)': 12_000_000,
    'P4 Contender ($8M)': 8_000_000,
    'P4 Average ($5M)': 5_000_000,
    'P4 Lower ($3M)': 3_000_000,
    'G6 Top ($1.5M)': 1_500_000,
    'G6 Average ($750K)': 750_000,
    'FCS ($250K)': 250_000,
    'Custom': 0,
}
st.sidebar.markdown("### Recruiting Budget")
_budget_tier = st.sidebar.selectbox("Budget Tier", list(BUDGET_PRESETS.keys()), index=2, key="rc_budget_tier")
if _budget_tier == 'Custom':
    rc_budget = st.sidebar.number_input("Custom Budget ($)", min_value=0, max_value=50_000_000,
                                         value=5_000_000, step=500_000, format="$%d", key="rc_budget_custom")
else:
    rc_budget = BUDGET_PRESETS[_budget_tier]
    st.sidebar.markdown(f'<div style="font-size:18px;font-weight:700;color:#1f2937;font-family:DM Mono,monospace;">{fmt_money_short(rc_budget)}</div>', unsafe_allow_html=True)

# ── Load data ──
with st.spinner("Loading data..."):
    prospects = load_all_prospects([2025, 2026])
    prospect_df = pd.DataFrame(prospects) if prospects else pd.DataFrame()

    # Portal targets: current season players with positive alpha (undervalued)
    try:
        portal_df = load_leaderboard(2025)
    except Exception:
        portal_df = pd.DataFrame()

# ── View toggle (with counts) ──
_prospect_count = len(prospect_df) if not prospect_df.empty else 0
_portal_count = len(portal_df[portal_df['opportunity_score'].fillna(0) > 0]) if not portal_df.empty else 0
_class_count = len(recruit_class)
rc_view = st.radio("View", [f"Class Overview ({_class_count})", f"Prospect Pool ({_prospect_count})", f"Portal Targets ({_portal_count})"],
                    horizontal=True, label_visibility="collapsed", key="rc_view")


def _add_to_class(player_dict, source='prospect'):
    """Add a player to the recruiting class."""
    pid = str(player_dict.get('player_id', ''))
    if pid and pid not in recruit_class:
        player_dict['_source'] = source
        st.session_state['recruit_class'][pid] = player_dict


def _remove_from_class(pid):
    """Remove a player from the recruiting class."""
    pid = str(pid)
    if pid in st.session_state['recruit_class']:
        del st.session_state['recruit_class'][pid]


if rc_view.startswith("Class Overview"):
    if not recruit_class:
        st.markdown(
            '<div style="text-align:center;padding:48px 24px;background:#f9fafb;border:1px dashed #d1d5db;border-radius:12px;margin:16px 0;">'
            '<div style="font-size:48px;margin-bottom:12px;">🎓</div>'
            '<div style="font-size:18px;font-weight:700;color:#1f2937;margin-bottom:8px;">No recruits in your class yet</div>'
            '<div style="font-size:13px;color:#6b7280;max-width:400px;margin:0 auto;">'
            'Browse the <strong style="color:#E8390E;">Prospect Pool</strong> or '
            '<strong style="color:#E8390E;">Portal Targets</strong> tabs to build your class.'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        class_df = pd.DataFrame(list(recruit_class.values()))

        # KPIs
        _rc_total_val = class_df['adjusted_value'].fillna(0).astype(float).sum()
        _rc_total_mkt = class_df['market_value'].fillna(0).astype(float).sum()
        _rc_total_alpha = _rc_total_val - _rc_total_mkt
        _rc_remaining = rc_budget - int(_rc_total_mkt)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Recruits", len(class_df))
        k2.metric("Total Value", fmt_money_short(int(_rc_total_val)))
        k3.metric("Total Cost", fmt_money_short(int(_rc_total_mkt)))
        k4.metric("Class Alpha", fmt_money_short(int(_rc_total_alpha)))
        k5.metric("Budget Left", fmt_money_short(_rc_remaining))

        if _rc_remaining < 0:
            st.error(f"Over budget by {fmt_money(abs(_rc_remaining))}")

        # Position breakdown
        st.markdown("**Class by Position**")
        _pos_data = []
        for _pos in ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']:
            _pp = class_df[class_df['position'] == _pos]
            if _pp.empty:
                continue
            _pos_data.append({
                'Position': _pos,
                'Count': len(_pp),
                'Avg Grade': round(_pp['core_grade'].astype(float).mean(), 1),
                'Total Value': fmt_money(int(_pp['adjusted_value'].fillna(0).astype(float).sum())),
                'Total Cost': fmt_money(int(_pp['market_value'].fillna(0).astype(float).sum())),
                'Source': f"{len(_pp[_pp.get('_source', '') == 'prospect'])} HS / {len(_pp[_pp.get('_source', '') == 'portal'])} Portal"
                if '_source' in _pp.columns else '',
            })
        if _pos_data:
            st.dataframe(pd.DataFrame(_pos_data), use_container_width=True, hide_index=True)

        # Full class list
        st.markdown("**Full Class**")
        _display = class_df[['name', 'position', 'school', 'tier', 'core_grade',
                              'adjusted_value', 'market_value']].copy()
        _display.columns = ['Name', 'Pos', 'School', 'Tier', 'Grade', 'Value', 'Cost']
        _display['Grade'] = _display['Grade'].astype(float).round(1)
        _display['Value'] = _display['Value'].apply(lambda x: fmt_money(int(float(x))) if pd.notna(x) else '--')
        _display['Cost'] = _display['Cost'].apply(lambda x: fmt_money(int(float(x))) if pd.notna(x) else '--')
        st.dataframe(_display, use_container_width=True, hide_index=True)

        # Remove buttons
        st.markdown("**Remove from class:**")
        _remove_cols = st.columns(min(5, len(recruit_class)))
        for i, (pid, p) in enumerate(list(recruit_class.items())):
            with _remove_cols[i % min(5, len(recruit_class))]:
                if st.button(f"✕ {p.get('name', '?')}", key=f"rc_remove_{pid}"):
                    _remove_from_class(pid)
                    st.rerun()

        if st.button("⚠️ Clear Entire Class", type="secondary", key="rc_clear"):
            st.session_state['recruit_class'] = {}
            st.rerun()


elif rc_view.startswith("Prospect Pool"):
    st.markdown("### High School Prospects (ESPN 300)")

    if prospect_df.empty:
        st.info("No prospect data available. Ensure ESPN 300 CSVs are in data/recruits/.")
    else:
        # Filters
        _pf1, _pf2, _pf3 = st.columns(3)
        _class_year = _pf1.selectbox("Class", sorted(prospect_df['recruit_class'].unique().tolist(), reverse=True),
                                      key="rc_class_year")
        _pos_filter = _pf2.selectbox("Position", ['All'] + sorted(prospect_df['position'].unique().tolist()),
                                      key="rc_pos")
        _search = _pf3.text_input("Search", placeholder="Player name...", key="rc_search")

        _pool = prospect_df[prospect_df['recruit_class'] == _class_year].copy()
        if _pos_filter != 'All':
            _pool = _pool[_pool['position'] == _pos_filter]
        if _search and len(_search) >= 2:
            _pool = _pool[_pool['name'].str.contains(_search, case=False, na=False)]

        _pool = _pool.sort_values('recruit_rank' if 'recruit_rank' in _pool.columns else 'core_grade',
                                   ascending='recruit_rank' in _pool.columns)

        if _pool.empty:
            st.info("No prospects match filters.")
        else:
            st.markdown(f"**{len(_pool)} prospects**")

            _class_pids = set(recruit_class.keys())
            _disp = _pool[['name', 'position', 'school', 'tier', 'stars', 'core_grade',
                            'adjusted_value', 'market_value', 'player_id']].copy()
            _disp.columns = ['Name', 'Pos', 'School', 'Tier', 'Stars', 'Grade', 'Value', 'Cost', 'pid']
            _disp['Grade'] = _disp['Grade'].astype(float).round(1)
            _disp['Value'] = _disp['Value'].apply(lambda x: fmt_money(int(float(x))) if pd.notna(x) else '--')
            _disp['Cost'] = _disp['Cost'].apply(lambda x: fmt_money(int(float(x))) if pd.notna(x) else '--')
            _disp['Stars'] = _disp['Stars'].apply(lambda x: '⭐' * int(x) if pd.notna(x) else '')
            _disp['Select'] = _disp['pid'].apply(lambda x: str(x) in _class_pids)
            _disp_show = _disp.drop(columns=['pid'])
            _edited = st.data_editor(
                _disp_show,
                column_config={"Select": st.column_config.CheckboxColumn("Add", default=False)},
                disabled=[c for c in _disp_show.columns if c != 'Select'],
                use_container_width=True, hide_index=True, key="prospect_editor"
            )
            # Process checkbox selections
            _needs_rerun = False
            for idx in range(len(_edited)):
                _pid = str(_pool.iloc[idx]['player_id'])
                _selected = _edited.iloc[idx].get('Select', False)
                if _selected and _pid not in _class_pids:
                    _add_to_class(_pool.iloc[idx].to_dict(), source='prospect')
                    _needs_rerun = True
                elif not _selected and _pid in _class_pids:
                    _remove_from_class(_pid)
                    _needs_rerun = True
            if _needs_rerun:
                st.rerun()


elif rc_view.startswith("Portal Targets"):
    st.markdown("### Transfer Portal Targets")
    st.caption("Current players with positive alpha (undervalued) who could be portal acquisition targets.")

    if portal_df.empty:
        st.info("No portal data available for 2025.")
    else:
        # Filters
        _tf1, _tf2, _tf3, _tf4 = st.columns(4)
        _t_pos = _tf1.selectbox("Position", ['All'] + sorted(portal_df['position'].dropna().unique().tolist()),
                                 key="rc_portal_pos")
        _t_tier = _tf2.selectbox("Tier", ['All', 'T1', 'T2', 'T3', 'T4'], key="rc_portal_tier")
        _t_search = _tf3.text_input("Search", placeholder="Player name...", key="rc_portal_search")
        _t_max_cost = _tf4.number_input("Max Cost ($)", min_value=0, max_value=10_000_000,
                                         value=1_000_000, step=100_000, format="%d", key="rc_portal_max")

        # Filter to undervalued players
        _portal_all = portal_df[portal_df['opportunity_score'].fillna(0) > 0].copy()
        _total_undervalued = len(_portal_all)
        _portal = _portal_all.copy()
        if _t_pos != 'All':
            _portal = _portal[_portal['position'] == _t_pos]
        if _t_tier != 'All':
            _portal = _portal[_portal['tier'] == _t_tier]
        if _t_search and len(_t_search) >= 2:
            _portal = _portal[_portal['name'].str.contains(_t_search, case=False, na=False)]
        _portal = _portal[_portal['market_value'].fillna(0) <= _t_max_cost]
        _portal = _portal.sort_values('opportunity_score', ascending=False)

        if _portal.empty:
            st.info("No portal targets match filters.")
        else:
            # Show filtered count and the total — eliminates the tab-vs-header count confusion.
            _filt_note = "" if len(_portal) == _total_undervalued else (
                f" <span style='color:#9ca3af;font-weight:400;'>of {_total_undervalued:,} "
                f"total undervalued players (filters applied)</span>"
            )
            st.markdown(
                f"**{len(_portal):,} undervalued players**{_filt_note}",
                unsafe_allow_html=True,
            )

            _class_pids = set(recruit_class.keys())
            _pdisp = _portal[['name', 'position', 'school', 'tier', 'core_grade', 'output_score',
                               'adjusted_value', 'market_value', 'opportunity_score', 'player_id']].head(50).copy()
            _pdisp.columns = ['Name', 'Pos', 'School', 'Tier', 'Grade', 'Output', 'Value', 'Cost', 'Alpha', 'pid']
            _pdisp['Grade'] = _pdisp['Grade'].round(1)
            _pdisp['Output'] = _pdisp['Output'].round(1)
            _pdisp['Value'] = _pdisp['Value'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
            _pdisp['Cost'] = _pdisp['Cost'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
            _pdisp['Alpha'] = _pdisp['Alpha'].apply(lambda x: fmt_money(int(x)) if pd.notna(x) else '--')
            _pdisp['Select'] = _pdisp['pid'].apply(lambda x: str(x) in _class_pids)
            _pdisp_show = _pdisp.drop(columns=['pid'])
            _portal_head = _portal.head(50).reset_index(drop=True)
            _pedited = st.data_editor(
                _pdisp_show,
                column_config={"Select": st.column_config.CheckboxColumn("Add", default=False)},
                disabled=[c for c in _pdisp_show.columns if c != 'Select'],
                use_container_width=True, hide_index=True, key="portal_editor"
            )
            # Process checkbox selections
            _needs_rerun = False
            for idx in range(len(_pedited)):
                _pid = str(_portal_head.iloc[idx]['player_id'])
                _selected = _pedited.iloc[idx].get('Select', False)
                if _selected and _pid not in _class_pids:
                    _add_to_class(_portal_head.iloc[idx].to_dict(), source='portal')
                    _needs_rerun = True
                elif not _selected and _pid in _class_pids:
                    _remove_from_class(_pid)
                    _needs_rerun = True
            if _needs_rerun:
                st.rerun()

render_footer()
