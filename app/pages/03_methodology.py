"""
NILytics — Methodology Page
Plain English explanation of every number.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

st.set_page_config(page_title="NILytics — Methodology", page_icon="🏈", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inject fonts after CSS
inject_fonts()

# Light-mode table and card styles for this page
st.markdown("""
<style>
/* Methodology page light-mode table overrides */
.method-section table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 14px;
}
.method-section table th {
    background: #3a4553;
    color: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 10px 14px;
    text-align: left;
    font-weight: 700;
}
.method-section table td {
    background: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    padding: 8px 14px;
}
.method-section table tr:hover td {
    background: #f9fafb;
}
.method-section h3 {
    color: #1f2937;
    margin-top: 0;
}
.method-section p, .method-section li {
    color: #6b7280;
    font-size: 14px;
    line-height: 1.7;
}
.method-section strong {
    color: #1f2937;
}
.method-section em {
    color: #6b7280;
}
.method-section code {
    background: #f3f4f6;
    color: #E8390E;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
}
.method-section h4 {
    color: #1f2937;
    margin-top: 16px;
}
</style>
""", unsafe_allow_html=True)

render_logo_and_nav(active_page='methodology')
user = check_auth()
render_user_sidebar()

# ── Sidebar Table of Contents ──
st.sidebar.markdown("### Contents")
st.sidebar.markdown("""
- [Core Grade](#1-core-grade)
- [Output Score](#2-output-score-0-100)
- [Tiers](#3-tier-t1-t2-t3-t4)
- [Value](#4-base-value-adjusted-value)
- [Market Value](#5-market-value-estimated)
- [Moneyball Signal](#the-moneyball-signal)
- [Data Sources](#data-sources-limitations)
""")

# Card wrapper open/close helpers
CARD_OPEN = '<div class="method-section" style="background:#ffffff; border:1px solid #e5e7eb; border-left:4px solid #E8390E; border-radius:0 8px 8px 0; padding:24px; margin:16px 0;">'
CARD_CLOSE = '</div>'

with st.spinner(""):

    # ── Intro ──
    st.markdown(f"""
{CARD_OPEN}
<h2 style="color:#1f2937; margin-top:0;">The Five-Layer System</h2>
<p style="color:#6b7280; font-size:15px; line-height:1.7;">
NILytics scores every FBS and FCS player through five layers, each building on the last.
No single number tells the whole story — the power is in the combination.
</p>
{CARD_CLOSE}
""", unsafe_allow_html=True)

    # ── Section 1: Core Grade ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### 1. Core Grade

**What it is:** A weighted composite of PFF position-specific grades that answers one question:
*How good is this player at his job?*

Every position has a custom formula. We don't grade a quarterback the same way we grade a
cornerback. The weights reflect what actually matters for that position:

| Position | Formula |
|----------|---------|
| **QB** | 60% passing grade, 10% rushing, 10% big-time throw %, 20% turnover-worthy play % (inverted) |
| **RB** | 60% rushing, 15% receiving, 5% pass blocking, 5% volume, 15% explosiveness |
| **WR** | 65% route running, 5% drop rate (inverted), 10% volume, 20% explosiveness |
| **TE** | 55% receiving, 35% blocking, 10% volume, 10% explosiveness |
| **OT** | 50% pass blocking, 40% run blocking, 5% penalties (inverted), 5% LT snap volume |
| **IOL** | 45% pass blocking, 45% run blocking, 5% penalties (inverted), 5% volume |
| **EDGE** | 50% pass rush, 25% total pressures, 15% hurries, 10% sacks |
| **IDL** | 40% pass rush, 40% run defense, 10% volume, 5% penalties, 5% disruption |
| **LB** | 25% coverage, 40% run defense, 15% pass rush, 10% volume, 10% reliability |
| **CB** | 50% coverage, 15% disruption, 15% reliability, 10% volume, 10% explosiveness |
| **S** | 35% coverage, 30% tackling, 15% ball production, 10% volume, 10% reliability |

**What it doesn't measure:** Core Grade doesn't account for team context, strength of schedule,
or how good the players around you are. A great guard on a bad line still gets a good Core Grade.
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

    # ── Section 2: Output Score ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### 2. Output Score (0-100)

**What it is:** A percentile ranking of Core Grade among all eligible players at the same position
in the same season. A score of 85 means "better than 85% of eligible players at this position
this year."

**Formula:** `Output Score = percentile(Core Grade)` within position and season.

**Why percentile?** Because raw grades aren't comparable across positions. A 75.0 grade means
something very different for a QB than for a cornerback. Percentiles put everyone on the same
scale.

**Who's eligible?** Players must have either:
- 300+ snaps (proves they actually played), OR
- An industry recruiting rating of 79.9+ (recognizes elite prospects with limited snaps)

**Output Score is the ONLY input for tiering.** Nothing else — not money, not market,
not recruiting stars — affects what tier a player lands in.
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

    # ── Section 3: Tiers ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### 3. Tier (T1 / T2 / T3 / T4)

**What it is:** An absolute quality bucket. Tier 1 means elite production. Tier 4 means
replacement-level.

**How cutoffs work:** We computed the Output Score distribution for every eligible player from
2021-2025 (five years of data). The cutoff lines are **frozen** — they never change based on
the current year's data, money, or market conditions.

For example, RB tier cutoffs:
- **T1** >= 86.60 — Elite back (top ~15%)
- **T2** >= 79.80 — Very good (next ~15%)
- **T3** >= 73.30 — Solid starter (next ~15%)
- **T4** < 73.30 — Rotation / depth

**Why freeze tiers?** Because if we recalculated every year, a T1 player in a weak year
would look the same as a T1 in a loaded year. Frozen tiers mean T1 always means the
same level of production, regardless of context.

**Critical rule: Money NEVER affects tiers.** A player doesn't become T1 because he got a
big NIL deal, and he doesn't become T4 because no one offered. Tiers are production only.
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

    # ── Section 4: Base Value & Adjusted Value ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### 4. Base Value & Adjusted Value

**Base Value** is the starting NIL dollar value based on three things:
1. Position (QBs are worth more than punters)
2. Market (P4 schools have bigger NIL budgets than FCS)
3. Tier (T1 players command premium prices)

Each combination has a range (e.g., QB + P4 + T1 = 2.5M-4M). We interpolate within
the range based on Output Score — the better you are within your tier, the higher you sit
in the range.

**Adjusted Value** adds or subtracts from Base Value:

| Adjustment | Rule |
|-----------|------|
| Snap penalty | < 300 snaps: -25% value |
| Experience (non-QB) | +50K per prior T1 season; +150K per prior T2+ season (>=330 snaps) |
| Experience (QB) | +500K per prior T2 season; +1M per prior T1 season (capped at 2M total) |
| EDGE sack bonus | 10+ sacks: +250K |
| RB yard bonus | 1,200+ scrimmage yards: +150K |
| RB TD bonus | 10+ TDs: +100K |
| CB coverage bonus | Catch rate <=45%: +100K |
| CB INT bonus | >=5 INTs: +75K |
| S elite bonus | T1 + coverage >=90 + 800+ snaps + 3 INTs or 8 PBUs: +200K-350K |
| Conference bonus | SEC/B1G CB or S: +100K |
| Nickel CB penalty | Slot snap majority: T1 ineligible, -75K |
| Two-way player | If player has significant stats at a second position, value = higher of the two |
| Value floor | No player valued below 25K (P4/G6) or 10K (FCS) |
| FCS modifier | All bonuses at 50% of standard values |
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

    # ── Section 5: Market Value ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### 5. Market Value (Estimated)

**What it is:** Our best estimate of what the **market** thinks this player is worth —
not what we think he's worth.

The market is driven by visibility, brand recognition, conference prestige, and position
glamour. It systematically **overpays** quarterbacks and skill positions, and **underpays**
offensive linemen and defensive players.

We model this using industry ranges from ESPN, CBS Sports, and On3 reporting, adjusted for:
- Conference premium (SEC/B1G get 20% market inflation)
- Visibility multiplier (high Output Score = more name recognition = higher market price)
- Market noise (+/-10% randomness to reflect real-world deal variance)
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

    # ── The Moneyball Signal ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### The Moneyball Signal

**Opportunity Score = Player Value - Market Value**

**Positive = Undervalued.** Our model says this player is worth more than the market is paying.
This is where the opportunity lives.

**Negative = Overvalued.** The market is paying more than production justifies. Proceed
with caution.

#### Auto-Flags

| Flag | What it means |
|------|--------------|
| **BREAKOUT CANDIDATE** | 3+ star recruit, sophomore or junior, trending up, below market — could explode |
| **HIDDEN GEM** | Low or unknown recruit ranking, high production, below market — the market hasn't noticed yet |
| **REGRESSION RISK** | High market value but declining production — potential overpay |
| **PORTAL VALUE** | High production at G6/FCS, likely undervalued — would be worth much more at a P4 school |
| **EXPERIENCE PREMIUM** | Multi-year P4 starter at a premium position — proven commodity with leadership value |

#### Trajectory

Compares a player's Output Score from season to season:
- **BREAKOUT** — Jumped 15+ points. Something clicked.
- **UP** — Improved 5-15 points. Trending in the right direction.
- **STABLE** — Within +/-5 points. Consistent producer.
- **DOWN** — Dropped 5+ points. Watch for regression.
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

    # ── Data Sources & Limitations ──
    st.markdown(f"""{CARD_OPEN}""", unsafe_allow_html=True)
    st.markdown("""
### Data Sources & Limitations

**Primary data:** PFF grades and stats (2018-2025). PFF is the industry standard for player
evaluation, but their grades are subjective assessments by human graders, not ground truth.

**Market estimates:** Based on reported deal ranges from ESPN, CBS Sports, and On3.
These are estimates — actual NIL deals are often private and the real number may differ.

**What we don't have:**
- Social media following (affects actual NIL deals but not football value)
- Academic eligibility concerns
- Injury history
- Character/leadership intangibles
- Coaching scheme fit

**This is a tool, not a crystal ball.** NILytics identifies where the math suggests
opportunity exists. Human judgment — yours — makes the final call.
""")
    st.markdown(f"""{CARD_CLOSE}""", unsafe_allow_html=True)

# ── Footer ──
render_footer()
