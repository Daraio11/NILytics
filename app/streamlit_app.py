"""
NILytics — Main Streamlit Entry Point
"""
import sys, os

# Ensure project root is on path so 'app.*' imports work
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

st.set_page_config(
    page_title="NILytics",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from app.components.nav import render_logo_and_nav, inject_fonts, render_footer
from app.auth import check_auth, render_user_sidebar

inject_fonts()

render_logo_and_nav(active_page='home')
user = check_auth()
render_user_sidebar()

st.markdown("""
<div class="main-header">
    <h1>Dashboard</h1>
    <p>Scouting intelligence at a glance</p>
</div>
""", unsafe_allow_html=True)

# Quick stats
from app.data import load_leaderboard
from app.components.card_front import fmt_money

df = load_leaderboard(2025)
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Eligible Players", f"{len(df):,}")
    with col2:
        t1 = len(df[df['tier'] == 'T1'])
        st.metric("Tier 1", f"{t1:,}")
    with col3:
        if 'opportunity_score' in df.columns:
            gems = len(df[df['opportunity_score'] > 500000])
            st.metric("High-Alpha", f"{gems:,}")
    with col4:
        positions = df['position'].nunique()
        st.metric("Positions", f"{positions}")

    st.markdown("---")

    # Navigation cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        **Leaderboard**
        Browse all players ranked by production, value, or opportunity.
        """)
        if st.button("Open Leaderboard", use_container_width=True):
            st.switch_page("pages/01_leaderboard.py")
    with c2:
        st.markdown("""
        **Player Card**
        Deep-dive into any player's full valuation profile.
        """)
        if st.button("Open Player Card", use_container_width=True):
            st.switch_page("pages/02_player_card.py")
    with c3:
        st.markdown("""
        **GM Mode**
        Build a roster under a budget and find the edge.
        """)
        if st.button("Open GM Mode", use_container_width=True):
            st.switch_page("pages/04_gm_mode.py")
    with c4:
        st.markdown("""
        **Methodology**
        How every number is computed, in plain English.
        """)
        if st.button("Open Methodology", use_container_width=True):
            st.switch_page("pages/03_methodology.py")
else:
    st.info("No data loaded yet. Run the scoring engine first.")

render_footer()
