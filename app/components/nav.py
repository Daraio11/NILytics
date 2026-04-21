"""
NILytics — Shared Navigation Components
PFF Premium Stats-style: dark top bar with logo left + nav right,
hamburger sidebar with all pages + utility links.
"""
import os
import base64
import streamlit as st
import streamlit.components.v1 as components


def inject_fonts():
    """Inject Google Fonts (Inter + DM Mono) with font-display: swap."""
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            @font-face { font-display: swap; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_logo_b64(app_dir):
    """Return base64-encoded logo or empty string."""
    logo_path = os.path.join(app_dir, 'assets', 'logo.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ''


def render_logo_and_nav(active_page='leaderboard'):
    """
    Render PFF Premium Stats-style navigation.
    - Dark top bar: logo left, core nav buttons right (single row)
    - Streamlit sidebar (hamburger): all pages + utility links
    """
    inject_fonts()

    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_b64 = _get_logo_b64(app_dir)

    # ── Page definitions ──
    core_pages = [
        ('leaderboard', 'Leaderboard', 'pages/01_leaderboard.py'),
        ('player_card', 'Player Search', 'pages/02_player_card.py'),
        ('team', 'Teams', 'pages/10_team.py'),
        ('gm_mode', 'GM Mode', 'pages/04_gm_mode.py'),
        ('recruiting', 'Recruiting', 'pages/07_recruiting.py'),
        ('alerts', 'Alerts', 'pages/08_alerts.py'),
    ]

    secondary_pages = [
        ('compare', 'Compare', 'pages/11_compare.py'),
        ('lab', 'Lab', 'pages/06_lab.py'),
        ('methodology', 'Methodology', 'pages/03_methodology.py'),
        ('board', 'My Board', 'pages/09_board.py'),
    ]

    # ── Inject all CSS ──
    _inject_nav_css()

    # ── TOP BAR: logo row with integrated hamburger toggle ──
    logo_img = ''
    if logo_b64:
        logo_img = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="height:26px;width:auto;vertical-align:middle;" />'
            f'<span style="font-family:Inter,sans-serif;font-weight:700;font-size:16px;'
            f'color:#ffffff;letter-spacing:0.08em;text-transform:uppercase;'
            f'margin-left:10px;vertical-align:middle;">NILytics</span>'
        )

    # Use components.html for the entire logo bar so JS works
    components.html(f"""
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; }}
        .topbar {{
            background: #111111;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            font-family: Inter, sans-serif;
        }}
        .hb {{
            background: none; border: none; cursor: pointer;
            padding: 4px 6px; margin-right: 12px; border-radius: 4px;
            display: flex; align-items: center; justify-content: center;
            transition: background 0.15s;
        }}
        .hb:hover {{ background: rgba(255,255,255,0.12); }}
    </style>
    <div class="topbar">
        <button class="hb" onclick="toggleSB()">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff"
                 stroke-width="2.5" stroke-linecap="round">
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
        </button>
        {logo_img}
    </div>
    <script>
    function toggleSB() {{
        var doc = window.parent.document;
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (sb && sb.getAttribute('aria-expanded') === 'true') {{
            var c = doc.querySelector('[data-testid="stSidebar"] button');
            if (c) c.click();
        }} else {{
            var e = doc.querySelector('[data-testid="stExpandSidebarButton"]');
            if (e) e.click();
        }}
    }}
    </script>
    """, height=46)

    # Nav buttons in a single row — active page gets HTML label, others get buttons
    # Use columns: small spacer left to push nav right, then one col per nav item
    spacer_ratio = 3
    col_ratios = [spacer_ratio] + [1] * len(core_pages)
    nav_cols = st.columns(col_ratios, gap="small")

    # Spacer column (empty)
    with nav_cols[0]:
        st.empty()

    for i, (key, label, page_path) in enumerate(core_pages):
        with nav_cols[i + 1]:
            if key == active_page:
                st.markdown(
                    f'<div class="nil-nav-active">{label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.switch_page(page_path)

    # Bottom border line under the nav
    st.markdown('<div class="nil-topbar-border"></div>', unsafe_allow_html=True)

    # ── SIDEBAR: All pages (PFF hamburger drawer) ──
    if logo_b64:
        st.sidebar.markdown(
            f'<div class="sidebar-brand">'
            f'<img src="data:image/png;base64,{logo_b64}" style="height:24px;margin-right:8px;" />'
            f'<span style="font-family:Inter,sans-serif;font-weight:700;font-size:14px;'
            f'color:#1f2937;letter-spacing:0.02em;">NILytics</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Core pages in sidebar
    for key, label, page_path in core_pages:
        if key == active_page:
            st.sidebar.markdown(
                f'<div class="sidebar-link sidebar-link-active">{label}</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.sidebar.button(label, key=f"sb_{key}", use_container_width=True):
                st.switch_page(page_path)

    # Divider + secondary section
    st.sidebar.markdown(
        '<div class="sidebar-divider"></div>'
        '<div class="sidebar-section-label">More Tools</div>',
        unsafe_allow_html=True,
    )

    for key, label, page_path in secondary_pages:
        if key == active_page:
            st.sidebar.markdown(
                f'<div class="sidebar-link sidebar-link-active">{label}</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.sidebar.button(label, key=f"sb_{key}", use_container_width=True):
                st.switch_page(page_path)


def _inject_nav_css():
    """Inject all navigation-related CSS."""
    st.markdown("""
    <style>
    /* ══════════════════════════════════════════
       GLOBAL — Remove Streamlit chrome
       ══════════════════════════════════════════ */
    /* Hide Streamlit header — we use our own hamburger toggle */
    .stApp > header {
        background: transparent !important;
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
    }
    div[data-testid="stImage"] { margin: 0 !important; padding: 0 !important; }

    /* Hide default Streamlit page nav in sidebar */
    section[data-testid="stSidebar"] nav {
        display: none !important;
    }

    /* ══════════════════════════════════════════
       TOP BAR — components.html iframe cleanup
       ══════════════════════════════════════════ */
    /* Remove padding/margin and make full-width */
    .stHtml {
        margin: 0 -1rem !important;
        padding: 0 !important;
    }
    .stHtml iframe {
        border: none !important;
        width: 100% !important;
    }
    /* Kill gap between invisible style-injection elements at top of page */
    .stMainBlockContainer > .stVerticalBlock {
        gap: 0 !important;
    }
    /* Add gap back between visible content elements (not style injections) */
    .stMainBlockContainer .stHorizontalBlock {
        margin-top: 8px;
    }

    /* ══════════════════════════════════════════
       TOP BAR — Nav button row
       ══════════════════════════════════════════ */
    /* Strip ALL Streamlit button chrome from nav buttons */
    .block-container div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button,
    .block-container div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:focus,
    .block-container div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:active {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        outline: none !important;
        padding: 12px 8px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #6b7280 !important;
        letter-spacing: 0.02em !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        transition: color 0.15s !important;
        font-family: 'Inter', sans-serif !important;
    }
    .block-container div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
        color: #111111 !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
    }
    .block-container div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button p {
        font-size: 13px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        color: inherit !important;
    }

    /* Active nav label */
    .nil-nav-active {
        padding: 12px 8px;
        font-size: 13px;
        font-weight: 700;
        color: #111111;
        border-bottom: 3px solid #E8390E;
        white-space: nowrap;
        letter-spacing: 0.02em;
        font-family: 'Inter', sans-serif;
        text-align: center;
    }

    /* Border under nav row */
    .nil-topbar-border {
        border-bottom: 2px solid #e5e7eb;
        margin: 0 -1rem 1rem -1rem;
    }

    /* ══════════════════════════════════════════
       SIDEBAR — PFF hamburger drawer style
       ══════════════════════════════════════════ */
    /* Sidebar container — light theme */
    section[data-testid="stSidebar"] {
        background: #f6f8fa !important;
    }
    section[data-testid="stSidebar"] > div {
        background: #f6f8fa !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        padding: 4px 0 16px 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    /* Style sidebar buttons to look like nav links */
    section[data-testid="stSidebar"] button {
        background: none !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 12px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #374151 !important;
        text-align: left !important;
        width: 100% !important;
        cursor: pointer !important;
        transition: background 0.15s, color 0.15s !important;
        box-shadow: none !important;
        font-family: 'Inter', sans-serif !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: rgba(0,0,0,0.04) !important;
        color: #1f2937 !important;
    }
    section[data-testid="stSidebar"] button p {
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    .sidebar-link {
        padding: 10px 12px;
        font-size: 14px;
        font-weight: 600;
        color: #1f2937;
        font-family: 'Inter', sans-serif;
        border-radius: 6px;
    }
    .sidebar-link-active {
        color: #E8390E !important;
        font-weight: 700 !important;
        background: rgba(232, 57, 14, 0.06);
    }

    .sidebar-divider {
        border-top: 1px solid #e5e7eb;
        margin: 16px 0 12px 0;
    }
    .sidebar-section-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #9ca3af;
        font-weight: 700;
        padding: 0 12px;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the app footer."""
    st.markdown(
        '<footer class="app-footer">'
        'NILytics &copy; 2026 &middot; Turning Production Into Compensation &middot; Data: PFF'
        '</footer>',
        unsafe_allow_html=True,
    )
