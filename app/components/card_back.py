"""
NILytics — Baseball Card Back (Drill-Down) Component
"""
import streamlit as st
import pandas as pd
from app.components.charts import career_trend_chart


def render_card_back(player, all_scores_df, all_signals_df, comps_df=None):
    """
    Render the back of the baseball card with detailed stats.
    """
    position = player.get('position', '?')

    # ── Year-over-Year Table ──
    st.markdown('<p class="section-header">Season-by-Season Breakdown</p>', unsafe_allow_html=True)

    if not all_scores_df.empty and not all_signals_df.empty:
        merged = all_scores_df.merge(
            all_signals_df[['season', 'market_value', 'opportunity_score', 'trajectory_flag', 'flags']],
            on='season', how='left'
        ).sort_values('season', ascending=False)

        display_df = merged[['season', 'core_grade', 'output_score', 'tier',
                             'adjusted_value', 'market_value', 'opportunity_score',
                             'trajectory_flag']].copy()
        display_df.columns = ['Season', 'Core Grade', 'Output', 'Tier',
                              'Player Value', 'Market Value', 'Alpha', 'Trend']

        # Fix: format season as plain year string so it doesn't show "2,024"
        display_df['Season'] = display_df['Season'].apply(lambda x: str(int(x)))
        display_df['Player Value'] = display_df['Player Value'].apply(
            lambda x: f"${int(float(x)):,}" if pd.notna(x) else '--'
        )
        display_df['Market Value'] = display_df['Market Value'].apply(
            lambda x: f"${int(float(x)):,}" if pd.notna(x) else '--'
        )
        display_df['Alpha'] = display_df['Alpha'].apply(
            lambda x: f"${int(float(x)):+,}" if pd.notna(x) else '--'
        )
        display_df['Core Grade'] = display_df['Core Grade'].apply(
            lambda x: f"{float(x):.1f}" if pd.notna(x) else '--'
        )
        display_df['Output'] = display_df['Output'].apply(
            lambda x: f"{float(x):.1f}" if pd.notna(x) else '--'
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)
    elif not all_scores_df.empty:
        # Show scores even without signals
        display_df = all_scores_df[['season', 'core_grade', 'output_score', 'tier',
                                     'adjusted_value']].copy()
        display_df.columns = ['Season', 'Core Grade', 'Output', 'Tier', 'Player Value']
        display_df['Season'] = display_df['Season'].apply(lambda x: str(int(x)))
        display_df['Core Grade'] = display_df['Core Grade'].apply(
            lambda x: f"{float(x):.1f}" if pd.notna(x) else '--'
        )
        display_df['Output'] = display_df['Output'].apply(
            lambda x: f"{float(x):.1f}" if pd.notna(x) else '--'
        )
        display_df['Player Value'] = display_df['Player Value'].apply(
            lambda x: f"${int(float(x)):,}" if pd.notna(x) else '--'
        )
        display_df = display_df.sort_values('Season', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No historical data available.")

    # ── Career Trend Charts ──
    if len(all_scores_df) >= 2:
        st.markdown("---")
        st.markdown('<p class="section-header">Career Trends</p>', unsafe_allow_html=True)
        career_trend_chart(all_scores_df, all_signals_df)

    # ── Score Breakdown ──
    st.markdown("---")
    st.markdown('<p class="section-header">What Drives This Score</p>', unsafe_allow_html=True)
    _render_score_explanation(player, all_scores_df, all_signals_df)

    # ── Comparable Players ──
    if comps_df is not None and not comps_df.empty:
        st.markdown("---")
        st.markdown('<p class="section-header">Comparable Players</p>', unsafe_allow_html=True)
        st.caption(f"Players at {position} with similar Output Score — click to view")

        # Header row
        hc = st.columns([2.5, 1.5, 0.8, 0.6, 1, 0.5])
        for col, label in zip(hc, ['Player', 'School', 'Output', 'Tier', 'Value', '']):
            col.markdown(f"<span style='font-size:11px;font-weight:700;text-transform:uppercase;"
                         f"letter-spacing:0.08em;color:#6b7280;'>{label}</span>",
                         unsafe_allow_html=True)

        for _, comp_row in comps_df.iterrows():
            rc = st.columns([2.5, 1.5, 0.8, 0.6, 1, 0.5])
            rc[0].markdown(f"**{comp_row.get('name', '?')}**")
            rc[1].markdown(f"{comp_row.get('school', '--')}")
            rc[2].markdown(f"{float(comp_row.get('output_score', 0)):.1f}")
            rc[3].markdown(f"{comp_row.get('tier', '--')}")
            rc[4].markdown(f"${int(float(comp_row.get('adjusted_value', 0))):,}")
            comp_pid = comp_row.get('player_id', 0)
            if rc[5].button("→", key=f"comp_{comp_pid}"):
                st.session_state['selected_player_id'] = comp_pid
                st.rerun()


def _render_score_explanation(player, scores_df, signals_df):
    """Plain English breakdown of what drives the score."""
    pos = player.get('position', '?')

    weight_descriptions = {
        'QB': "65% passing grade, 20% rushing, 10% big-time throws, 5% turnover-worthy plays",
        'RB': "55% rushing grade, 25% receiving, 10% pass blocking, 5% volume, 5% explosiveness",
        'WR': "60% route running, 20% drop rate, 5% volume, 15% explosiveness (YPRR/YAC/MTF)",
        'TE': "40% receiving, 40% blocking, 10% volume, 10% explosiveness",
        'OT': "50% pass blocking, 40% run blocking, 5% penalties, 5% snap volume",
        'IOL': "45% pass blocking, 45% run blocking, 5% penalties, 5% volume",
        'EDGE': "50% pass rush, 25% total pressures, 15% hurries, 10% sacks",
        'IDL': "45% pass rush, 35% run defense, 10% volume, 5% penalties, 5% disruption",
        'LB': "35% coverage, 35% run defense, 15% pass rush, 10% volume, 5% reliability",
        'CB': "50% coverage, 15% disruption, 15% reliability, 10% volume, 10% explosiveness",
        'S': "35% coverage, 30% tackling, 15% ball production, 10% volume, 10% reliability",
    }

    weights = weight_descriptions.get(pos, "Position-specific weighted PFF grades")

    # Use structured layout instead of raw markdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Core Grade**")
        st.caption(f"Weighted composite of PFF position grades: {weights}")

        st.markdown(f"**Output Score**")
        st.caption("Percentile rank (0-100) among all eligible players at the same position. "
                    "Higher = better relative production.")

    with col2:
        st.markdown(f"**Player Value**")
        st.caption(f"Starts from the tier-based NIL range for {player.get('market', 'P4')} {pos}, "
                    "then adjusts for snap penalties, experience bonuses, and position-specific bonuses.")

        st.markdown(f"**Market Value**")
        st.caption("Estimates what the NIL market perceives this player is worth, factoring in "
                    "conference visibility, name recognition, and market tendencies.")

    # Alpha insight
    if not signals_df.empty:
        latest = signals_df.sort_values('season').iloc[-1]
        opp = int(float(latest.get('opportunity_score', 0)))
        if opp > 100000:
            st.success(f"This player appears **significantly undervalued** by ${abs(opp):,}. "
                       "The market hasn't caught up to their production.")
        elif opp > 0:
            st.info(f"This player is **slightly undervalued** by ${abs(opp):,}.")
        elif opp < -100000:
            st.warning(f"This player appears **overvalued** by ${abs(opp):,}. "
                       "Market price exceeds production-based value.")
        else:
            st.info("This player is **fairly valued** — market price aligns with production value.")
