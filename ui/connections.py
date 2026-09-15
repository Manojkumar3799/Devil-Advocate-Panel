"""UI for connecting third-party services (GitHub, Stripe, Sheets, Notion)."""

from __future__ import annotations

import streamlit as st
from db.connections import get_user_connections, delete_connection, save_user_connection
from connectors.oauth import get_oauth_authorize_url
from core.config import get_app_base_url


def render_connections_view(user_id: str):
    st.markdown('<div class="page-title">Connect accounts</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="helper-text">Ground the committee\'s scrutiny in real metrics, repositories, and notes. The panel will cross-check your statements directly against these data sources.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)

    connections = {c["provider"]: c for c in get_user_connections(user_id)}

    # Four rows (GitHub, Stripe, Google Sheets, Notion) per §7
    providers = [
        ("github", "GitHub", "Allows the VC to inspect commit velocity, repository age, and active contributors."),
        ("stripe", "Stripe", "Enables the Financial Analyst to verify actual MRR, churn rate, and customer count."),
        ("sheets", "Google Sheets", "Allows the Financial Analyst to audit formula logic and financial projections."),
        ("notion", "Notion", "Enables the Market Realist to review internal market research documents and notes."),
    ]

    for key, name, desc in providers:
        is_connected = key in connections

        with st.container():
            col1, col2 = st.columns([7, 3])
            with col1:
                st.markdown(
                    f"""
                    <div style="font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; font-size: 16px; color: var(--text-primary); margin-bottom: 4px;">
                        {name}
                    </div>
                    <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 14px; color: var(--text-secondary); line-height: 1.4;">
                        {desc}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                if is_connected:
                    st.markdown(
                        '<div style="text-align: right; color: var(--severity-low); font-weight: 500; font-size: 14px; margin-bottom: 8px;">:material/check_circle: Connected</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Disconnect", key=f"disc_{key}", type="secondary", use_container_width=True):
                        delete_connection(user_id, key)
                        st.rerun()
                else:
                    auth_url = get_oauth_authorize_url(key, get_app_base_url(), f"provider={key}")
                    if auth_url:
                        st.link_button("Connect", auth_url, use_container_width=True)
                    else:
                        if st.button("Connect", key=f"mock_conn_{key}", type="secondary", use_container_width=True):
                            save_user_connection(user_id, key, access_token=f"mock_token_{key}")
                            st.rerun()

            st.markdown('<hr style="border: none; border-top: 1px solid var(--border-hairline); margin: 16px 0;" />', unsafe_allow_html=True)
