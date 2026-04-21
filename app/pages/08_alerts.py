"""
NILytics — Alerts Dashboard (D9)
Surface notable changes: grade drops, trajectory shifts, market moves, and roster risks.
Scans multi-season data on demand (no background jobs needed).
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

st.set_page_config(page_title="NILytics — Alerts", page_icon="🏈", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()
render_logo_and_nav(active_page='alerts')
user = check_auth()
render_user_sidebar()

st.markdown("## Alert Dashboard")
st.caption("Notable changes and watchlist items detected from multi-season analysis. Filter by severity, type, and position below.")


@st.cache_data(ttl=300)
def _generate_alerts(current_season: int, prior_season: int):
    """Scan for alerts by comparing two seasons."""
    alerts = []

    try:
        cur_df = load_leaderboard(current_season)
        prev_df = load_leaderboard(prior_season)
    except Exception:
        return alerts

    if cur_df.empty or prev_df.empty:
        return alerts

    # Merge current and prior by player_id
    merged = cur_df.merge(
        prev_df[['player_id', 'core_grade', 'output_score', 'adjusted_value', 'market_value', 'tier']],
        on='player_id', how='inner', suffixes=('', '_prev')
    )

    for _, row in merged.iterrows():
        name = row.get('name', '?')
        pos = row.get('position', '?')
        school = row.get('school', '?')
        pid = row.get('player_id', 0)

        cur_grade = float(row.get('core_grade', 0) or 0)
        prev_grade = float(row.get('core_grade_prev', 0) or 0)
        grade_delta = cur_grade - prev_grade

        cur_val = float(row.get('adjusted_value', 0) or 0)
        prev_val = float(row.get('adjusted_value_prev', 0) or 0)
        val_delta = cur_val - prev_val

        cur_mkt = float(row.get('market_value', 0) or 0)
        prev_mkt = float(row.get('market_value_prev', 0) or 0)
        mkt_delta = cur_mkt - prev_mkt

        cur_tier = row.get('tier', '')
        prev_tier = row.get('tier_prev', '')

        traj = row.get('trajectory_flag', '')

        # Alert: Significant grade drop (>10 points)
        if grade_delta < -10:
            alerts.append({
                'type': '📉 Grade Drop',
                'severity': 'high' if grade_delta < -15 else 'medium',
                'player': name,
                'position': pos,
                'school': school,
                'player_id': pid,
                'detail': f"Grade fell {grade_delta:+.1f} ({prev_grade:.1f} → {cur_grade:.1f})",
                'impact': f"Value change: {fmt_money(int(val_delta))}",
            })

        # Alert: Breakout (grade jump > 10)
        if grade_delta > 10:
            alerts.append({
                'type': '🚀 Breakout',
                'severity': 'info',
                'player': name,
                'position': pos,
                'school': school,
                'player_id': pid,
                'detail': f"Grade jumped {grade_delta:+.1f} ({prev_grade:.1f} → {cur_grade:.1f})",
                'impact': f"Value change: +{fmt_money(int(val_delta))}",
            })

        # Alert: Tier change
        tier_order = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}
        if cur_tier in tier_order and prev_tier in tier_order:
            if tier_order[cur_tier] < tier_order[prev_tier]:
                alerts.append({
                    'type': '⬆️ Tier Promotion',
                    'severity': 'info',
                    'player': name,
                    'position': pos,
                    'school': school,
                    'player_id': pid,
                    'detail': f"Promoted from {prev_tier} → {cur_tier}",
                    'impact': f"New value: {fmt_money(int(cur_val))}",
                })
            elif tier_order[cur_tier] > tier_order[prev_tier]:
                alerts.append({
                    'type': '⬇️ Tier Demotion',
                    'severity': 'medium',
                    'player': name,
                    'position': pos,
                    'school': school,
                    'player_id': pid,
                    'detail': f"Demoted from {prev_tier} → {cur_tier}",
                    'impact': f"New value: {fmt_money(int(cur_val))}",
                })

        # Alert: Market rate spike (>50% increase)
        if prev_mkt > 10000 and mkt_delta > 0:
            pct = (mkt_delta / prev_mkt) * 100
            if pct > 50:
                alerts.append({
                    'type': '💰 Market Spike',
                    'severity': 'high' if pct > 100 else 'medium',
                    'player': name,
                    'position': pos,
                    'school': school,
                    'player_id': pid,
                    'detail': f"Market rate up {pct:.0f}% ({fmt_money(int(prev_mkt))} → {fmt_money(int(cur_mkt))})",
                    'impact': f"Alpha: {fmt_money(int(cur_val - cur_mkt))}",
                })

        # Alert: Significantly overvalued (alpha < -200K)
        alpha = cur_val - cur_mkt
        if alpha < -200000:
            alerts.append({
                'type': '⚠️ Overvalued',
                'severity': 'medium',
                'player': name,
                'position': pos,
                'school': school,
                'player_id': pid,
                'detail': f"Market pays {fmt_money(int(cur_mkt))} but production worth {fmt_money(int(cur_val))}",
                'impact': f"Alpha: {fmt_money(int(alpha))}",
            })

        # Alert: Trajectory DOWN with high market value
        if traj == 'DOWN' and cur_mkt > 100000:
            alerts.append({
                'type': '📉 Declining + Expensive',
                'severity': 'high',
                'player': name,
                'position': pos,
                'school': school,
                'player_id': pid,
                'detail': f"Trending DOWN with {fmt_money(int(cur_mkt))} market rate",
                'impact': "Risk of overpaying for declining production",
            })

    return alerts


# ── Season + Filter row ──
# Pre-load alerts for all 3 seasons to enable single-row filter layout
_alert_season_default = st.session_state.get('alert_season', 2025)

# Load data first
with st.spinner("Scanning for alerts..."):
    alerts = _generate_alerts(_alert_season_default, _alert_season_default - 1)

# All filters in one row
_alert_types = sorted(set(a['type'] for a in alerts)) if alerts else []
_severities = ['all', 'high', 'medium', 'info']
_positions = sorted(set(a['position'] for a in alerts)) if alerts else []

_af0, _af1, _af2, _af3 = st.columns([1, 1.5, 1, 2])
_alert_season = _af0.selectbox("Season", [2025, 2024, 2023], key="alert_season")

# Reload if season changed
if _alert_season != _alert_season_default:
    st.rerun()

if not alerts:
    st.info(f"No alerts detected comparing {_alert_season - 1} → {_alert_season}. "
            "This could mean no prior season data is available.")
else:
    _type_filter = _af1.selectbox("Alert Type", ['All'] + _alert_types, key="alert_type_filter")
    _sev_filter = _af2.selectbox("Severity", _severities, index=0, key="alert_sev_filter")
    _pos_filter = _af3.selectbox("Position", ['All'] + _positions, key="alert_pos_filter")

    filtered = alerts
    if _type_filter != 'All':
        filtered = [a for a in filtered if a['type'] == _type_filter]
    if _sev_filter != 'all':
        filtered = [a for a in filtered if a['severity'] == _sev_filter]
    if _pos_filter != 'All':
        filtered = [a for a in filtered if a['position'] == _pos_filter]

    # Summary KPIs
    _high = len([a for a in filtered if a['severity'] == 'high'])
    _med = len([a for a in filtered if a['severity'] == 'medium'])
    _info = len([a for a in filtered if a['severity'] == 'info'])

    st.markdown(
        f'<div style="display:flex;gap:12px;margin-bottom:16px;">'
        f'<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:12px 20px;flex:1;text-align:center;">'
        f'<div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.08em;">Total</div>'
        f'<div style="font-size:24px;font-weight:800;color:#1f2937;">{len(filtered)}</div></div>'
        f'<div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;padding:12px 20px;flex:1;text-align:center;">'
        f'<div style="font-size:11px;color:#dc2626;text-transform:uppercase;letter-spacing:0.08em;">High</div>'
        f'<div style="font-size:24px;font-weight:800;color:#dc2626;">{_high}</div></div>'
        f'<div style="background:#fef9c3;border:1px solid #fde047;border-radius:8px;padding:12px 20px;flex:1;text-align:center;">'
        f'<div style="font-size:11px;color:#b45309;text-transform:uppercase;letter-spacing:0.08em;">Medium</div>'
        f'<div style="font-size:24px;font-weight:800;color:#b45309;">{_med}</div></div>'
        f'<div style="background:#dbeafe;border:1px solid #93c5fd;border-radius:8px;padding:12px 20px;flex:1;text-align:center;">'
        f'<div style="font-size:11px;color:#2563eb;text-transform:uppercase;letter-spacing:0.08em;">Info</div>'
        f'<div style="font-size:24px;font-weight:800;color:#2563eb;">{_info}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Alert table
    _sev_colors = {'high': '#dc2626', 'medium': '#d97706', 'info': '#2563eb'}

    def _group_alerts(alerts):
        """Group alerts by player_id, keeping all alert types together."""
        groups = {}
        for a in alerts:
            pid = a.get('player_id', 0)
            if pid not in groups:
                groups[pid] = {'player': a['player'], 'position': a['position'], 'school': a['school'], 'player_id': pid, 'alerts': []}
            groups[pid]['alerts'].append(a)
        # Sort groups by highest severity alert count
        sev_rank = {'high': 0, 'medium': 1, 'info': 2}
        return sorted(groups.values(), key=lambda g: min(sev_rank.get(a['severity'], 3) for a in g['alerts']))

    ALERTS_PER_PAGE = 25
    _groups = _group_alerts(filtered)
    _total_groups = len(_groups)
    _total_alert_pages = max(1, (_total_groups + ALERTS_PER_PAGE - 1) // ALERTS_PER_PAGE)

    if 'alert_page' not in st.session_state:
        st.session_state['alert_page'] = 1

    _alert_page = st.session_state['alert_page']
    if _alert_page > _total_alert_pages:
        _alert_page = _total_alert_pages
        st.session_state['alert_page'] = _alert_page

    _start = (_alert_page - 1) * ALERTS_PER_PAGE
    _page_groups = _groups[_start:_start + ALERTS_PER_PAGE]

    for g in _page_groups:
        _n_alerts = len(g['alerts'])
        _max_sev = min(g['alerts'], key=lambda a: {'high': 0, 'medium': 1, 'info': 2}.get(a['severity'], 3))['severity']
        _color = _sev_colors.get(_max_sev, '#8b949e')

        with st.container():
            # Player header with alert count badge
            st.markdown(
                f'<div style="background:#ffffff;border-left:3px solid {_color};padding:10px 14px;'
                f'margin:8px 0 2px 0;border-radius:0 8px 8px 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<a href="/player_card?pid={g["player_id"]}" target="_self" style="text-decoration:none;">'
                f'<span style="font-size:14px;font-weight:700;color:#1f2937;cursor:pointer;">'
                f'{g["player"]} ({g["position"]}, {g["school"]})</span></a>'
                f'<span style="background:{_color}22;color:{_color};padding:2px 8px;border-radius:4px;'
                f'font-size:11px;font-weight:700;">{_n_alerts} alert{"s" if _n_alerts > 1 else ""}</span></div>',
                unsafe_allow_html=True,
            )
            # Show each alert as a sub-item
            for a in g['alerts']:
                _ac = _sev_colors.get(a['severity'], '#8b949e')
                st.markdown(
                    f'<div style="padding:4px 14px 4px 24px;font-size:12px;color:#6b7280;">'
                    f'<span style="display:inline-block;background:{_ac}15;color:{_ac};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;margin-right:6px;">{a["type"]}</span> '
                    f'{a["detail"]} · {a["impact"]}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

    if _total_alert_pages > 1:
        _pc1, _pc2, _pc3, _pc4, _pc5 = st.columns([1, 1, 3, 1, 1])
        with _pc1:
            if st.button("First", key="alert_pg_first", disabled=(_alert_page <= 1)):
                st.session_state['alert_page'] = 1; st.rerun()
        with _pc2:
            if st.button("Prev", key="alert_pg_prev", disabled=(_alert_page <= 1)):
                st.session_state['alert_page'] = max(1, _alert_page - 1); st.rerun()
        with _pc3:
            st.markdown(f'<p style="text-align:center;font-size:13px;color:#6b7280;padding-top:6px;">'
                        f'Page {_alert_page} of {_total_alert_pages} ({_total_groups} players)</p>', unsafe_allow_html=True)
        with _pc4:
            if st.button("Next", key="alert_pg_next", disabled=(_alert_page >= _total_alert_pages)):
                st.session_state['alert_page'] = min(_total_alert_pages, _alert_page + 1); st.rerun()
        with _pc5:
            if st.button("Last", key="alert_pg_last", disabled=(_alert_page >= _total_alert_pages)):
                st.session_state['alert_page'] = _total_alert_pages; st.rerun()

    # Roster-specific alerts (if GM Mode roster exists)
    roster = st.session_state.get('gm_roster', {})
    if roster:
        st.markdown("---")
        st.markdown("### Roster Watch")
        st.caption("Alerts for players currently on your GM Mode roster.")

        _roster_pids = set(int(k) for k in roster.keys() if str(k).isdigit())
        _roster_alerts = [a for a in alerts if a.get('player_id') in _roster_pids]

        if _roster_alerts:
            for a in _roster_alerts:
                _color = _sev_colors.get(a['severity'], '#8b949e')
                st.markdown(
                    f'<div style="background:#ffffff;border-left:3px solid {_color};padding:10px 14px;'
                    f'margin:6px 0;border-radius:0 8px 8px 0;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1f2937;">'
                    f'{a["type"]} — {a["player"]}</span><br>'
                    f'<span style="font-size:12px;color:#6b7280;">'
                    f'{a["detail"]} · {a["impact"]}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("No alerts for your rostered players.")

render_footer()
