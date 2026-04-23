# NILytics — User Guide

A practical reference for college football staff using NILytics to evaluate players, build rosters, and make NIL decisions.

> **TL;DR** — NILytics is a Moneyball operating system for college football. It combines PFF production data with NIL market intelligence to answer: *Who's worth what? Where's the alpha? Who can we afford?*

---

## Table of Contents

1. [Core Concepts — The Six Numbers](#core-concepts)
2. [Page-by-Page Reference](#pages)
3. [Common Workflows](#workflows)
4. [Features & Features](#features)
5. [Glossary](#glossary)
6. [FAQ](#faq)

---

<a name="core-concepts"></a>

## 1. Core Concepts — The Six Numbers

Every page in the app reuses these. Understand them once and the rest of the app reads itself.

### Core Grade (0–100)
How well is this player playing right now? A weighted composite of their position-specific PFF grades. Higher = better tape. Ignores playing time entirely — think *quality per snap*.

### Output Score (0–100 percentile)
How dominant is this player vs. position peers? Combines Core Grade with snap volume. An 88 Core on 800 snaps outranks an 88 Core on 80. This is what drives Tier.

### Tier (T1–T4)
Position-within-market rank, **frozen from the 2021–2025 eligible pool**. NIL dollars *never* move tier lines. T1 = elite, T4 = depth. Tier is evaluated per position × per market (P4/G6/FCS), so a T1 FCS EDGE and a T1 P4 EDGE are not the same player.

### Value ($)
What the player's production is *worth* per our model. Starts from the tier-specific NIL range for their position + market, then adjusts for snap volume, conference premium, and experience bonuses.

### Market Value ($)
What the NIL market *actually pays* for that production. Derived from industry NIL ranges (ESPN / On3 / CBS). SEC and Big Ten carry a 20% premium, high-visibility (output ≥ 95) carries a 25% premium.

### Alpha ($) = Value − Market
The edge.
- **Positive (green)** = bargain. Production value exceeds NIL market price.
- **Negative (red)** = market overpays. Common for star SEC/Big Ten QBs (bidding wars push them to a $6.25M cap).
- **Alpha is a pricing signal, not a quality signal.** A −$2.7M alpha on Diego Pavia means the market overpays for him, not that he's a bad player.

---

<a name="pages"></a>

## 2. Page-by-Page Reference

### 🏠 Dashboard (`/`)
Landing page. Four stat cards with tooltips (hover any number), a "New here?" banner that links to the Getting Started page, and quick-launch cards to Leaderboard / Player Card / GM Mode / Methodology.

### 📊 Leaderboard (`/leaderboard`)
The power table — 3,600+ eligibility-scored players for the season.

**Three view modes:**
- **Scouting — Best Players** — ranked by Core Grade. "Who's playing the best football right now?"
- **Moneyball — Best Deals** — ranked by Alpha descending. "Who's most undervalued?"
- **Market — Highest Value** — ranked by production Value. "Whose production justifies the biggest NIL number?"

**Features:**
- **Flag filters** — Breakout 🚀 / Hidden Gem 💎 / Regression 📉 / Portal Value 🔄 / Experience Premium 🎖️. Legend sits above the table with hover tooltips.
- **Conference-Adjusted Alpha toggle** — recomputes alpha as `player_alpha − (position+conference peer median)`. Shows who's undervalued *within their conference tier* — exactly what you need when competing against a specific market level's typical spend.
- **"Transferred this season" filter** — 5,566 real transfers detected by diffing per-season team affiliation across PFF stats tables. Rows get a 🔁 icon with "From X" tooltip.
- **Sidebar filters** — Position, Market (P4/G6/FCS), Conference, Tier. Each is a dedicated dropdown (search bar only matches name/school to keep mental model clean).
- **Click any school** — opens that school's Team page with full roster.
- **Click any player name** — opens their Player Card.

### 🏈 Player Search / Player Card (`/player_card`)
Drill-down on any individual player.

**What you see:**
- Hero header with Tier pill + TRANSFER badge (if applicable)
- Five metric cards: Core Grade, Output Score, Value, Mkt Value, Alpha (with undervalued/overvalued banner)
- Position-specific stats panel (passing stats for QB, receiving for WR, etc.)
- Season-by-Season Breakdown table (career-to-date)
- Career Trend charts
- "What Drives This Score" — plain-English explanation of the grade composition
- Comparable Players — same position, similar Output Score
- 🔁 Transfer Portal Timeline — chronological moves with LATEST pill on the newest
- Contract Projection — remaining eligibility
- My Notes & Tags — personal scouting notes with status (Watching / Targeting / In Negotiation / Committed / Signed / Passed)

**Actions:**
- ➕ Add to Compare (queues into the Compare page's 4-player slot)
- ➕ Add to GM Roster (persists to DB, auto-saves)
- ➕ Add to Recruiting Class
- ➕ Add to My Board

### 🏫 Teams (`/team`)
School-level roster view. **NEW as of Round 6.**

**What you see:**
- School header banner with conference + market badge
- KPI strip: Total Rostered / Avg Core Grade / Total Value / Total Market Cost / Team Alpha
- Positional Breakdown grid — every position, count + avg grade + alpha
- Top Performers + Moneyball Picks side-by-side
- **Full Roster** — every PFF-tracked player (50–80 bodies, not just the 25 who clear eligibility). Depth players show provisional PFF grades marked with `*`.

**Key controls:**
- **Roster Mode toggle** — Full Roster (as-played) vs. Projected N+1 Returners (auto-hides anyone with 4+ seasons of stats + any you've manually 🚪-marked).
- 🚪 **Per-player departure** — click to remove a graduating/transferred player from your projection. DB-persisted per user+school+season.
- ↩️ **Departed panel** — always-visible expander above the roster lets you Restore any accidental 🚪.
- ⚔️ **Compare vs another team** — expandable section for gameweek scouting. Position-by-position grade head-to-head with color-coded winner cells + win tally.

**Row chips:**
- `~FR` / `~SO` / `~JR` / `~SR` / `~GS` — estimated class year (seasons of stats heuristic; `class_year` is NULL in our DB).
- 🔁 — transferred in this season.
- DEPTH — below eligibility threshold but played.
- ⏰ LIKELY GRAD — 4+ seasons on tape.
- `T2*` — provisional tier (raw PFF grade, not eligibility-certified).

### 🎯 GM Mode (`/gm_mode`)
The roster builder. Build a full roster within a NIL budget.

**Budget presets:** Elite P4 ($30M) / Competitive P4 ($20M) / Mid-Tier P4 ($12M) / G6 Contender ($6M) / G6 Standard ($3M) / FCS ($1.5M) / Custom.

**Player Market (always visible):**
- Name search, Position/Tier/Conference/School filters.
- **Saved Filter Profiles** — save current filter set under a name (e.g., "Vandy EDGE Search") and one-click Apply later. DB-persisted per user.
- "Affordable only" — hides players above your remaining budget.
- "Portal Targets" — G6/FCS T1/T2 with output ≥ 65 + anyone with the PORTAL_VALUE flag.
- Flag filter buttons for the same flags as Leaderboard.
- 8 sort options (Output, Value, Mkt, Alpha best/worst, Core Grade, etc.).

**Five views (split into VIEW | ANALYZE):**

| View | Purpose |
|------|---------|
| 📋 **List View** | Text table of your current roster |
| 📋 **Depth Chart** | Visual formation (Pro/Spread/4-3/Nickel) with empty slots |
| 📊 **Roster Analysis** | 85-man template gap analysis + positional spending dashboard |
| 📊 **What-If** | Simulate inflation, trades, budget shifts |
| 📊 **Optimizer** | Auto-fill positions given budget + strategy (Maximize Output / Maximize Alpha / Balanced) |

**Persistence:**
- **Auto-saves** your roster on every add/remove/clear. DB-backed, survives refresh + tab close.
- Named roster slots (💾 save current under a name) for multiple what-if rosters.

### 📋 Recruiting (`/recruiting`)
**Three tabs:**
- **Class Overview** — your current recruiting class with budget tracker.
- **Prospect Pool** — ESPN 300 recruits (2025 & 2026 classes) with projected valuations.
- **Portal Targets** — all undervalued (alpha > 0) players, filterable by position/tier/cost/search.

### 🚨 Alerts (`/alerts`)
Auto-detected roster events across seasons. Groups by player, shows all alert types per player.

**Alert types:**
- **Breakout** — Core Grade jumped ≥ 10 pts season-over-season.
- **Tier Promotion** — Moved up a tier.
- **Tier Demotion** — Moved down a tier.
- **Market Spike** — Market rate up 50%+.
- **Overvalued** — Alpha < −$200K.
- **Declining + Expensive** — Trending DOWN with > $100K market rate.

**Controls:**
- Season / Alert Type / Severity (high/medium/info/all) / Position filters.
- Per-row actions: 👤 **Card** (jump to player card), ✕ (dismiss this player for the session).
- Bulk: "Dismiss N INFO alerts" + "Restore dismissed" escape hatch.

### 🔬 Lab (`/lab`)
Experiment with Core Grade weight composition. Slide different stat categories up/down per position and watch rankings shift in real-time. Read-only by default — your weights don't affect the live scoring unless an admin merges them.

### 📚 Methodology (`/methodology`)
Plain-English explanation of every formula, weight, and threshold in the system. Recommended reading during your first week.

### ⚔️ Compare (`/compare`)
Head-to-head comparison for up to 4 players.

**Features:**
- Player picker (live search over the 2025 leaderboard).
- Header cards with View Card / ◀ Move Left / Remove per player.
- Side-by-Side metric table with green-highlighted best-in-row.
- Alpha color-coded (green = undervalued, red = overvalued).
- "Quick Take" callout: Best Moneyball Pick + Highest Core Grade.
- **🔗 Copy share link** — generates a URL like `/compare?pids=123,456,789` that reconstructs the exact comparison. Sendable to teammates.

### 📌 My Board (`/board`)
Your personal watchlist — every player you've tagged in their Player Card. Filter by status (Watching / Targeting / In Negotiation / Committed / Signed / Passed). Jump back to any card with one click.

### 🚀 Getting Started (`/getting_started`)
Ten-minute guided onboarding — the six numbers, every page at a glance, three end-to-end workflows, FAQ. Linked from the Dashboard's "New here?" banner.

---

<a name="workflows"></a>

## 3. Common Workflows

### Workflow 1: Find a portal target under budget
**Scenario:** Vanderbilt GM, $12M budget, needs an EDGE for 2026.

1. Open **GM Mode**. Budget preset: **Mid-Tier P4 ($12M)**.
2. Under Player Market: filter **Position: EDGE**, check **Portal Targets**, check **Affordable only**, sort by **Alpha (Best Value)**.
3. Type a name under Save (e.g., *"Vandy EDGE Search"*) and hit 💾. Next session, pick from dropdown → Apply → filters restore instantly.
4. Scan top candidates. Click any name → Player Card. Check **Transfer Portal Timeline** and **What Drives This Score**.
5. On two finalists, click **Add to Compare**. Navigate to **Compare** page. Read the Quick Take summary.
6. On the winner, click **Add to GM Roster**. Budget and alpha update live. Roster is auto-saved to DB.

### Workflow 2: Project next year's roster
**Scenario:** It's spring — project who's actually returning next year.

1. Open **Teams** → pick your school. Switch mode to **Projected 2026 Returners**.
2. Scan Positional Breakdown. Empty groups show "No scored returners" — these are your biggest gaps. ⏰ LIKELY GRAD chips call out seniors about to leave.
3. For anyone you KNOW is leaving (transfer declaration, draft), click 🚪 on their row. DB-persisted. The 🚪 Departed panel at top has ↩️ Restore if you misclick.
4. KPIs auto-recompute based on returners only — this is your baseline. Fill gaps via GM Mode (portal) + Recruiting (HS class).

### Workflow 3: Gameweek opponent scout
**Scenario:** You play Kentucky Saturday — where are they vulnerable?

1. Open **Teams** → pick your school. Expand **⚔️ Compare vs another team**. Pick **KENTUCKY**.
2. Position-by-position grade table colors cells green (you win) or red (opponent wins). Summary tally at top tells you who holds the edge.
3. Click red-highlighted top players → Player Card → check career trend. Rising or declining? Injury history?
4. Open **Alerts** → filter by their school + position → see any tier moves or market spikes on their roster.

### Workflow 4: Monitor a recruiting target
**Scenario:** You're watching a G6 QB who might enter the portal.

1. Open his **Player Card**. Click **My Notes & Tags**. Set status to **Watching**, add scouting notes.
2. He appears on your **My Board** page, filtered under "Watching."
3. If you get an **Alert** about him (e.g., Market Spike), the alert card shows "Your tracked status: Watching" and you get a one-click 👤 Card jump.
4. When he enters the portal, update status to **Targeting** and use **GM Mode** to budget.

---

<a name="features"></a>

## 4. Features Cheat Sheet

### Flags (appear as icons + column tooltips)
| Icon | Flag | Definition |
|------|------|------------|
| 🚀 | Breakout | Young player trending up with undervalued alpha |
| 💎 | Hidden Gem | Low recruit rating, elite production, undervalued by market |
| 📉 | Regression | Declining production OR unsustainable breakout spike |
| 🔄 | Portal Value | G6/FCS elite who'd be a bargain at P4 |
| 🎖️ | Experience Premium | Multi-year P4 starter at premium position |
| ↩️ | Transfer In | Same-season move detected from per-season PFF team_name diff |

### Color Coding
- **Green** — positive alpha, you win a matchup, bargain
- **Red** — negative alpha, opponent wins, overpaying
- **Amber/Yellow** — caution (e.g., ⏰ LIKELY GRAD, historical data warning)
- **Purple** — PORTAL_VALUE flag
- **Blue** — INFO severity on alerts, FR/SO class

### Persistence Model
Everything user-specific is keyed by **user_email** + Supabase tables:

| Data | Table | Scope |
|------|-------|-------|
| GM Roster (auto-save) | `saved_rosters` (`name='__autosave__'`) | 1 per user |
| GM Roster (named) | `saved_rosters` | Many per user |
| Team departures | `team_departures` | Per user × school × season |
| GM filter profiles | `saved_filter_profiles` | Per user × page |
| Player notes | `player_notes` | Per user × player |

In current trial mode (`AUTH_DISABLED=True`), all testers share `test@nilytics.com` → all see shared state. Flip auth on to silo per user.

---

<a name="glossary"></a>

## 5. Glossary

| Term | Definition |
|------|------------|
| Alpha | Value minus Market. Positive = bargain. Negative = overpaid. |
| Core Grade | PFF weighted composite of position-specific grades. |
| Output Score | Percentile rank within position group (0–100). |
| Tier | T1–T4, frozen from 2021–2025 eligible pool. Position × market. |
| Value | What production is worth per NILytics model. |
| Market Value | What NIL market actually pays (industry rate × premiums). |
| Conference-Adjusted Alpha | Player alpha minus position+conference peer median. |
| P4 / G6 / FCS | Power 4 / Group of 6 / Football Championship Subdivision. |
| Eligibility-scored | Player met snap threshold (`snaps_proxy ≥ 300` OR PFF rating ≥ 79.9). |
| Depth | Played but didn't hit threshold. Shows provisional grade. |
| Provisional grade (`*`) | Raw PFF grade for depth players; approximation only. |
| PFF | Pro Football Focus — play-by-play grading service our raw data comes from. |
| `snaps_proxy` | Best available snap count across all stat tables. |
| Seasons played | Count of distinct seasons with any PFF stats — proxy for class year. |

---

<a name="faq"></a>

## 6. FAQ

**Q: Why is Diego Pavia's Alpha −$2.7M? He's a Heisman finalist.**
A: Alpha measures *pricing*, not quality. The NIL market caps top SEC QBs around $6.25M. Our production model values his tape around $3.55M (T1 P4 QB standard NIL range). The $2.7M gap is what SEC bidding inflates. Real number for acquisition math, zero reflection of ability.

**Q: Only 6 "High-Alpha" players on the Dashboard — bug?**
A: No. High-Alpha = alpha > +$500K, an intentionally high bar. Use **Leaderboard → Moneyball** view to browse all undervalued players.

**Q: What's a `T2*` tier (with asterisk)?**
A: Provisional tier from raw PFF grade for a depth player. Directional only — use for backup/rotation evaluation, not official ranking.

**Q: How often is data updated?**
A: 2018–2025 seasons are in DB. PFF drops are processed via `scoring/run_scoring.py → signals/run_signals.py`. Ask admin for last run date.

**Q: My GM Roster / departures / filter profiles disappeared.**
A: In current trial mode (`AUTH_DISABLED=True`), all testers share one account and may see each other's state. Real auth silos per user.

**Q: Transfer data — is it real portal data?**
A: Detected indirectly — 5,566 moves inferred by diffing per-season `team_name` across PFF stats. We don't track live portal entry status (Exploring / Committed / Signed) yet; use **My Notes & Tags** to record your own.

**Q: Why can't I see stats for freshmen / walk-ons / deep backups?**
A: If they took a PFF-tracked snap, they're on the Team page's Full Roster with a provisional grade (`T2*` / `73.1*`). If they never took a snap, they're not in the DB.

**Q: Can I export?**
A: Yes — GM Roster exports to CSV (button on List View). Recruiting class exports too.

**Q: How do I add a new user?**
A: Admin-only via the Admin page (currently locked). When auth is enabled, admins invite by email via the `app_admins` table.

---

## Support

- **Questions about the data?** → Methodology page
- **Bug reports / feature requests** → GitHub issues on the repo
- **Not loading / 404** → Hit "Manage app → Reboot" on Streamlit Cloud, or contact the admin

---

*Last updated: this file lives at `USER_GUIDE.md` in the repo root and is the canonical long-form reference. For a quick tour, use the in-app **Getting Started** page instead.*
