"""
NILytics — Master Leaderboard
PFF-inspired dense data table with flag filters, trajectory, and clickable names.
"""
import json
import streamlit as st
import pandas as pd

# Ensure project root on path
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data import load_leaderboard, load_market_rate_history
from app.components.filters import render_filters, apply_filters
from app.components.card_front import fmt_money
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.components.exports import export_leaderboard_csv
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Leaderboard", page_icon="🏈", layout="wide", initial_sidebar_state="expanded")

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inject fonts before any content
inject_fonts()

# ── Page-level CSS overrides for leaderboard UI ──
st.markdown("""
<style>
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
/* Secondary (inactive) flag buttons */
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
/* Primary (active) flag buttons */
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
    padding: 5px 14px !important;
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
/* Force inner text on inactive */
.stRadio > div[role="radiogroup"] > label p,
.stRadio > div[role="radiogroup"] > label span {
    color: #6b7280 !important;
}
.stRadio > div[role="radiogroup"] > label:hover {
    background: #e5e7eb !important;
}
/* Hide the actual radio circle */
.stRadio > div[role="radiogroup"] > label > div:first-child {
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}
/* Active pill segment */
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

/* ── Reduce whitespace ── */
hr { margin: 0.3rem 0 !important; }
.stRadio { margin-bottom: 0 !important; }
.stCaption { margin-top: -0.25rem !important; margin-bottom: 0.15rem !important; }
/* Pagination buttons */
.stButton > button[kind="secondary"] {
    border: 1px solid #d1d5db !important;
    border-radius: 4px !important;
    padding: 4px 10px !important;
    min-height: 0 !important;
}

/* ── Search bar styling ── */
.search-bar-container .stTextInput input {
    border-radius: 8px !important;
    padding-left: 12px !important;
    height: 36px !important;
}

/* ── Rows per page selectbox compact ── */
.rows-per-page .stSelectbox {
    min-width: 80px;
}
.rows-per-page .stSelectbox label {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* ── Mono class for dollar values ── */
.mono {
    font-family: 'DM Mono', 'SF Mono', 'Fira Code', monospace;
}

/* ── Table header sort arrows ── */
.sort-arrows {
    font-size: 8px;
    color: #4B5563;
    margin-left: 4px;
    letter-spacing: -1px;
    opacity: 0.5;
}
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='leaderboard')

# Auth
user = check_auth()
render_user_sidebar()

# Filters
filters = render_filters()
season = filters['season']

# Load data with spinner
with st.spinner(""):
    try:
        df = load_leaderboard(season)
    except Exception as e:
        st.error("Unable to connect to the database. Supabase may be temporarily down. "
                 "Please refresh in a minute.")
        st.caption(f"Error: {e}")
        st.stop()

if df.empty:
    st.warning(f"No data available for {season}.")
    st.stop()

df = apply_filters(df, filters)

if df.empty:
    st.info("No players match the current filters.")
    st.stop()

# ── Search bar + Flag definitions ──
FLAG_CONFIG = {
    'BREAKOUT_CANDIDATE': {'icon': '🚀', 'label': 'Breakout', 'css': 'flag-breakout'},
    'HIDDEN_GEM':         {'icon': '💎', 'label': 'Hidden Gem', 'css': 'flag-hidden'},
    'REGRESSION_RISK':    {'icon': '📉', 'label': 'Regression', 'css': 'flag-regression'},
    'PORTAL_VALUE':       {'icon': '🔄', 'label': 'Portal Value', 'css': 'flag-portal'},
    'EXPERIENCE_PREMIUM': {'icon': '🎖️', 'label': 'Experienced', 'css': 'flag-experience'},
}

# Count flags in dataset
flag_counts = {}
if 'flags' in df.columns:
    for _, row in df.iterrows():
        flags_raw = row.get('flags', '[]')
        try:
            flag_list = json.loads(flags_raw) if isinstance(flags_raw, str) else (flags_raw if isinstance(flags_raw, list) else [])
        except (json.JSONDecodeError, TypeError):
            flag_list = []
        for f in flag_list:
            flag_counts[f] = flag_counts.get(f, 0) + 1

# ── Search bar row ──
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    player_search = st.text_input(
        "Search players",
        placeholder="\U0001f50d Search by player name, school, or position...",
        label_visibility="collapsed",
        key="leaderboard_search",
    )

# Apply search filter
if player_search and len(player_search) >= 2:
    df = df[df['name'].str.contains(player_search, case=False, na=False)]
    if df.empty:
        st.info(f'No players match "{player_search}".')
        st.stop()

# ── Flag filter buttons ──
if 'active_flag_filter' not in st.session_state:
    st.session_state['active_flag_filter'] = None

flag_cols = st.columns(len(FLAG_CONFIG) + 1)
with flag_cols[0]:
    all_active = st.session_state['active_flag_filter'] is None
    if st.button(f"All ({len(df):,})", key="flag_all", use_container_width=True,
                 type="primary" if all_active else "secondary"):
        st.session_state['active_flag_filter'] = None
        st.rerun()

for i, (flag_key, config) in enumerate(FLAG_CONFIG.items(), 1):
    count = flag_counts.get(flag_key, 0)
    is_active = st.session_state['active_flag_filter'] == flag_key
    with flag_cols[i]:
        if st.button(f"{config['icon']} {config['label']} ({count})", key=f"flag_{flag_key}",
                     use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state['active_flag_filter'] = flag_key
            st.rerun()

# Apply flag filter
active_flag = st.session_state.get('active_flag_filter')
if active_flag and 'flags' in df.columns:
    df = df[df['flags'].apply(lambda x: active_flag in (json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else []))
                                        if pd.notna(x) else False)]
    if df.empty:
        st.info(f"No players with {FLAG_CONFIG.get(active_flag, {}).get('label', active_flag)} flag.")
        st.stop()

# ── View toggle ──
VIEW_INFO = {
    "Scouting — Best Players": {
        'sort': 'core_grade',
        'description': "Ranked by **Core Grade** — who is playing the best football right now?",
    },
    "Moneyball — Best Deals": {
        'sort': 'opportunity_score',
        'description': "Ranked by **Alpha** — who is the most undervalued?",
    },
    "Market — Highest Value": {
        'sort': 'adjusted_value',
        'description': "Ranked by **Value** — whose production justifies the biggest NIL number?",
    },
}

view = st.radio(
    "View",
    list(VIEW_INFO.keys()),
    horizontal=True,
    label_visibility="collapsed",
)

# Contextual subtitle — reflects active flag filter
_active_flag_label = FLAG_CONFIG.get(active_flag, {}).get('label', '') if active_flag else ''
if active_flag and _active_flag_label:
    _flag_count = flag_counts.get(active_flag, 0)
    st.caption(f"Showing **{_flag_count} {_active_flag_label}** players · {VIEW_INFO[view]['description']}")
else:
    st.caption(VIEW_INFO[view]['description'])

# ── Column sort via query params ──
# Sortable columns: key → (default_ascending)
SORTABLE_COLUMNS = {
    'core_grade': False,
    'output_score': False,
    'adjusted_value': False,
    'market_value': False,
    'opportunity_score': False,
    'name': True,
    'school': True,
    'tier': True,
}

view_default_sort = VIEW_INFO[view]['sort']
if view_default_sort not in df.columns:
    view_default_sort = 'core_grade'

# Check query params for sort override
qp_sort = st.query_params.get('sort')
qp_dir = st.query_params.get('dir')

if qp_sort and qp_sort in SORTABLE_COLUMNS:
    sort_col = qp_sort
    # Toggle direction: if clicking same column, flip; otherwise use default
    if 'lb_sort_col' in st.session_state and st.session_state['lb_sort_col'] == qp_sort:
        sort_ascending = not st.session_state.get('lb_sort_asc', SORTABLE_COLUMNS[qp_sort])
    else:
        sort_ascending = qp_dir == 'asc' if qp_dir else SORTABLE_COLUMNS[qp_sort]
    st.session_state['lb_sort_col'] = sort_col
    st.session_state['lb_sort_asc'] = sort_ascending
    st.session_state['lb_page'] = 1
    # Clear sort params so they don't persist on refresh
    st.query_params.clear()
    st.rerun()
else:
    sort_col = st.session_state.get('lb_sort_col', view_default_sort)
    sort_ascending = st.session_state.get('lb_sort_asc', SORTABLE_COLUMNS.get(sort_col, False))

sorted_df = df.sort_values(sort_col, ascending=sort_ascending).reset_index(drop=True)

st.session_state['selected_season'] = season

# ── Tier text colors (readable on white bg) ──
TIER_COLORS = {
    'T1': '#c0392b',
    'T2': '#d35400',
    'T3': '#7f8c8d',
    'T4': '#bdc3c7',
}

# ── Trajectory display (simple text arrows, not emoji) ──
TRAJ_DISPLAY = {
    'BREAKOUT': ('▲▲', '#d35400', '700'),
    'UP':       ('▲', '#27ae60', '600'),
    'STABLE':   ('–', '#95a5a6', '400'),
    'DOWN':     ('▼', '#c0392b', '600'),
}

# ── Pagination controls ──
ROWS_OPTIONS = [25, 50, 100, 200]
total_players = len(sorted_df)

if 'lb_page' not in st.session_state:
    st.session_state['lb_page'] = 1

pc_label, pc_r, pc_1, pc_2, pc_info, pc_3, pc_4 = st.columns([0.55, 0.55, 0.35, 0.35, 1.5, 0.35, 0.35])
with pc_label:
    st.markdown(
        '<p style="font-size:12px;color:#6b7280;margin-top:10px;white-space:nowrap;">Rows per page:</p>',
        unsafe_allow_html=True,
    )
with pc_r:
    rows_per_page = st.selectbox("Rows", ROWS_OPTIONS, index=1, key="rows_per_page",
                                  label_visibility="collapsed")

total_pages = max(1, (total_players + rows_per_page - 1) // rows_per_page)
page = st.session_state['lb_page']
if page > total_pages:
    page = total_pages
    st.session_state['lb_page'] = page

start_display = (page - 1) * rows_per_page + 1
end_display = min(page * rows_per_page, total_players)

with pc_1:
    if st.button("First", key="pg_first", disabled=(page <= 1), use_container_width=True):
        st.session_state['lb_page'] = 1
        st.rerun()
with pc_2:
    if st.button("Prev", key="pg_prev", disabled=(page <= 1), use_container_width=True):
        st.session_state['lb_page'] = max(1, page - 1)
        st.rerun()
with pc_info:
    st.markdown(
        f'<p style="font-size:13px;color:#1f2937;font-weight:600;text-align:center;margin-top:8px;">'
        f'Page {page} of {total_pages}'
        f'<span style="font-size:11px;color:#6b7280;font-weight:400;"> &nbsp;&mdash;&nbsp; '
        f'{start_display}&ndash;{end_display} of {total_players:,}</span></p>',
        unsafe_allow_html=True,
    )
with pc_3:
    if st.button("Next", key="pg_next", disabled=(page >= total_pages), use_container_width=True):
        st.session_state['lb_page'] = min(total_pages, page + 1)
        st.rerun()
with pc_4:
    if st.button("Last", key="pg_last", disabled=(page >= total_pages), use_container_width=True):
        st.session_state['lb_page'] = total_pages
        st.rerun()

start_idx = (page - 1) * rows_per_page
page_df = sorted_df.iloc[start_idx:start_idx + rows_per_page]

# ── Flags legend ──
st.markdown(
    '<p style="font-size:10px;color:#9ca3af;margin:4px 0 2px 0;padding:0;line-height:1.4;">'
    '\U0001f680 Breakout &nbsp;&nbsp; \U0001f48e Hidden Gem &nbsp;&nbsp; '
    '\U0001f4c9 Regression &nbsp;&nbsp; \U0001f504 Portal Value &nbsp;&nbsp; '
    '\U0001f396\ufe0f Experienced'
    '</p>',
    unsafe_allow_html=True,
)

# ── Build PFF-style HTML table ──
rows_html = []
for rank_idx, (_, row) in enumerate(page_df.iterrows(), start=start_idx + 1):
    pos = row.get('position', '--')
    tier = row.get('tier', 'T4')
    tier_color = TIER_COLORS.get(tier, '#bbb')

    name = row.get('name', '?')
    school = row.get('school', '--')
    pid = row.get('player_id', 0)

    cg = float(row['core_grade']) if pd.notna(row.get('core_grade')) else 0
    out = float(row['output_score']) if pd.notna(row.get('output_score')) else 0
    av = row.get('adjusted_value', 0)
    mv = row.get('market_value', 0)
    alpha = row.get('opportunity_score', 0)

    # Grade color — PFF-style: small colored square + dark text number
    def _grade_color(val):
        if val >= 90: return '#1e8449'
        if val >= 80: return '#2874a6'
        if val >= 70: return '#b7950b'
        if val >= 60: return '#ca6f1e'
        return '#c0392b'

    grade_sq = _grade_color(cg)
    out_sq = _grade_color(out)

    # Alpha — professional, subtle styling
    alpha_val = int(float(alpha)) if pd.notna(alpha) else 0
    if alpha_val >= 1000:
        alpha_html = f'<span style="color:#1e8449;font-size:11px;font-weight:600;font-family:Inter,sans-serif;">+{fmt_money(abs(alpha_val))}</span>'
    elif alpha_val <= -1000:
        alpha_html = f'<span style="color:#c0392b;font-size:11px;font-weight:600;font-family:Inter,sans-serif;">-{fmt_money(abs(alpha_val))}</span>'
    else:
        alpha_html = f'<span style="color:#95a5a6;font-size:11px;font-family:Inter,sans-serif;">—</span>'

    # Trajectory
    traj = row.get('trajectory_flag', 'STABLE') or 'STABLE'
    traj_icon, traj_color, traj_weight = TRAJ_DISPLAY.get(traj, ('➡', '#888', '600'))
    traj_html = f'<span style="color:{traj_color};font-weight:{traj_weight};">{traj_icon}</span>'

    # Flags (small icons)
    flags_raw = row.get('flags', '[]')
    try:
        flag_list = json.loads(flags_raw) if isinstance(flags_raw, str) else (flags_raw if isinstance(flags_raw, list) else [])
    except (json.JSONDecodeError, TypeError):
        flag_list = []
    flag_icons = ''.join(
        f'<span title="{FLAG_CONFIG[f]["label"]}" style="cursor:help;">{FLAG_CONFIG[f]["icon"]}</span>'
        for f in flag_list if f in FLAG_CONFIG
    )

    rows_html.append(
        f'<tr data-pid="{pid}">'
        f'<td style="text-align:center;font-size:10px;color:#9ca3af;">{rank_idx}</td>'
        f'<td style="text-align:left;"><a class="player-link" href="?pid={pid}" target="_self" style="font-weight:600;font-size:11px;">{name}</a></td>'
        f'<td style="text-align:left;font-size:9px;color:#6b7280;text-transform:uppercase;letter-spacing:.03em;">{school}</td>'
        f'<td style="text-align:center;font-size:10px;color:#6b7280;">{pos}</td>'
        f'<td style="text-align:center;color:{tier_color};font-weight:700;font-size:10px;">{tier}</td>'
        f'<td style="text-align:right;"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:{grade_sq};margin-right:4px;vertical-align:middle;"></span><span style="font-size:11px;font-weight:600;color:#1f2937;">{cg:.1f}</span></td>'
        f'<td style="text-align:right;"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:{out_sq};margin-right:4px;vertical-align:middle;"></span><span style="font-size:11px;font-weight:600;color:#1f2937;">{out:.1f}</span></td>'
        f'<td style="text-align:center;font-size:11px;">{traj_html}</td>'
        f'<td style="text-align:right;font-size:10px;color:#374151;">{fmt_money(av)}</td>'
        f'<td style="text-align:right;font-size:10px;color:#6b7280;">{fmt_money(mv) if pd.notna(mv) else "–"}</td>'
        f'<td style="text-align:right;">{alpha_html}</td>'
        f'<td style="text-align:center;font-size:11px;letter-spacing:1px;">{flag_icons}</td>'
        f'</tr>'
    )

# Table header — clickable sort links
def _sort_header(label, col_key, align='left'):
    """Build a clickable header that sorts by this column."""
    if col_key not in SORTABLE_COLUMNS:
        return label
    # Show arrow if this is the active sort
    if col_key == sort_col:
        arrow = ' ▲' if sort_ascending else ' ▼'
        next_dir = 'asc' if not sort_ascending else 'desc'
        color = '#E8390E'
    else:
        arrow = ''
        next_dir = 'desc' if not SORTABLE_COLUMNS[col_key] else 'asc'
        color = '#ffffff'
    return (
        f'<a href="?sort={col_key}&dir={next_dir}" target="_self" '
        f'style="color:{color};text-decoration:none;cursor:pointer;font-weight:700;" '
        f'title="Sort by {label}">{label}{arrow}</a>'
    )

table_html = (
    '<div class="pff-table-wrap" style="overflow-x:auto; -webkit-overflow-scrolling:touch;">'
    '<table class="pff-table" style="table-layout:fixed;width:100%;">'
    '<colgroup>'
    '<col style="width:3%;">'     # #
    '<col style="width:15%;">'    # Player
    '<col style="width:10%;">'    # School
    '<col style="width:5%;">'     # Pos
    '<col style="width:4%;">'     # Tier
    '<col style="width:8%;">'     # Grade
    '<col style="width:8%;">'     # Output
    '<col style="width:5%;">'     # Trend
    '<col style="width:10%;">'    # Value
    '<col style="width:10%;">'    # Mkt Value
    '<col style="width:10%;">'    # Alpha
    '<col style="width:6%;">'     # Flags
    '</colgroup>'
    '<thead><tr>'
    f'<th style="text-align:center;" title="Rank position">#</th>'
    f'<th style="text-align:left;" title="Player name">{_sort_header("Player", "name")}</th>'
    f'<th style="text-align:left;" title="College/University">{_sort_header("School", "school")}</th>'
    f'<th style="text-align:center;" title="Position group">Pos</th>'
    f'<th style="text-align:center;" title="Tier: T1 (elite) → T4 (depth)">{_sort_header("Tier", "tier")}</th>'
    f'<th style="text-align:right;" title="PFF Core Grade (0–100 scale)">{_sort_header("Grade", "core_grade")}</th>'
    f'<th style="text-align:right;" title="Percentile rank within position (0–100)">{_sort_header("Output", "output_score")}</th>'
    f'<th style="text-align:center;" title="Season-over-season trajectory">Trend</th>'
    f'<th style="text-align:right;" title="What production justifies — based on output, visibility, and conference">{_sort_header("Value", "adjusted_value")}</th>'
    f'<th style="text-align:right;" title="What the NIL market actually pays">{_sort_header("Mkt Value", "market_value")}</th>'
    f'<th style="text-align:right;" title="Value minus Market — positive = undervalued (Moneyball pick)">{_sort_header("Alpha", "opportunity_score")}</th>'
    f'<th style="text-align:center;" title="Breakout, Hidden Gem, Regression, Portal Value, Experienced">Flags</th>'
    '</tr></thead>'
    '<tbody>' + ''.join(rows_html) + '</tbody>'
    '</table>'
    '</div>'
)

st.markdown(table_html, unsafe_allow_html=True)

# JavaScript to handle player link clicks → navigate to player card
nav_js = """
<script>
document.addEventListener('click', function(e) {
    var link = e.target.closest('.player-link');
    if (link) {
        e.preventDefault();
        var href = link.getAttribute('href');
        var pid = new URLSearchParams(href.replace('?','')).get('pid');
        if (pid) {
            var url = new URL(window.location);
            url.pathname = url.pathname.replace(/\\/[^\\/]*$/, '/player_card');
            url.searchParams.set('pid', pid);
            window.location.href = url.toString();
        }
    }
});
</script>
"""
st.markdown(nav_js, unsafe_allow_html=True)

# ── Clickable player navigation (Streamlit buttons as fallback) ──
# Handle query param navigation
qp = st.query_params
if 'pid' in qp:
    try:
        pid = int(qp['pid'])
        st.session_state['selected_player_id'] = pid
        st.query_params.clear()
        st.switch_page("pages/02_player_card.py")
    except (ValueError, TypeError):
        pass

# ── CSV Export ──
view_name = view.split("—")[0].strip() if "—" in view else view
export_leaderboard_csv(sorted_df, view_name, season)

# ── Sidebar: Player Search ──
st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Search")
search = st.sidebar.text_input("Search by name", placeholder="e.g. Jaxson Dart")

if search and len(search) >= 2:
    matches = df[df['name'].str.contains(search, case=False, na=False)].head(10)
    if not matches.empty:
        for _, row in matches.iterrows():
            pid = row['player_id']
            name = row['name']
            pos = row['position']
            school = row['school']
            if st.sidebar.button(f"{name} ({pos}, {school})", key=f"search_{pid}"):
                st.session_state['selected_player_id'] = pid
                st.switch_page("pages/02_player_card.py")
    else:
        st.sidebar.info("No matches found.")

# ── OPPONENT SCOUTING REPORT ──
st.markdown("---")
with st.expander("🔍 Opponent Scouting Report", expanded=False):
    _schools = sorted(df['school'].dropna().unique().tolist()) if not df.empty else []
    _scout_school = st.selectbox("Select a school to scout", [''] + _schools, key="scout_school")

    if _scout_school:
        _school_df = df[df['school'] == _scout_school].copy()
        if _school_df.empty:
            st.info(f"No scored players found at {_scout_school}.")
        else:
            _school_conf = _school_df['conference'].iloc[0] if 'conference' in _school_df.columns else ''
            _school_mkt = _school_df['market'].iloc[0] if 'market' in _school_df.columns else ''

            st.markdown(
                f'<div style="font-size:20px;font-weight:800;color:#1f2937;margin-bottom:4px;">{_scout_school}</div>'
                f'<div style="font-size:13px;color:#6b7280;margin-bottom:12px;">{_school_conf} · {_school_mkt} · {len(_school_df)} scored players</div>',
                unsafe_allow_html=True,
            )

            # KPI row
            _s_total_val = _school_df['adjusted_value'].fillna(0).sum()
            _s_total_mkt = _school_df['market_value'].fillna(0).sum()
            _s_total_alpha = _s_total_val - _s_total_mkt
            _s_avg_grade = _school_df['core_grade'].mean()
            _s_t1 = len(_school_df[_school_df['tier'] == 'T1'])
            _s_t2 = len(_school_df[_school_df['tier'] == 'T2'])

            _sk1, _sk2, _sk3, _sk4, _sk5 = st.columns(5)
            _sk1.metric("Team Value", fmt_money(_s_total_val))
            _sk2.metric("Market Cost", fmt_money(_s_total_mkt))
            _sk3.metric("Team Alpha", fmt_money(_s_total_alpha))
            _sk4.metric("Avg Grade", f"{_s_avg_grade:.1f}")
            _sk5.metric("T1/T2 Players", f"{_s_t1 + _s_t2}")

            # Position breakdown
            st.markdown("**Roster by Position**")
            _pos_data = []
            for _pos in ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']:
                _pp = _school_df[_school_df['position'] == _pos]
                if _pp.empty:
                    continue
                _pos_data.append({
                    'Pos': _pos,
                    'Count': len(_pp),
                    'Avg Grade': round(_pp['core_grade'].mean(), 1),
                    'Best': _pp['core_grade'].max(),
                    'Total Value': fmt_money(_pp['adjusted_value'].fillna(0).sum()),
                    'Total Mkt': fmt_money(_pp['market_value'].fillna(0).sum()),
                })
            if _pos_data:
                st.dataframe(pd.DataFrame(_pos_data), use_container_width=True, hide_index=True)

            # Vulnerability flags: regression risk + overvalued players
            st.markdown("**Vulnerabilities**")
            _vuln = _school_df.copy()
            _regression = _vuln[_vuln['flags'].apply(
                lambda x: 'REGRESSION_RISK' in (json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else []))
                if pd.notna(x) else False
            )] if 'flags' in _vuln.columns else pd.DataFrame()

            _overvalued = _vuln[_vuln['opportunity_score'].fillna(0) < -100000] if 'opportunity_score' in _vuln.columns else pd.DataFrame()

            if not _regression.empty:
                _reg_names = [f"{r['name']} ({r['position']}, {r.get('tier', '?')})" for _, r in _regression.iterrows()]
                st.warning(f"**Regression Risk:** {', '.join(_reg_names)}")

            if not _overvalued.empty:
                _ov_names = [f"{r['name']} ({r['position']}, {fmt_money(abs(r['opportunity_score']))} overvalued)"
                            for _, r in _overvalued.iterrows()]
                st.error(f"**Significantly Overvalued:** {', '.join(_ov_names[:5])}"
                        + (f" + {len(_ov_names) - 5} more" if len(_ov_names) > 5 else ""))

            if _regression.empty and _overvalued.empty:
                st.success("No major vulnerabilities detected.")

            # Top targets (undervalued players who might portal)
            _undervalued = _vuln[_vuln['opportunity_score'].fillna(0) > 100000] if 'opportunity_score' in _vuln.columns else pd.DataFrame()
            if not _undervalued.empty:
                st.markdown("**Portal Watch** — Undervalued players who may seek better deals")
                for _, _uv in _undervalued.sort_values('opportunity_score', ascending=False).head(5).iterrows():
                    st.markdown(
                        f"- **{_uv['name']}** ({_uv['position']}, {_uv.get('tier', '?')}) — "
                        f"Value {fmt_money(_uv['adjusted_value'])} vs Mkt {fmt_money(_uv['market_value'])} "
                        f"(**+{fmt_money(_uv['opportunity_score'])} alpha**)"
                    )

# ── CONFERENCE BENCHMARKING ──
with st.expander("📊 Conference Benchmarking", expanded=False):
    if df.empty:
        st.info("No data available.")
    else:
        _conf_list = sorted(df['conference'].dropna().unique().tolist())
        _bench_data = []
        for _conf in _conf_list:
            _cdf = df[df['conference'] == _conf]
            _schools_in_conf = _cdf['school'].nunique()
            _total_mkt = _cdf['market_value'].fillna(0).sum()
            _avg_mkt_per_school = _total_mkt / _schools_in_conf if _schools_in_conf else 0
            _avg_grade = _cdf['core_grade'].mean()
            _t1_count = len(_cdf[_cdf['tier'] == 'T1'])
            _total_alpha = _cdf['adjusted_value'].fillna(0).sum() - _total_mkt
            _bench_data.append({
                'Conference': _conf,
                'Schools': _schools_in_conf,
                'Players': len(_cdf),
                'Avg Grade': round(float(_avg_grade), 1) if pd.notna(_avg_grade) else 0,
                'T1 Players': _t1_count,
                'Avg Spend/School': int(_avg_mkt_per_school),
                'Total Alpha': int(_total_alpha),
            })

        _bench_df = pd.DataFrame(_bench_data).sort_values('Avg Spend/School', ascending=False)

        # Chart
        _chart_df = _bench_df.set_index('Conference')[['Avg Spend/School']].copy()
        _chart_df = _chart_df / 1000
        st.bar_chart(_chart_df, use_container_width=True)
        st.caption("Average NIL Market Cost per school ($K)")

        # Format for display
        _display_bench = _bench_df.copy()
        _display_bench['Avg Spend/School'] = _display_bench['Avg Spend/School'].apply(lambda x: fmt_money(x))
        _display_bench['Total Alpha'] = _display_bench['Total Alpha'].apply(
            lambda x: f"+{fmt_money(abs(x))}" if x > 0 else f"-{fmt_money(abs(x))}" if x < 0 else "$0")
        st.dataframe(_display_bench, use_container_width=True, hide_index=True)

        st.caption("Conferences ranked by average NIL market cost per school. "
                   "Positive Alpha = conference players are undervalued on average.")

# ── HISTORICAL MARKET RATE TRACKER (D4) ──
with st.expander("📈 Historical Market Rate Tracker", expanded=False):
    with st.spinner(""):
        _mkt_hist = load_market_rate_history([2022, 2023, 2024, 2025])

    if _mkt_hist.empty:
        st.info("Not enough multi-season data for market rate tracking.")
    else:
        _available_seasons = sorted(_mkt_hist['season'].unique())
        st.markdown(
            f'<div style="font-size:13px;color:#6b7280;margin-bottom:12px;">'
            f'Tracking NIL market rates across {len(_available_seasons)} seasons '
            f'({_available_seasons[0]}–{_available_seasons[-1]}). '
            f'Identify which positions are inflating fastest and where the market is cooling.</div>',
            unsafe_allow_html=True,
        )

        # Position group selector
        _all_positions = sorted(_mkt_hist['position'].unique().tolist())
        _off_positions = [p for p in ['QB', 'RB', 'WR', 'TE', 'OT', 'IOL'] if p in _all_positions]
        _def_positions = [p for p in ['EDGE', 'IDL', 'LB', 'CB', 'S'] if p in _all_positions]

        _pos_group = st.radio(
            "Position Group", ["All", "Offense", "Defense"],
            horizontal=True, key="mkt_hist_group", label_visibility="collapsed",
        )
        if _pos_group == "Offense":
            _selected_pos = _off_positions
        elif _pos_group == "Defense":
            _selected_pos = _def_positions
        else:
            _selected_pos = _all_positions

        _filtered_hist = _mkt_hist[_mkt_hist['position'].isin(_selected_pos)]

        # --- Average Value by Position (line chart) ---
        st.markdown("**Average Player Value by Position**")
        _pivot_val = _filtered_hist.pivot(index='season', columns='position', values='avg_value')
        _pivot_val = _pivot_val.fillna(0) / 1000
        _pivot_val.index = _pivot_val.index.astype(str)
        st.line_chart(_pivot_val, use_container_width=True)
        st.caption("Average production value per eligible player ($K)")

        # --- Average Market Rate by Position (line chart) ---
        st.markdown("**Average Market Rate by Position**")
        _pivot_mkt = _filtered_hist.pivot(index='season', columns='position', values='avg_mkt')
        _pivot_mkt = _pivot_mkt.fillna(0) / 1000
        _pivot_mkt.index = _pivot_mkt.index.astype(str)
        st.line_chart(_pivot_mkt, use_container_width=True)
        st.caption("Average NIL market cost per eligible player ($K)")

        # --- Top-10 Average (elite tier pricing) ---
        st.markdown("**Top-10 Average Value by Position** — Elite tier pricing")
        _pivot_top = _filtered_hist.pivot(index='season', columns='position', values='top10_avg_value')
        _pivot_top = _pivot_top.fillna(0) / 1000
        _pivot_top.index = _pivot_top.index.astype(str)
        st.line_chart(_pivot_top, use_container_width=True)
        st.caption("Average value of the top 10 players per position ($K)")

        # --- YoY Change Table ---
        st.markdown("**Year-over-Year Market Rate Changes**")

        if len(_available_seasons) >= 2:
            _latest = _available_seasons[-1]
            _prior = _available_seasons[-2]

            _yoy_rows = []
            for _pos in _selected_pos:
                _cur = _filtered_hist[(_filtered_hist['position'] == _pos) & (_filtered_hist['season'] == _latest)]
                _prev = _filtered_hist[(_filtered_hist['position'] == _pos) & (_filtered_hist['season'] == _prior)]
                if _cur.empty or _prev.empty:
                    continue
                _cur_mkt = float(_cur['avg_mkt'].iloc[0])
                _prev_mkt = float(_prev['avg_mkt'].iloc[0])
                _cur_val = float(_cur['avg_value'].iloc[0])
                _prev_val = float(_prev['avg_value'].iloc[0])
                _pct_mkt = ((_cur_mkt - _prev_mkt) / _prev_mkt * 100) if _prev_mkt > 0 else 0
                _pct_val = ((_cur_val - _prev_val) / _prev_val * 100) if _prev_val > 0 else 0
                _count = int(_cur['player_count'].iloc[0])

                if _pct_mkt > 15:
                    _signal = "🔴 Inflating"
                elif _pct_mkt > 5:
                    _signal = "🟠 Rising"
                elif _pct_mkt > -5:
                    _signal = "🟢 Stable"
                elif _pct_mkt > -15:
                    _signal = "🔵 Cooling"
                else:
                    _signal = "⚪ Deflating"

                _yoy_rows.append({
                    'Position': _pos,
                    f'Avg Mkt {_prior}': fmt_money(int(_prev_mkt)),
                    f'Avg Mkt {_latest}': fmt_money(int(_cur_mkt)),
                    'Mkt Δ%': f"{_pct_mkt:+.1f}%",
                    f'Avg Value {_latest}': fmt_money(int(_cur_val)),
                    'Value Δ%': f"{_pct_val:+.1f}%",
                    'Signal': _signal,
                    'Players': _count,
                })

            if _yoy_rows:
                _yoy_df = pd.DataFrame(_yoy_rows)
                st.dataframe(_yoy_df, use_container_width=True, hide_index=True)

                # Summary insights
                _inflating = [r['Position'] for r in _yoy_rows if 'Inflating' in r['Signal']]
                _cooling = [r['Position'] for r in _yoy_rows if 'Cooling' in r['Signal'] or 'Deflating' in r['Signal']]

                if _inflating:
                    st.warning(f"**Fastest inflating:** {', '.join(_inflating)} — budget more aggressively for these positions")
                if _cooling:
                    st.success(f"**Market cooling:** {', '.join(_cooling)} — potential buying opportunities")
        else:
            st.info("Need at least 2 seasons of data for YoY comparison.")

# ── Footer ──
render_footer()
