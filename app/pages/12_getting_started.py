"""
NILytics — Getting Started
Guided tour: what this platform does, the 6 numbers that matter,
and three workflows that cover 80% of a GM's job.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Getting Started", page_icon="🏈", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

# Page-specific CSS
st.markdown("""
<style>
.gs-hero {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    color: #ffffff;
    padding: 28px 32px;
    border-radius: 14px;
    margin-bottom: 20px;
}
.gs-hero h1 {
    font-size: 32px;
    font-weight: 800;
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
}
.gs-hero p {
    font-size: 15px;
    color: #d1d5db;
    margin: 0;
    max-width: 720px;
    line-height: 1.6;
}
.gs-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px 18px;
    height: 100%;
}
.gs-card h3 {
    font-size: 14px;
    font-weight: 800;
    color: #111827;
    margin: 0 0 6px 0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.gs-card p {
    font-size: 13px;
    color: #4b5563;
    line-height: 1.5;
    margin: 0;
}
.gs-metric {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-left: 4px solid #E8390E;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin-bottom: 10px;
}
.gs-metric .name {
    font-size: 11px;
    font-weight: 800;
    color: #E8390E;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.gs-metric .def {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
    margin-top: 2px;
}
.gs-metric .desc {
    font-size: 12px;
    color: #6b7280;
    margin-top: 2px;
    line-height: 1.5;
}
.gs-step {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    padding: 12px 0;
    border-bottom: 1px solid #f3f4f6;
}
.gs-step:last-child { border-bottom: none; }
.gs-step .num {
    flex: 0 0 32px;
    height: 32px;
    width: 32px;
    border-radius: 50%;
    background: #E8390E;
    color: #ffffff;
    font-weight: 800;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.gs-step .body {
    flex: 1;
    font-size: 13px;
    color: #374151;
    line-height: 1.55;
}
.gs-step .body b { color: #111827; }
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='getting_started')
user = check_auth()
render_user_sidebar()

# ── HERO ──
st.markdown(
    '<div class="gs-hero">'
    '<h1>NILytics — a Moneyball operating system for college football</h1>'
    '<p>This guide gets you productive in 10 minutes. Skim the six numbers, pick a workflow that '
    'matches a real decision you need to make this week, and use the deep-link buttons to jump '
    'straight into the tool. Every page has tooltips — hover anything you want more detail on.</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── 6 NUMBERS THAT MATTER ──
st.markdown("## The six numbers that matter")
st.caption("Every page reuses these. Understand them once and the rest of the app reads itself.")

_m1, _m2 = st.columns(2)
with _m1:
    st.markdown(
        '<div class="gs-metric">'
        '<div class="name">CORE GRADE</div>'
        '<div class="def">How well is this player playing right now? (0–100 PFF scale)</div>'
        '<div class="desc">A weighted composite of their position-specific PFF grades. '
        'Higher = better tape. Ignores playing time entirely — think quality per snap.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gs-metric">'
        '<div class="name">OUTPUT SCORE</div>'
        '<div class="def">How dominant is this player vs. their position peers? (0–100 percentile)</div>'
        '<div class="desc">Combines Core Grade with volume. An 88 Core on 800 snaps outranks an '
        '88 Core on 80. This is what drives Tier.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gs-metric">'
        '<div class="name">TIER (T1–T4)</div>'
        '<div class="def">Position rank within their market level, frozen 2021–2025.</div>'
        '<div class="desc">T1 = elite, T4 = depth. <b>NIL dollars never move tier lines.</b> '
        'Tier is evaluated per position × per market (P4/G6/FCS), so a T1 FCS EDGE and a T1 '
        'P4 EDGE are not the same player.</div></div>',
        unsafe_allow_html=True,
    )

with _m2:
    st.markdown(
        '<div class="gs-metric">'
        '<div class="name">VALUE ($)</div>'
        '<div class="def">What their production is <i>worth</i> per our model.</div>'
        '<div class="desc">Starts from the tier-specific NIL range for their position + market, '
        'then adjusts for snap volume, conference premium, and experience bonuses.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gs-metric">'
        '<div class="name">MARKET VALUE ($)</div>'
        '<div class="def">What the NIL market <i>actually pays</i> for that production.</div>'
        '<div class="desc">Derived from industry NIL ranges (ESPN / On3 / CBS). SEC and Big Ten '
        'carry a 20% premium, visibility (output ≥ 95) carries a 25% premium. This is what '
        'you\'d realistically have to pay to acquire them.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gs-metric" style="border-left-color:#16a34a;">'
        '<div class="name" style="color:#16a34a;">ALPHA ($)</div>'
        '<div class="def">Value − Market. The edge.</div>'
        '<div class="desc"><b style="color:#16a34a;">Positive (green)</b> = bargain, '
        'production exceeds price. <b style="color:#dc2626;">Negative (red)</b> = NIL market '
        'overpays — common for star SEC/B1G QBs. <b>Alpha is a pricing signal, not a quality '
        'signal.</b> A -$2.7M Alpha on Pavia means the market overpays, not that he\'s bad.</div></div>',
        unsafe_allow_html=True,
    )

# ── THE PAGES ──
st.markdown("---")
st.markdown("## The 12 pages at a glance")
st.caption("One line on what each page does and when you'd open it.")

_PAGES = [
    ('📊 Leaderboard', 'pages/01_leaderboard.py',
     "The power table. 3,600+ eligibility-scored players, three views (Scouting / Moneyball / Market), flag filters, Conference-Adjusted Alpha toggle. Start here for broad scans."),
    ('🏈 Player Search', 'pages/02_player_card.py',
     "Drill into a single player: stats, trends, comps, transfer timeline, your notes & tags, Add-to-Compare / GM Roster / My Board."),
    ('🏫 Teams', 'pages/10_team.py',
     "Every PFF-tracked player on one team (50–80 bodies, not just starters). Positional breakdown, Projected Returners mode, ⚔️ Compare vs another team."),
    ('🎯 GM Mode', 'pages/04_gm_mode.py',
     "The roster builder. Budget presets, Player Market with savable Filter Profiles, List / Depth Chart / Roster Analysis / What-If / Optimizer views. Auto-saves your roster."),
    ('📋 Recruiting', 'pages/07_recruiting.py',
     "ESPN-300 high-school prospect pool + Portal Targets tab. Pair with GM Mode for 2026+ class building."),
    ('🚨 Alerts', 'pages/08_alerts.py',
     "Auto-detected roster events — tier movers, breakouts, market spikes, overvalued flags. Per-row 👤 Card jump and bulk-dismiss."),
    ('🔬 Lab', 'pages/06_lab.py',
     "Interactive weight-tuning for Core Grade. Slide stat categories up/down and watch rankings shift."),
    ('📚 Methodology', 'pages/03_methodology.py',
     "Plain-English explanation of every formula, weight, and threshold. Keep this open during your first week."),
    ('⚔️ Compare', 'pages/11_compare.py',
     "Head-to-head for up to 4 players. Best-in-row highlights. Copy-link to share a comparison URL with teammates."),
    ('📌 My Board', 'pages/09_board.py',
     "Your personal watchlist. Every player you've tagged Watching / Targeting / In Negotiation / Committed / etc."),
    ('🏠 Dashboard', 'streamlit_app.py',
     "Landing page with top-level stats and quick-launch cards. Click any number for a tooltip."),
]

_cols = st.columns(2)
for i, (label, path, desc) in enumerate(_PAGES):
    with _cols[i % 2]:
        st.markdown(
            f'<div class="gs-card">'
            f'<h3>{label}</h3>'
            f'<p>{desc}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if path != 'streamlit_app.py':
            if st.button(f"Open {label.split(' ', 1)[1] if ' ' in label else label} →",
                         key=f"open_{path}", use_container_width=True):
                st.switch_page(path)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── WORKFLOWS ──
st.markdown("---")
st.markdown("## Three workflows that cover 80% of GM work")
st.caption("Each is a copy-paste of what a real user did. Follow along on the actual app.")

wf_tabs = st.tabs([
    "🎯 Find a portal target under budget",
    "🗓 Project next year's roster",
    "⚔️ Gameweek opponent scout",
])

with wf_tabs[0]:
    st.markdown("##### Scenario: Vanderbilt GM, $12M budget, needs an EDGE for 2026")
    st.markdown(
        '<div class="gs-step"><div class="num">1</div><div class="body">'
        'Open <b>GM Mode</b>. Budget preset: <b>Mid-Tier P4 ($12M)</b>. '
        'Under Player Market, filter <b>Position: EDGE</b>, check <b>Portal Targets</b>, '
        'check <b>Affordable only</b>, sort by <b>Alpha (Best Value)</b>.</div></div>'
        '<div class="gs-step"><div class="num">2</div><div class="body">'
        'Type a name under <b>Save</b> like <i>"Vandy EDGE Search"</i> and hit 💾. Next session, '
        'pick it from the saved-filters dropdown → Apply → everything returns instantly.</div></div>'
        '<div class="gs-step"><div class="num">3</div><div class="body">'
        'Scan the top 3 candidates. On any row, click the player name → Player Card. '
        'Check the <b>Transfer Portal Timeline</b> (are they a portal regular?) and '
        '<b>What Drives This Score</b>.</div></div>'
        '<div class="gs-step"><div class="num">4</div><div class="body">'
        'On two candidates you like, click <b>Add to Compare</b>. Navigate to <b>⚔️ Compare</b> and '
        'head-to-head them. Best Moneyball Pick + Highest Grade are called out in the Quick Take.</div></div>'
        '<div class="gs-step"><div class="num">5</div><div class="body">'
        'Back to their Player Card → <b>Add to GM Roster</b>. You get a live budget update + alpha readout. '
        'Roster is auto-saved to DB — survives refresh, tab close, device switch.</div></div>',
        unsafe_allow_html=True,
    )

with wf_tabs[1]:
    st.markdown("##### Scenario: It's spring — project who's actually returning next year")
    st.markdown(
        '<div class="gs-step"><div class="num">1</div><div class="body">'
        'Open <b>Teams</b> → pick your school. Switch the mode toggle to '
        '<b>Projected 2026 Returners</b>. The page auto-hides anyone with 4+ seasons of stats '
        '(likely graduating).</div></div>'
        '<div class="gs-step"><div class="num">2</div><div class="body">'
        'Scan the Positional Breakdown. Empty position groups show "No scored returners" — '
        'those are your biggest gaps. Flag ⏰ <b>LIKELY GRAD</b> calls out seniors you\'re about to lose.</div></div>'
        '<div class="gs-step"><div class="num">3</div><div class="body">'
        'For anyone you KNOW is leaving (transfer declaration, draft, etc.), click 🚪 on their row. '
        'Saved to DB — the 🚪 Departed panel at the top lets you ↩️ Restore if you misclick.</div></div>'
        '<div class="gs-step"><div class="num">4</div><div class="body">'
        'Your KPI cards (Avg Grade, Team Value, Team Alpha) auto-recompute based on returners only. '
        'This IS your baseline — fill the gaps via GM Mode (portal) + Recruiting (HS class).</div></div>',
        unsafe_allow_html=True,
    )

with wf_tabs[2]:
    st.markdown("##### Scenario: You play Kentucky this Saturday — where are they vulnerable?")
    st.markdown(
        '<div class="gs-step"><div class="num">1</div><div class="body">'
        'Open <b>Teams</b> → pick your school. Expand <b>⚔️ Compare vs another team</b>. Pick <b>KENTUCKY</b>.</div></div>'
        '<div class="gs-step"><div class="num">2</div><div class="body">'
        'The position-by-position grade table colors each cell green (you win) or red (opponent wins), '
        'with each side\'s top player. A summary tally at the top tells you who holds the edge.</div></div>'
        '<div class="gs-step"><div class="num">3</div><div class="body">'
        'Click any of their red-highlighted top players → Player Card → check their career trend. '
        'Rising or declining? Injury history? This informs the game plan.</div></div>'
        '<div class="gs-step"><div class="num">4</div><div class="body">'
        'Bonus: open <b>🚨 Alerts</b>, filter by team / position — any tier moves or market spikes '
        'on their roster? A hot breakout player might be over-indexed in the box score.</div></div>',
        unsafe_allow_html=True,
    )

# ── READING ALPHA ──
st.markdown("---")
st.markdown("## The one gotcha: how to read Alpha")
_alpha_left, _alpha_right = st.columns(2)
with _alpha_left:
    st.markdown(
        '<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:14px 18px;">'
        '<div style="font-size:11px;font-weight:800;color:#16a34a;text-transform:uppercase;letter-spacing:0.08em;">Green Alpha (+)</div>'
        '<div style="font-size:15px;font-weight:700;color:#111827;margin-top:4px;">Bargain</div>'
        '<div style="font-size:13px;color:#14532d;margin-top:6px;line-height:1.5;">'
        'Production value exceeds NIL market price. You\'re getting more snaps of quality football than '
        'you pay for. Example: a G6 T1 EDGE worth $944K that market pays $624K = <b>+$320K alpha</b>.'
        '</div></div>',
        unsafe_allow_html=True,
    )
with _alpha_right:
    st.markdown(
        '<div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:14px 18px;">'
        '<div style="font-size:11px;font-weight:800;color:#dc2626;text-transform:uppercase;letter-spacing:0.08em;">Red Alpha (−)</div>'
        '<div style="font-size:15px;font-weight:700;color:#111827;margin-top:4px;">Overpriced — not bad</div>'
        '<div style="font-size:13px;color:#7f1d1d;margin-top:6px;line-height:1.5;">'
        'Market pays more than production warrants. Common for star SEC / Big Ten QBs '
        '(bidding wars push to a $6.25M cap). '
        '<b>Negative alpha ≠ bad player.</b> It means you\'re overpaying, not under-producing.'
        '</div></div>',
        unsafe_allow_html=True,
    )

# ── FAQ ──
st.markdown("---")
st.markdown("## FAQ")

with st.expander("Why is Diego Pavia's Alpha shown as −$2.7M? He's a Heisman finalist."):
    st.markdown(
        "Alpha measures pricing, not quality. The NIL market caps top SEC QBs around **$6.25M**. "
        "Our production model values his tape around **$3.55M** (which is what a T1 P4 QB in the "
        "standard NIL range is worth). The $2.7M gap is what SEC bidding inflates — a real number "
        "for anyone trying to acquire him, but zero reflection of his actual ability."
    )

with st.expander("Only 6 'High-Alpha' players on the Dashboard — is that a bug?"):
    st.markdown(
        "No — it's by design. High-Alpha = players with alpha > **+$500K**, which is an intentionally "
        "high bar (most seasons, only a handful clear it). To browse a wider undervalued pool, open "
        "**Leaderboard → Moneyball — Best Deals** view."
    )

with st.expander("What does a Tier like 'T2*' (with an asterisk) mean?"):
    st.markdown(
        "Asterisks mark **provisional** data for depth players who didn't meet the eligibility "
        "threshold (snaps_proxy ≥ 300 OR PFF rating ≥ 79.9). Their grade is their raw PFF grade "
        "from the biggest stats table they appear in — useful as a directional signal for "
        "rotation/backup evaluation, but not eligibility-certified. Official Tiers use the full v1.1 model."
    )

with st.expander("How often is the data updated?"):
    st.markdown(
        "Seasons 2018–2025 are in the database. PFF drops are processed through our scoring pipeline "
        "(scoring/run_scoring.py → signals/run_signals.py). Re-runs refresh all alpha signals and flags. "
        "Ask your admin when the last run happened if you care about the exact date."
    )

with st.expander("My GM Roster / departures / filter profiles disappeared"):
    st.markdown(
        "They shouldn't — everything is DB-persisted per **user_email**. In the current trial mode "
        "(`AUTH_DISABLED=True`), every tester shares one `test@nilytics.com` account so you may see "
        "another tester's state. When real auth is flipped on, each user gets their own silo."
    )

with st.expander("The transfer history shows a player moved from NEW MEX ST to VANDERBILT — is that from real portal data?"):
    st.markdown(
        "Yes, but detected indirectly. The transfer flag is derived by diffing per-season `team_name` "
        "across all 5 PFF stats tables between consecutive years. It surfaces 5,566 actual moves. "
        "What we DON'T have is live portal-entry status (Exploring / Visiting / Signed) — for that, "
        "use the **My Notes & Tags** feature on a Player Card to record your own tracked status."
    )

# ── FOOTER LINKS ──
st.markdown("---")
_fc1, _fc2, _fc3 = st.columns(3)
with _fc1:
    if st.button("📊 Jump to Leaderboard", use_container_width=True, type="primary"):
        st.switch_page("pages/01_leaderboard.py")
with _fc2:
    if st.button("🎯 Open GM Mode", use_container_width=True, type="primary"):
        st.switch_page("pages/04_gm_mode.py")
with _fc3:
    if st.button("📚 Read Methodology", use_container_width=True):
        st.switch_page("pages/03_methodology.py")

render_footer()
