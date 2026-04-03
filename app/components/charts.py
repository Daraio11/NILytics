"""
NILytics — Chart Components
"""
import streamlit as st
import pandas as pd


def career_trend_chart(scores_df: pd.DataFrame, signals_df: pd.DataFrame):
    """
    Render career trend line charts for a player.

    scores_df: from player_scores (season, core_grade, output_score, adjusted_value)
    signals_df: from alpha_signals (season, market_value)
    """
    if scores_df.empty or len(scores_df) < 2:
        return

    df = scores_df.sort_values('season').copy()

    # Merge signals for market_value
    if not signals_df.empty:
        sig = signals_df[['season', 'market_value']].copy()
        df = df.merge(sig, on='season', how='left')
    else:
        df['market_value'] = 0

    # Apply value swap (same as load_leaderboard): adjusted_value=market rate, market_value=production
    if 'adjusted_value' in df.columns and 'market_value' in df.columns:
        av_copy = df['adjusted_value'].copy()
        df['adjusted_value'] = df['market_value']     # Value = production worth
        df['market_value'] = av_copy                   # Mkt Value = market rate

    # Fix season index to show as integer years
    df['season'] = df['season'].astype(int).astype(str)

    # Performance trend (Core Grade + Output Score)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Performance Trend**")
        score_data = df.set_index('season')[['core_grade', 'output_score']].rename(
            columns={'core_grade': 'Core Grade', 'output_score': 'Output Score'}
        )
        st.line_chart(score_data, use_container_width=True)

    with col2:
        st.markdown("**Value Trend**")
        value_data = df.set_index('season')[['adjusted_value', 'market_value']].rename(
            columns={'adjusted_value': 'Value', 'market_value': 'Mkt Value'}
        )
        value_data = value_data.fillna(0) / 1000
        st.line_chart(value_data, use_container_width=True)
        st.caption("Values in $K")


def tier_distribution_chart(df: pd.DataFrame):
    """Bar chart of tier distribution."""
    if df.empty:
        return
    tier_counts = df['tier'].value_counts().reindex(['T1', 'T2', 'T3', 'T4'], fill_value=0)
    st.bar_chart(tier_counts, use_container_width=True)
