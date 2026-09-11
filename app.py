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


def main():
    # Authentication & User State
    user_id = render_auth_view()
    if not user_id:
        st.stop()

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

    # Main view routing
    active = st.session_state["active_page"]
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


if __name__ == "__main__":
    main()
