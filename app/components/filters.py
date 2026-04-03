"""
NILytics — Shared Filter Sidebar
"""
import streamlit as st

POSITIONS = ['All', 'QB', 'RB', 'WR', 'TE', 'OT', 'IOL', 'EDGE', 'IDL', 'LB', 'CB', 'S']
MARKETS = ['All', 'P4', 'G6', 'FCS']
TIERS = ['All', 'T1', 'T2', 'T3', 'T4']
SEASONS = list(range(2025, 2017, -1))

CONFERENCES = [
    'All', 'SEC', 'Big Ten', 'Big 12', 'ACC', 'American', 'Mountain West',
    'Sun Belt', 'MAC', 'Conference USA', 'Pac-12', 'Independent',
    'Big Sky', 'CAA', 'MVFC', 'Southland', 'Ohio Valley', 'Other'
]


def render_filters():
    """Render sidebar filters and return filter dict."""
    st.sidebar.markdown(
        '<p style="font-size:13px; font-weight:600; color:#E8390E; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;">Filters</p>',
        unsafe_allow_html=True
    )

    season = st.sidebar.selectbox("Season", SEASONS, index=0)
    position = st.sidebar.selectbox("Position", POSITIONS, index=0)
    market = st.sidebar.selectbox("Market", MARKETS, index=0)
    tier = st.sidebar.selectbox("Tier", TIERS, index=0)
    conference = st.sidebar.selectbox("Conference", CONFERENCES, index=0)

    return {
        'season': season,
        'position': None if position == 'All' else position,
        'market': None if market == 'All' else market,
        'tier': None if tier == 'All' else tier,
        'conference': None if conference == 'All' else conference,
    }


def apply_filters(df, filters):
    """Apply filter dict to a DataFrame."""
    filtered = df.copy()

    if filters.get('position'):
        filtered = filtered[filtered['position'] == filters['position']]
    if filters.get('market'):
        filtered = filtered[filtered['market'] == filters['market']]
    if filters.get('tier'):
        filtered = filtered[filtered['tier'] == filters['tier']]
    if filters.get('conference'):
        if filters['conference'] == 'Other':
            known = set(CONFERENCES) - {'All', 'Other'}
            filtered = filtered[~filtered['conference'].isin(known)]
        else:
            filtered = filtered[filtered['conference'] == filters['conference']]

    return filtered
