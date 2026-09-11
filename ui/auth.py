"""Authentication UI view using Supabase Auth or Local Session."""

from __future__ import annotations

import streamlit as st
from db.client import get_supabase_client


def render_auth_view() -> str | None:
    """Render login/user status view. Returns user_id if authenticated."""
    client = get_supabase_client()

    # Local developer fallback when Supabase is not configured
    if not client:
        st.session_state["user_id"] = "dev_user_demo"
        st.session_state["user_email"] = "founder@demo.local"
        return "dev_user_demo"

    # Supabase session handling
    if "user_id" in st.session_state and st.session_state["user_id"]:
        return st.session_state["user_id"]

    st.markdown('<div class="page-title">Sign in</div>', unsafe_allow_html=True)
    st.markdown('<p class="helper-text">Access your private investment committee session archives.</p>', unsafe_allow_html=True)

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
