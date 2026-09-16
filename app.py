"""
Devil's Advocate Panel — Main Streamlit Application Entry Point.
Pitch your startup idea. Get grilled by ruthless AI investors.
"""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from ui.components import apply_custom_styles
from ui.auth import render_auth_view
from ui.pitch import render_pitch_view
from ui.session import render_session_view
from ui.verdict import render_verdict_view
from ui.connections import render_connections_view
from ui.history import render_history_view

load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="Devil's Advocate Panel",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize theme state in Python (§6)
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# Apply customized design system based on active theme
apply_custom_styles()


from connectors.oauth import exchange_code_for_token
from core.config import get_app_base_url
from db.connections import save_user_connection
from db.client import get_supabase_client


def main():
    # Authentication & User State
    user_id = render_auth_view()
    if not user_id:
        st.stop()

    # --- OAuth Callback Handling (§1) ---
    code = st.query_params.get("code")
    state = st.query_params.get("state")
    if code and state:
        # State format from ui/connections.py is "provider={key}"
        provider = None
        if "provider=" in state:
            provider = state.split("provider=")[1].split("&")[0]
        
        if provider:
            token_data = exchange_code_for_token(provider, code, redirect_uri=get_app_base_url())
            if token_data and "access_token" in token_data:
                access_token = token_data["access_token"]
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in")
                save_user_connection(
                    user_id=user_id,
                    provider=provider,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    metadata=token_data,
                )
                st.query_params.clear()
                st.toast(f"Successfully connected {provider.capitalize()}!", icon="✅")
                st.session_state["active_page"] = "connections"
                st.rerun()
            else:
                st.query_params.clear()
                st.error(f"Failed to connect {provider.capitalize()} — could not exchange authorization code.")

    # Sidebar: Global Shell (§7)
    with st.sidebar:
        # App wordmark (Fraunces 22px)
        st.markdown('<div class="app-wordmark">Devil\'s Advocate Panel</div>', unsafe_allow_html=True)

        if "active_page" not in st.session_state:
            st.session_state["active_page"] = "pitch"

        # 5 Nav items with exact Material Symbols shorthand (§3)
        nav_items = [
            ("pitch", ":material/target: Pitch Submission"),
            ("session", ":material/gavel: Live Interrogation"),
            ("verdict", ":material/description: Final Verdict Report"),
            ("connections", ":material/link: Connect Accounts"),
            ("history", ":material/history: Pitch History"),
        ]

        for page_key, label in nav_items:
            is_active = (st.session_state["active_page"] == page_key)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_key}", type=btn_type, use_container_width=True):
                st.session_state["active_page"] = page_key
                st.rerun()

        st.markdown('<div style="flex-grow: 1; height: 120px;"></div>', unsafe_allow_html=True)

        # Theme toggle icon button (§3 and §6)
        current_theme = st.session_state["theme"]
        toggle_icon = ":material/light_mode:" if current_theme == "dark" else ":material/dark_mode:"
        toggle_label = f"{toggle_icon} {'Light mode' if current_theme == 'dark' else 'Dark mode'}"
        
        st.markdown('<div class="theme-toggle-container">', unsafe_allow_html=True)
        if st.button(toggle_label, key="theme_toggle", use_container_width=True):
            st.session_state["theme"] = "light" if current_theme == "dark" else "dark"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="helper-text" style="padding-top: 12px; font-size: 13px;">v1.0 • Private committee session</div>',
            unsafe_allow_html=True,
        )

        user_email = st.session_state.get("user_email")
        if user_email:
            st.markdown(
                f'<div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{user_email}</div>',
                unsafe_allow_html=True,
            )

        if st.button(":material/logout: Log out", key="logout_btn", type="secondary", use_container_width=True):
            client = get_supabase_client()
            if client:
                try:
                    client.auth.sign_out()
                except Exception:
                    pass
            st.session_state.pop("user_id", None)
            st.session_state.pop("user_email", None)
            st.session_state.pop("sb_access_token", None)
            st.query_params.clear()
            st.rerun()

    # Main view routing wrapped in cross-fade & upward slide transition
    active = st.session_state["active_page"]
    st.markdown('<div class="screen-transition-container">', unsafe_allow_html=True)
    if active == "pitch":
        render_pitch_view(user_id)
    elif active == "session":
        render_session_view(user_id)
    elif active == "verdict":
        render_verdict_view(user_id)
    elif active == "connections":
        render_connections_view(user_id)
    elif active == "history":
        render_history_view(user_id)
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
