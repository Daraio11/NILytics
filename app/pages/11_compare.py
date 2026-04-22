"""
NILytics — Compare Players
Dedicated side-by-side comparison view for up to 4 players.
Session-backed so additions from Leaderboard / Player Card persist here.
"""
import streamlit as st
import pandas as pd

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import load_leaderboard, load_player_info, load_player_history
from app.components.card_front import fmt_money, TIER_COLORS
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Compare", page_icon="🏈", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()
render_logo_and_nav(active_page='compare')
user = check_auth()
render_user_sidebar()

# Shared compare pool across pages
if 'compare_players' not in st.session_state:
    st.session_state['compare_players'] = {}

st.markdown("## Compare Players")
st.caption("Head-to-head comparison for up to 4 players. Add players from the Leaderboard or Player Card.")

# ── Handle query param pid additions (e.g., from Leaderboard) ──
qp = st.query_params

# Bulk restore from a shared comparison link: /compare?pids=123,456,789
if 'pids' in qp:
    try:
        _raw = qp['pids']
        _pid_list = [int(x.strip()) for x in _raw.split(',') if x.strip()]
        st.session_state['compare_players'] = {}  # fresh slate for shared link
        for _share_pid in _pid_list[:4]:
            _pinfo = load_player_info(_share_pid)
            _scores_df, _signals_df = load_player_history(_share_pid)
            if _pinfo and not _scores_df.empty:
                _latest_scores = _scores_df.sort_values('season', ascending=False).iloc[0].to_dict()
                _latest_signals = (_signals_df.sort_values('season', ascending=False).iloc[0].to_dict()
                                   if not _signals_df.empty else
                                   {'market_value': 0, 'opportunity_score': 0, 'trajectory_flag': 'STABLE', 'flags': '[]'})
                st.session_state['compare_players'][_share_pid] = {
                    'name': _pinfo.get('name', '?'),
                    'position': _pinfo.get('position', '?'),
                    'school': _pinfo.get('school', '?'),
                    'conference': _pinfo.get('conference', ''),
                    'market': _pinfo.get('market', ''),
                    'tier': _latest_scores.get('tier', 'T4'),
                    'core_grade': float(_latest_scores.get('core_grade', 0) or 0),
                    'output_score': float(_latest_scores.get('output_score', 0) or 0),
                    'adjusted_value': float(_latest_scores.get('adjusted_value', 0) or 0),
                    'market_value': float(_latest_signals.get('market_value', 0) or 0),
                    'opportunity_score': float(_latest_signals.get('opportunity_score', 0) or 0),
                    'trajectory_flag': _latest_signals.get('trajectory_flag', 'STABLE'),
                    'flags': _latest_signals.get('flags', '[]'),
                }
        st.query_params.clear()
    except (ValueError, TypeError):
        pass

if 'add_pid' in qp:
    try:
        _add_pid = int(qp['add_pid'])
        if _add_pid not in st.session_state['compare_players'] and len(st.session_state['compare_players']) < 4:
            _pinfo = load_player_info(_add_pid)
            _scores_df, _signals_df = load_player_history(_add_pid)
            if _pinfo and not _scores_df.empty:
                # Pick most-recent season
                _latest_scores = _scores_df.sort_values('season', ascending=False).iloc[0].to_dict()
                if not _signals_df.empty:
                    _latest_signals = _signals_df.sort_values('season', ascending=False).iloc[0].to_dict()
                else:
                    _latest_signals = {'market_value': 0, 'opportunity_score': 0, 'trajectory_flag': 'STABLE', 'flags': '[]'}
                st.session_state['compare_players'][_add_pid] = {
                    'name': _pinfo.get('name', '?'),
                    'position': _pinfo.get('position', '?'),
                    'school': _pinfo.get('school', '?'),
                    'conference': _pinfo.get('conference', ''),
                    'market': _pinfo.get('market', ''),
                    'tier': _latest_scores.get('tier', 'T4'),
                    'core_grade': float(_latest_scores.get('core_grade', 0) or 0),
                    'output_score': float(_latest_scores.get('output_score', 0) or 0),
                    'adjusted_value': float(_latest_scores.get('adjusted_value', 0) or 0),
                    'market_value': float(_latest_signals.get('market_value', 0) or 0),
                    'opportunity_score': float(_latest_signals.get('opportunity_score', 0) or 0),
                    'trajectory_flag': _latest_signals.get('trajectory_flag', 'STABLE'),
                    'flags': _latest_signals.get('flags', '[]'),
                }
        st.query_params.clear()
    except (ValueError, TypeError):
        pass

# ── Player picker + Clear control ──
_p1, _p2, _p3 = st.columns([3, 1, 1])

with _p1:
    if len(st.session_state['compare_players']) < 4:
        with st.spinner("Loading players..."):
            df_all = load_leaderboard(2025)
        if not df_all.empty:
            # Exclude already-added players
            _added_pids = set(st.session_state['compare_players'].keys())
            _available = df_all[~df_all['player_id'].isin(_added_pids)].copy()
            _available['_display'] = _available.apply(
                lambda r: f"{r['name']}  ·  {r.get('position', '?')} · {r.get('school', '?')} · T{r.get('tier', '?')[-1] if pd.notna(r.get('tier')) else '?'}",
                axis=1,
            )
            _options = [''] + _available['_display'].tolist()
            _sel = st.selectbox(
                f"Add a player ({len(st.session_state['compare_players'])}/4 selected)",
                _options,
                key="cmp_add_search",
            )
            if _sel and _sel != '':
                _match = _available[_available['_display'] == _sel].iloc[0]
                _pid = int(_match['player_id'])
                if _pid not in st.session_state['compare_players']:
                    st.session_state['compare_players'][_pid] = {
                        'name': _match.get('name', '?'),
                        'position': _match.get('position', '?'),
                        'school': _match.get('school', '?'),
                        'conference': _match.get('conference', ''),
                        'market': _match.get('market', ''),
                        'tier': _match.get('tier', 'T4'),
                        'core_grade': float(_match.get('core_grade', 0) or 0),
                        'output_score': float(_match.get('output_score', 0) or 0),
                        'adjusted_value': float(_match.get('adjusted_value', 0) or 0),
                        'market_value': float(_match.get('market_value', 0) or 0),
                        'opportunity_score': float(_match.get('opportunity_score', 0) or 0),
                        'trajectory_flag': _match.get('trajectory_flag', 'STABLE'),
                        'flags': _match.get('flags', '[]'),
                    }
                    st.rerun()
    else:
        st.info("Maximum 4 players reached. Remove one to add another.")

with _p2:
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    if st.session_state['compare_players']:
        if st.button("Clear All", use_container_width=True, key="cmp_clear"):
            st.session_state['compare_players'] = {}
            st.rerun()

with _p3:
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    if st.button("← Leaderboard", use_container_width=True, key="cmp_back"):
        st.switch_page("pages/01_leaderboard.py")

# ── Empty state ──
if not st.session_state['compare_players']:
    st.markdown(
        '<div style="text-align:center;padding:48px 24px;background:#f9fafb;border:1px dashed #d1d5db;'
        'border-radius:12px;margin:20px 0;">'
        '<div style="font-size:48px;margin-bottom:12px;">⚖️</div>'
        '<div style="font-size:18px;font-weight:700;color:#1f2937;margin-bottom:8px;">Nothing to compare yet</div>'
        '<div style="font-size:13px;color:#6b7280;max-width:440px;margin:0 auto;">'
        'Use the search above to add up to 4 players. You can also click <b>Add to Compare</b> '
        'on any Player Card to drop someone into this view.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    render_footer()
    st.stop()

# ── Render Comparison ──
cmp_data = st.session_state['compare_players']
cmp_pids = list(cmp_data.keys())
n = len(cmp_pids)

# Header cards per player
_pl_hdr, _pl_share = st.columns([5, 1.2])
with _pl_hdr:
    st.markdown("### Players")
with _pl_share:
    # Share-link near the heading for discoverability
    _share_pids_top = ",".join(str(p) for p in cmp_pids)
    _share_url_top = f"/compare?pids={_share_pids_top}"
    if st.button("🔗 Copy share link", key="share_compare_top", use_container_width=True,
                 help=("Copy a URL that opens this exact comparison — shareable with teammates. "
                       "Anyone with the link sees the same players head-to-head.")):
        import streamlit.components.v1 as _cmp_html_top
        _cmp_html_top.html(
            f"<script>navigator.clipboard.writeText(window.location.origin + '{_share_url_top}');</script>",
            height=0,
        )
        st.toast(f"Link copied — {_share_url_top}", icon="🔗")

_hdr_cols = st.columns(n)
for i, pid in enumerate(cmp_pids):
    p = cmp_data[pid]
    _tc = TIER_COLORS.get(p['tier'], '#6B7280')
    with _hdr_cols[i]:
        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div><div style="font-size:15px;font-weight:800;color:#1f2937;">{p["name"]}</div>'
            f'<div style="font-size:11px;color:#6b7280;">{p["position"]} · {p["school"]}</div></div>'
            f'<span style="background:{_tc};color:#fff;font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;">{p["tier"]}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        _rc1, _rc2, _rc3 = st.columns([1.5, 1, 1])
        with _rc1:
            if st.button("View Card", key=f"cmp_view_{pid}", use_container_width=True):
                st.session_state['selected_player_id'] = pid
                st.switch_page("pages/02_player_card.py")
        with _rc2:
            # Swap left (disabled on first column)
            can_swap_left = i > 0
            if st.button("◀", key=f"cmp_swap_l_{pid}", use_container_width=True,
                         help="Move this player one slot left" if can_swap_left else "Already leftmost",
                         disabled=not can_swap_left):
                # Rebuild dict with this pid swapped with the previous
                _keys = list(cmp_data.keys())
                _keys[i], _keys[i - 1] = _keys[i - 1], _keys[i]
                st.session_state['compare_players'] = {k: cmp_data[k] for k in _keys}
                st.rerun()
        with _rc3:
            if st.button("Remove", key=f"cmp_rm_{pid}", use_container_width=True,
                         help="Remove this player from the comparison"):
                del st.session_state['compare_players'][pid]
                st.rerun()

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
st.markdown("### Side-by-Side Metrics")

# ── Metric comparison table ──
metrics = [
    ('Position',     lambda p: p['position'],                              'text'),
    ('Conference',   lambda p: p.get('conference', '—') or '—',             'text'),
    ('Market',       lambda p: p.get('market', '—') or '—',                 'text'),
    ('Tier',         lambda p: p['tier'],                                  'text'),
    ('Core Grade',   lambda p: p.get('core_grade', 0),                     'number_hi'),
    ('Output Score', lambda p: p.get('output_score', 0),                   'number_hi'),
    ('Value',        lambda p: p.get('adjusted_value', 0),                 'money_hi'),
    ('Mkt Value',    lambda p: p.get('market_value', 0),                   'money_lo'),
    ('Alpha',        lambda p: p.get('opportunity_score', 0),              'money_hi'),
    ('Trajectory',   lambda p: (p.get('trajectory_flag') or 'STABLE').title(), 'text'),
]

# Compute best value per row for numeric metrics
def _format_val(metric_type, v):
    if metric_type == 'text':
        return str(v)
    try:
        fv = float(v)
    except (ValueError, TypeError):
        return '—'
    if metric_type.startswith('money'):
        if fv > 0 and metric_type == 'money_hi':
            return fmt_money(int(fv))
        return fmt_money(int(fv))
    return f"{fv:.1f}"

# Build HTML table with highlighted bests
rows_html = []
for label, fn, mtype in metrics:
    vals = [fn(cmp_data[pid]) for pid in cmp_pids]
    # determine best index
    best_idx = None
    if mtype in ('number_hi', 'money_hi'):
        try:
            num_vals = [float(v) for v in vals]
            if num_vals:
                best_idx = num_vals.index(max(num_vals))
        except (ValueError, TypeError):
            pass
    elif mtype == 'money_lo':
        try:
            num_vals = [float(v) for v in vals]
            if num_vals:
                best_idx = num_vals.index(min(num_vals))
        except (ValueError, TypeError):
            pass

    tds = []
    for i, v in enumerate(vals):
        formatted = _format_val(mtype, v)
        is_best = (best_idx == i)
        # Special coloring for Alpha
        if label == 'Alpha':
            try:
                alpha_num = float(v)
                if alpha_num > 0:
                    formatted = f'+{fmt_money(int(abs(alpha_num)))}'
                    color = '#16a34a'
                elif alpha_num < 0:
                    formatted = f'-{fmt_money(int(abs(alpha_num)))}'
                    color = '#dc2626'
                else:
                    color = '#6b7280'
                _style = f'font-weight:{"800" if is_best else "600"};color:{color};'
            except (ValueError, TypeError):
                _style = 'color:#6b7280;'
        else:
            _style = ('font-weight:800;color:#111827;background:#f0fdf4;' if is_best
                      else 'color:#374151;')
        tds.append(f'<td style="padding:10px 14px;text-align:right;font-size:13px;{_style}">{formatted}</td>')

    rows_html.append(
        f'<tr style="border-bottom:1px solid #f3f4f6;">'
        f'<td style="padding:10px 14px;font-size:12px;color:#6b7280;text-transform:uppercase;'
        f'letter-spacing:0.04em;font-weight:600;">{label}</td>'
        + ''.join(tds) + '</tr>'
    )

header_cells = ''.join(
    f'<th style="padding:10px 14px;text-align:right;font-size:12px;color:#1f2937;'
    f'font-weight:800;">{cmp_data[pid]["name"]}</th>'
    for pid in cmp_pids
)

table_html = (
    '<table style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
    f'<thead><tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;">'
    f'<th style="padding:10px 14px;text-align:left;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;">Metric</th>'
    f'{header_cells}'
    '</tr></thead>'
    f'<tbody>{"".join(rows_html)}</tbody></table>'
)

st.markdown(table_html, unsafe_allow_html=True)
st.caption("💡 Green-highlighted cell = best value on that row. Alpha colored green (undervalued) / red (overvalued).")

# ── Summary Insights ──
st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
st.markdown("### Quick Take")

st.caption(
    f"Computed from most-recent season data on file for each player. "
    f"Alpha = production value minus market price — positive = undervalued deal."
)

if n >= 2:
    # Find the best value buy (highest alpha) and highest grade
    best_alpha_pid = max(cmp_pids, key=lambda pid: cmp_data[pid].get('opportunity_score', 0))
    best_grade_pid = max(cmp_pids, key=lambda pid: cmp_data[pid].get('core_grade', 0))
    best_alpha_p = cmp_data[best_alpha_pid]
    best_grade_p = cmp_data[best_grade_pid]

    _i1, _i2 = st.columns(2)
    with _i1:
        _a = best_alpha_p.get('opportunity_score', 0)
        _sign = '+' if _a > 0 else ''
        st.success(
            f"**Best Moneyball Pick:** {best_alpha_p['name']} ({best_alpha_p['position']}, "
            f"{best_alpha_p['school']}) — **{_sign}{fmt_money(int(_a))} alpha**."
        )
    with _i2:
        st.info(
            f"**Highest Core Grade:** {best_grade_p['name']} ({best_grade_p['position']}, "
            f"{best_grade_p['school']}) — **{best_grade_p.get('core_grade', 0):.1f}**."
        )

render_footer()
