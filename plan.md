# NILytics — Build Plan

## Project Overview
Private, invite-only college football player valuation platform.
Moneyball for NIL: identify undervalued players by comparing computed Player Value against estimated Market Value.

**Stack:** Python + Supabase + Streamlit + GitHub
**Supabase Project:** `wnrarukpqncmklforald` (NILytics, us-west-2, active)

---

## Data Inventory

### PFF CSV Files (already in project root)
5 file types × 8 seasons (2018–2025). No season column — season inferred from file naming:

| Suffix | Season | Verification Player |
|--------|--------|-------------------|
| `(7)` | 2018 | Gardner Minshew, Wash State |
| `(6)` | 2019 | Anthony Gordon, Wash State |
| `(5)` | 2020 | Kyle Trask, Florida |
| `(4)` | 2021 | Bailey Zappe, W Kentucky |
| `(3)` | 2022 | Will Rogers, Miss State |
| `(2)` | 2023 | Michael Penix Jr, Washington |
| `(1)` | 2024 | Kyle McCord, Syracuse |
| *(none)* | 2025 | Nick Minicucci, Delaware |

**File types and approximate row counts per season:**
- `passing_summary` — ~500 rows (QBs + some skill players)
- `receiving_summary` — ~2,200 rows (WR/TE/RB/all positions)
- `rushing_summary` — ~1,600 rows (RB/QB/all positions)
- `offense_blocking` — ~5,500 rows (OL/TE/all positions)
- `defense_summary` — ~5,000 rows (EDGE/IDL/LB/CB/S/all positions)

**Note:** Defense files are numbered (2)–(8) + base (no (1) file). Year mapping may differ by 1 — will verify during import.

**PFF Position Code Mapping:**
| PFF Code | NILytics Position |
|----------|------------------|
| QB | QB |
| HB | RB |
| WR | WR |
| TE | TE |
| T | OT |
| C, G | IOL |
| ED | EDGE |
| DI | IDL |
| LB | LB |
| CB | CB |
| S | S |
| FB, K, P, LS | Excluded (no valuation model) |

### Key Column Mapping (PFF → NILytics)

**Passing (QB Core Grade inputs):**
- `grades_pass` → pass grade (65%)
- `grades_run` → rush grade (20%)
- `btt_rate` → BTT% (10%)
- `twp_rate` → TWP% inverted (5%)
- `passing_snaps` → snap proxy for QB

**Receiving (WR/TE Core Grade inputs):**
- `grades_pass_route` → route grade (WR 60%, TE receiving 40%)
- `grades_hands_drop` → drop grade (WR 20%)
- `yprr` → yards per route run (explosiveness)
- `yards_after_catch` / `yards_after_catch_per_reception` → YAC
- `wide_snaps` + `slot_snaps` + `inline_snaps` → snap proxy components
- `grades_pass_block` → TE blocking component

**Rushing (RB Core Grade inputs):**
- `grades_run` → rush grade (55%)
- `grades_pass_route` → receiving grade (25%, from receiving file)
- `grades_pass_block` → pass block grade (10%)
- `attempts` → volume (5%)
- `elusive_rating` / `breakaway_percent` → explosiveness (5%)
- Snap proxy: receiving snaps + blocking snaps + rush attempts

**Blocking (OT/IOL Core Grade inputs):**
- `grades_pass_block` → pass block (OT 50%, IOL 45%)
- `grades_run_block` → run block (OT 40%, IOL 45%)
- `penalties` → penalties inverted (5%)
- `snap_counts_lt` → LT snap volume (OT 5%)
- `snap_counts_block` → snap proxy for OL

**Defense (EDGE/IDL/LB/CB/S Core Grade inputs):**
- `grades_pass_rush_defense` → pass rush grade
- `grades_run_defense` → run defense grade
- `grades_coverage_defense` → coverage grade
- `grades_tackle` → tackling grade
- `total_pressures`, `hurries`, `sacks` → pass rush production
- `interceptions`, `pass_break_ups` → ball production
- `missed_tackle_rate` → reliability (inverted)
- `catch_rate` → coverage efficiency (inverted for CB)
- `snap_counts_run_defense` + `snap_counts_pass_rush` + `snap_counts_coverage` → snap proxy

---

## Phase 1 — Database Foundation

### 1.1 Create Supabase Tables
Execute SQL migrations via Supabase MCP to create:

**`players`** — Master player table
```
player_id (PFF ID, PK), name, position, school, conference, market (P4/G6/FCS), class_year, created_at
```

**`player_seasons`** — Raw PFF metrics per season
```
player_id (FK), season, team, position, snaps_proxy, + all raw PFF columns organized by prefix:
  pass__* (passing metrics)
  rec__* (receiving metrics)
  rush__* (rushing metrics)
  blk__* (blocking metrics)
  def__* (defense metrics)
PK: (player_id, season)
```

**`player_scores`** — Computed scores
```
player_id (FK), season, core_grade, output_score, tier, base_value, adjusted_value, model_version, computed_at
PK: (player_id, season, model_version)
```

**`player_recruit_rating`** — Recruiting data
```
pff_player_id (FK), industry_rating, star_rating, composite_score
```

**`portal_history`** — Transfer tracking
```
player_id (FK), season, from_school, to_school, portal_date
```

**`nil_market_estimates`** — External market valuations
```
player_id (FK), season, estimated_market_value, source, confidence_band, scraped_at
```

**`alpha_signals`** — The Moneyball output
```
player_id (FK), season, player_value, market_value, opportunity_score, trajectory_flag, flags (JSONB), computed_at
```

**`conference_teams`** — Reference table for market classification
```
team_name, conference, market (P4/G6/FCS)
```

### 1.2 CSV Import Scripts
Python scripts to:
1. Rename/organize CSVs into `data/raw/{season}/{type}.csv`
2. Parse each CSV, map PFF columns to prefixed `player_seasons` columns
3. Deduplicate players across files (same `player_id` appears in multiple file types per season)
4. Merge all file types for each player-season into one `player_seasons` row
5. Populate `players` table with distinct player records
6. Assign `market` (P4/G6/FCS) using `conference_teams` reference

### 1.3 Validation
- Row counts per season match expectations
- No null `player_id` values
- Spot-check known players (e.g., McCord 2024 passing stats)
- All 11 position groups have data across all seasons

**Deliverables:** All tables created, all 8 seasons imported, validation passing.

---

## Phase 2 — Scoring Engine

### 2.1 Snap Proxy Computation
Module: `scoring/snap_proxy.py`
- QB: `pass__passing_snaps`
- RB/WR: `rec__wide_snaps + rec__slot_snaps + rec__inline_snaps + blk__snap_counts_run_block + rush__attempts`
- TE: `rec__wide_snaps + rec__slot_snaps + rec__inline_snaps + blk__snap_counts_run_block + blk__snap_counts_pass_block`
- OL: `blk__snap_counts_block`
- Defense: `def__snap_counts_run_defense + def__snap_counts_pass_rush + def__snap_counts_coverage`

### 2.2 Core Grade Computation
Module: `scoring/core_grade.py`
- One function per position group using weights from brief
- Normalize each component to 0–100 scale before weighting
- Handle missing data gracefully (some players won't have all file types)

### 2.3 Output Score (Percentile Ranking)
Module: `scoring/output_score.py`
- Rank each player's core_grade within their position group for that season
- Convert to 0–100 percentile score
- This is the ONLY input for tiering

### 2.4 Tier Assignment
Module: `scoring/tiers.py`
- Use frozen global cutoffs (computed from 2021–2025 eligible pool)
- Eligibility: `snaps_proxy >= 300 OR industry_rating >= 79.9`
- Pre-set cutoffs for RB, WR, TE, OT, IOL
- Compute cutoffs for QB, EDGE, IDL, LB, CB, S on first run from eligible pool, then freeze
- T1/T2/T3/T4 assignment — money NEVER affects tiers

### 2.5 Base Value Calculation
Module: `scoring/valuation.py`
- Look up NIL range by (position, market, tier)
- Interpolate within range based on output_score percentile within tier
- P4 ranges from brief; G6 = ~50% of P4; FCS = ~25% of P4 (derived from QB ratios)

### 2.6 Adjusted Value Calculation
Module: `scoring/adjustments.py`
- Snap penalty: snaps < 300 → -25% NIL value
- Experience bonuses (non-QB): +$50K/season at T1 w/ ≥330 snaps; +$150K/season at T2+ w/ ≥330 snaps
- Experience bonuses (QB): +$500K/prior T2 season; +$1.5M/prior T1 season
- Position-specific bonuses:
  - EDGE: 10+ sacks → +$250K
  - RB: 1200+ scrimmage yards → +$150K; 10+ TDs → +$100K
  - CB: catch rate ≤45% → +$100K; ≥5 INTs → +$75K
  - S: elite deviation (T1 + coverage ≥90 + 800+ snaps + 3 INTs or 8 PBUs) → +$200K–$350K
  - SEC/B1G CB or S → +$100K conference bonus
  - Nickel CB (slot snap majority) → T1 ineligible, -$125K penalty
- FCS bonuses = 50% of standard bonus values

### 2.7 Write to `player_scores`
- Compute all scores for all player-seasons
- Write with `model_version` tag for reproducibility

**Deliverables:** All scoring modules working, scores computed for 2018–2025, spot-checked against manual calculations.

---

## Phase 3 — Alpha Signal Layer

### 3.1 Market Value Scraper
Module: `data/scrapers/on3_scraper.py`
- Scrape On3 NIL valuations
- Store in `nil_market_estimates` with source and confidence band
- Fallback: manual CSV import for initial dataset from provided articles

### 3.2 Market Knowledge Base
Baseline market ranges from research articles (ESPN, CBS Sports, On3):
- QB portal elite: $1M–$2M+
- WR high-end portal: $1M–$2M; average: $500K–$800K
- RB high-end portal: $400K–$900K
- OT elite portal: $800K–$1.2M+
- DL elite: $500K–$1M
- CB top: $250K–$400K
- P4 average: ~$75K; all-division average: ~$40K
- SEC/B1G premium confirmed across sources

### 3.3 Opportunity Score
Module: `signals/opportunity.py`
```
opportunity_score = adjusted_value - market_value_estimate
```
Positive = undervalued player.

### 3.4 Auto-Flag Logic
Module: `signals/flags.py`
| Flag | Criteria |
|------|---------|
| BREAKOUT_CANDIDATE | 3+ star recruit, soph/junior, output_score trending up, below-market value |
| HIDDEN_GEM | Low recruit rank, high output_score, below-market value |
| REGRESSION_RISK | High market value, declining output_score trend |
| PORTAL_VALUE | High output_score at G6/FCS, likely undervalued if moved to P4 |
| EXPERIENCE_PREMIUM | Multi-year P4 starter at premium position |

### 3.5 Trajectory Analysis
- Compare output_score across seasons for same player
- Flag: UP (improving), DOWN (declining), STABLE, BREAKOUT (>15pt jump)

### 3.6 Write to `alpha_signals`

**Deliverables:** Market estimates loaded, opportunity scores computed, all flags assigned, trajectory arrows working.

---

## Phase 4 — Streamlit UI

### 4.1 App Structure
```
app/
  streamlit_app.py          # Entry point
  pages/
    01_leaderboard.py       # Master leaderboard (3 views)
    02_player_card.py       # Baseball card detail page
    03_methodology.py       # Plain English explanations
  components/
    card_front.py           # Baseball card front
    card_back.py            # Baseball card back (drill-down)
    filters.py              # Shared filter sidebar
    charts.py               # Trend line charts
  styles/
    theme.css               # Dark ESPN/PFF aesthetic
```

### 4.2 Master Leaderboard
Three toggle views:
1. **Scouting View** — sorted by `output_score` DESC
2. **Moneyball View** — sorted by `opportunity_score` DESC
3. **Market View** — sorted by `adjusted_value` DESC

Filters: position, conference, market (P4/G6/FCS), season, tier, class year
All columns sortable. Position filter dynamically changes visible stat columns.

### 4.3 Baseball Card — Front
- Player photo placeholder
- Name, position, school, class year
- Three bold badges: Core Grade / Player Value / Market Value
- Opportunity Score with UP/DOWN/NEUTRAL indicator
- 1–2 headline position-specific stats
- Trajectory arrow

### 4.4 Baseball Card — Back (Drill-Down)
- Year-over-year stat table (all seasons)
- Trend line chart: Core Grade, Player Value, Market Value over career
- Score breakdown in plain English
- Portal/transfer history
- Recruiting origin + over/underperformance vs expectation
- Comparable player comps (same position, similar output_score range)

### 4.5 Dark Theme CSS
- Dark backgrounds (#1a1a2e or similar)
- Bold, high-contrast text
- Color-coded tiers: T1=gold, T2=silver, T3=bronze, T4=gray
- Opportunity Score: green (undervalued), red (overvalued), gray (neutral)
- ESPN/PFF-inspired aesthetic

### 4.6 Methodology Page
Plain English explanation of:
- What Core Grade measures and doesn't
- How Output Score works (percentile, not absolute)
- Why tiers are frozen and never change based on money
- How Base Value and Adjusted Value are calculated
- What Opportunity Score means
- What each flag means
- Data sources and limitations

**Deliverables:** Fully functional Streamlit app with all three views, player cards, filters, and methodology page.

---

## Phase 5 — Auth & Sharing

### 5.1 Supabase Auth
- Email-based invite-only authentication
- No public signup — admin sends invite links
- Row-level security on all tables
- Session management via Streamlit

### 5.2 CSV Export
- Export leaderboard views as CSV
- Export individual player cards as CSV/PDF

### 5.3 Admin Panel
- Invite new users
- Trigger score recalculation
- Upload new season data

**Deliverables:** Auth working, invite flow tested, exports functional.

---

## Project Structure
```
NILytics/
  data/
    raw/                    # Organized CSVs by season
      2018/ 2019/ ... 2025/
    scrapers/
      on3_scraper.py
    import_csv.py           # Main CSV import script
    conference_teams.py     # P4/G6/FCS reference data
  scoring/
    snap_proxy.py
    core_grade.py
    output_score.py
    tiers.py
    valuation.py
    adjustments.py
    run_all.py              # Orchestrator
  signals/
    opportunity.py
    flags.py
    trajectory.py
    run_all.py
  app/
    streamlit_app.py
    pages/
    components/
    styles/
  config/
    cutoffs.json            # Frozen tier cutoffs
    value_ranges.json       # NIL value ranges by position/market/tier
    position_weights.json   # Core grade weights
  tests/
    test_scoring.py
    test_signals.py
    test_import.py
  .env                      # Supabase credentials (never committed)
  .gitignore
  requirements.txt
  plan.md
```

---

## Execution Rules
1. Build phase by phase — no skipping ahead
2. Test after each phase before moving to next
3. Spot-check against known players at every stage
4. `model_version` tag on all computed outputs for reproducibility
5. Money never affects tiers — enforce this in code and tests
6. All credentials in `.env` only
