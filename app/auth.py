"""
NILytics — Authentication Layer
Invite-only email auth via Supabase Auth.
"""
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


def _get_secret(key: str) -> str:
    """Get a secret from environment or Streamlit Cloud secrets."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        raise ValueError(f"Missing secret: {key}. Set in .env or Streamlit Cloud secrets.")


def _get_auth_client():
    """Get a Supabase client for auth operations."""
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    return create_client(url, key)


def check_auth():
    """
    Check if user is authenticated. If not, show login form and stop.
    Returns the user dict if authenticated.
    """
    # ── AUTH BYPASS (testing mode) ──
    # Set to False to re-enable login
    AUTH_DISABLED = True
    if AUTH_DISABLED:
        return {'id': 'test', 'email': 'test@nilytics.com', 'access_token': 'bypass'}

    # Check if already logged in this session
    if st.session_state.get('authenticated') and st.session_state.get('user'):
        return st.session_state['user']

    # Show login form
    _show_login_page()
    st.stop()


def _show_login_page():
    """Render the login page."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(app_dir, 'assets', 'logo.png')

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, width=280)

        st.markdown(
            '<div style="text-align:center; margin-bottom:2rem;">'
            '<p style="color:#888; font-size:0.9rem;">Invite-only scouting intelligence platform</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        tab_login, tab_reset = st.tabs(["Sign In", "Reset Password"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@team.com")
                password = st.text_input("Password", type="password", placeholder="Your password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        _handle_login(email, password)

        with tab_reset:
            with st.form("reset_form"):
                reset_email = st.text_input("Email", placeholder="you@team.com", key="reset_email")
                reset_submitted = st.form_submit_button("Send Reset Link", use_container_width=True)

                if reset_submitted:
                    if not reset_email:
                        st.error("Please enter your email.")
                    else:
                        _handle_password_reset(reset_email)

        st.markdown(
            '<div style="text-align:center; margin-top:2rem; color:#ccc; font-size:0.75rem;">'
            'Access is by invitation only. Contact your admin for an invite.'
            '</div>',
            unsafe_allow_html=True,
        )


def _handle_login(email: str, password: str):
    """Attempt to sign in."""
    try:
        sb = _get_auth_client()
        response = sb.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        if response.user:
            st.session_state['authenticated'] = True
            st.session_state['user'] = {
                'id': response.user.id,
                'email': response.user.email,
                'access_token': response.session.access_token,
            }
            # Check if admin
            admin_check = sb.table('app_admins').select('email').eq('email', email).execute()
            st.session_state['is_admin'] = len(admin_check.data) > 0

            st.success("Signed in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials.")
    except Exception as e:
        error_msg = str(e)
        if 'Invalid login' in error_msg or 'invalid' in error_msg.lower():
            st.error("Invalid email or password.")
        elif 'Email not confirmed' in error_msg:
            st.warning("Please check your email and confirm your account first.")
        else:
            st.error(f"Login failed: {error_msg}")


def _handle_password_reset(email: str):
    """Send password reset email."""
    try:
        sb = _get_auth_client()
        sb.auth.reset_password_email(email)
        st.success("If that email exists in our system, a reset link has been sent.")
    except Exception as e:
        st.error(f"Reset failed: {e}")


def logout():
    """Clear session and sign out."""
    st.session_state['authenticated'] = False
    st.session_state['user'] = None
    st.session_state['is_admin'] = False
    st.rerun()


def is_admin():
    """Check if current user is an admin."""
    return st.session_state.get('is_admin', False)


def render_user_sidebar():
    """Render user info and logout in sidebar."""
    user = st.session_state.get('user')
    if user:
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Signed in as **{user['email']}**")
        if st.sidebar.button("Sign Out", use_container_width=True):
            logout()
