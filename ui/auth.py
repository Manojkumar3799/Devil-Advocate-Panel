"""Authentication UI view using Supabase Auth or Local Session.

Login flow:
1. "Continue with Google" — triggers Supabase OAuth which redirects the browser
   to Google, then back to APP_BASE_URL with the session tokens in the URL
   *fragment* (e.g.  ``#access_token=...&refresh_token=...``).  URL fragments are
   never sent to the server, so we inject a tiny JS snippet that converts the
   fragment into a query-param ``?sb_access_token=...`` which Streamlit CAN read.
2. Email / password — traditional Supabase password auth (kept as fallback).
3. Dev fallback — when Supabase is not configured, always returns dev_user_demo.
"""

from __future__ import annotations

import streamlit as st
from db.client import get_supabase_client
from core.config import get_app_base_url


# ---------------------------------------------------------------------------
# Supabase fragment → query-param bridge
# Supabase implicit/PKCE flow returns tokens in the URL *hash* which the
# server never sees.  This JS reads the hash, rewrites it to a query-param
# and does a single window.location.replace() — which triggers a Streamlit
# page reload that can then read `st.query_params`.
# The snippet is a no-op if no access_token is present in the hash.
# ---------------------------------------------------------------------------
_OAUTH_BRIDGE_JS = """
<script>
(function() {
  const hash = window.location.hash;
  if (!hash || hash.indexOf('access_token') === -1) return;
  // Parse the fragment as URL params
  const params = new URLSearchParams(hash.substring(1));
  const accessToken  = params.get('access_token');
  const refreshToken = params.get('refresh_token') || '';
  const tokenType    = params.get('token_type') || 'bearer';
  if (!accessToken) return;
  // Build a new URL without the fragment, with tokens as query params instead
  const newUrl = window.location.pathname
    + '?sb_access_token=' + encodeURIComponent(accessToken)
    + '&sb_refresh_token=' + encodeURIComponent(refreshToken);
  // Replace so we don't push a history entry
  window.location.replace(newUrl);
})();
</script>
"""


def _handle_supabase_token_callback(client) -> bool:
    """Check for a Supabase access token in query params (written by the JS bridge).

    Returns True if a session was established, False otherwise.
    """
    sb_token = st.query_params.get("sb_access_token")
    if not sb_token:
        return False

    try:
        user_resp = client.auth.get_user(sb_token)
        if user_resp and user_resp.user:
            st.session_state["user_id"] = str(user_resp.user.id)
            st.session_state["user_email"] = user_resp.user.email or ""
            st.session_state["sb_access_token"] = sb_token
            st.query_params.clear()
            return True
    except Exception as e:
        st.error(f"Google sign-in failed while verifying token: {e}")
        st.query_params.clear()
    return False


def render_auth_view() -> str | None:
    """Render login/user status view. Returns user_id if authenticated."""
    client = get_supabase_client()

    # Local developer fallback when Supabase is not configured
    if not client:
        st.session_state["user_id"] = "dev_user_demo"
        st.session_state["user_email"] = "founder@demo.local"
        return "dev_user_demo"

    # --- OAuth fragment bridge (injected on every page load; no-op when hash is absent) ---
    st.html(_OAUTH_BRIDGE_JS)

    # Check if Supabase redirected back with tokens in query params (written by JS bridge)
    if _handle_supabase_token_callback(client):
        st.rerun()

    # Already authenticated
    if "user_id" in st.session_state and st.session_state["user_id"]:
        return st.session_state["user_id"]

    # ---- Login UI ----
    st.markdown('<div class="page-title">Sign in</div>', unsafe_allow_html=True)
    st.markdown('<p class="helper-text">Access your private investment committee session archives.</p>', unsafe_allow_html=True)

    # Primary: Google OAuth (above the email/password tabs)
    st.markdown('<div style="margin: 20px 0 8px 0;">', unsafe_allow_html=True)
    try:
        oauth_resp = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": get_app_base_url()},
        })
        google_url = oauth_resp.url if oauth_resp else None
    except Exception:
        google_url = None

    if google_url:
        st.link_button(
            "🔵  Continue with Google",
            google_url,
            use_container_width=True,
            type="primary",
        )
    else:
        st.info("Google sign-in not configured. Enable the Google provider in your Supabase dashboard.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="display: flex; align-items: center; gap: 8px; margin: 16px 0;">'
        '<hr style="flex:1;border:none;border-top:1px solid var(--border-hairline);"/>'
        '<span class="helper-text" style="white-space:nowrap;">or continue with email</span>'
        '<hr style="flex:1;border:none;border-top:1px solid var(--border-hairline);"/>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Secondary: email / password (kept as-is for fallback)
    tab_login, tab_signup = st.tabs(["Sign in", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign in", type="primary", use_container_width=True):
            try:
                auth_res = client.auth.sign_in_with_password({"email": email, "password": password})
                if auth_res.user:
                    st.session_state["user_id"] = str(auth_res.user.id)
                    st.session_state["user_email"] = auth_res.user.email
                    st.rerun()
            except Exception as e:
                st.error(f"Sign in failed: {e}")

    with tab_signup:
        signup_email = st.text_input("New email", key="signup_email")
        signup_pass = st.text_input("New password", type="password", key="signup_pass")
        if st.button("Create account", type="primary", use_container_width=True):
            try:
                auth_res = client.auth.sign_up({"email": signup_email, "password": signup_pass})
                if auth_res.user:
                    st.session_state["user_id"] = str(auth_res.user.id)
                    st.session_state["user_email"] = auth_res.user.email
                    st.rerun()
            except Exception as e:
                st.error(f"Registration failed: {e}")

    return st.session_state.get("user_id")
