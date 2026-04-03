"""
NILytics — Admin Panel
Invite users, manage data, trigger recalculations.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import check_auth, is_admin, render_user_sidebar
from app.data import get_supabase
from app.components.nav import render_logo_and_nav, inject_fonts, render_footer

st.set_page_config(page_title="NILytics — Admin", page_icon="🏈", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_fonts()

render_logo_and_nav(active_page='admin')

# Auth check
user = check_auth()
render_user_sidebar()

if not is_admin():
    st.error("Access denied. Admin privileges required.")
    st.stop()

st.markdown(
    '<div class="main-header">'
    '<h1>Admin Panel</h1>'
    '<p>Manage users, data, and system settings</p>'
    '</div>',
    unsafe_allow_html=True,
)

sb = get_supabase()

# ── Section 1: Invite Users ──
st.markdown('<p class="section-header">Invite Users</p>', unsafe_allow_html=True)
st.caption("Send an invitation email. The user will receive a link to set their password.")

with st.form("invite_form"):
    invite_email = st.text_input("Email address", placeholder="coach@university.edu")
    submitted = st.form_submit_button("Send Invite", use_container_width=False)

    if submitted and invite_email:
        try:
            # Use Supabase Admin API to invite user
            # Note: This requires the service_role key for admin operations
            service_key = os.environ.get('SUPABASE_SERVICE_KEY', '')
            if service_key:
                from supabase import create_client
                admin_sb = create_client(os.environ['SUPABASE_URL'], service_key)
                admin_sb.auth.admin.invite_user_by_email(invite_email)
                st.success(f"Invitation sent to **{invite_email}**")
            else:
                st.warning("Service role key not configured. Add `SUPABASE_SERVICE_KEY` to `.env` to enable invites. "
                           "You can find it in Supabase Dashboard > Settings > API > service_role key.")
        except Exception as e:
            st.error(f"Failed to send invite: {e}")

st.markdown("---")

# ── Section 2: Current Users ──
st.markdown('<p class="section-header">Registered Admins</p>', unsafe_allow_html=True)

try:
    admins = sb.table('app_admins').select('*').execute()
    if admins.data:
        for admin in admins.data:
            st.markdown(f"- **{admin['email']}** (added {admin.get('added_at', 'unknown')[:10]})")
    else:
        st.info("No admins configured.")
except Exception as e:
    st.error(f"Could not load admins: {e}")

# Add admin
with st.form("add_admin_form"):
    new_admin = st.text_input("Add admin email", placeholder="admin@university.edu")
    add_submitted = st.form_submit_button("Add Admin")

    if add_submitted and new_admin:
        try:
            sb.table('app_admins').insert({'email': new_admin}).execute()
            st.success(f"Added **{new_admin}** as admin.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")

st.markdown("---")

# ── Section 3: Data Management ──
st.markdown('<p class="section-header">Data Overview</p>', unsafe_allow_html=True)

try:
    # Get counts
    players_count = sb.table('players').select('player_id', count='exact').execute()
    scores_count = sb.table('player_scores').select('id', count='exact').execute()
    signals_count = sb.table('alpha_signals').select('id', count='exact').execute()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Players", f"{players_count.count:,}" if players_count.count else "?")
    with c2:
        st.metric("Score Records", f"{scores_count.count:,}" if scores_count.count else "?")
    with c3:
        st.metric("Signal Records", f"{signals_count.count:,}" if signals_count.count else "?")
except Exception as e:
    st.error(f"Could not load counts: {e}")

st.markdown("---")

# ── Section 4: Scoring Engine ──
st.markdown('<p class="section-header">Scoring Engine</p>', unsafe_allow_html=True)
st.caption("Re-run the scoring engine for a specific season. This will recalculate all scores and signals.")

with st.form("rescore_form"):
    rescore_season = st.selectbox("Season", list(range(2025, 2017, -1)))
    rescore_submitted = st.form_submit_button("Re-Score Season")

    if rescore_submitted:
        st.info(f"To re-score {rescore_season}, run from the command line:\n\n"
                f"```\npython3 -m scoring.run_scoring --season {rescore_season}\n"
                f"python3 -m scoring.alpha_signals --season {rescore_season}\n```")
        st.caption("Automated re-scoring from the UI will be available in a future update.")

render_footer()
