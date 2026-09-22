"""UI for connecting third-party services (GitHub, Stripe, Sheets, Notion)."""

from __future__ import annotations

import streamlit as st

try:
    from .. import api_client
except ImportError:
    import api_client


def render_connections_view(user_id: str):
    token = st.session_state.get("sb_access_token", "")

    st.markdown('<div class="page-title">Connect accounts</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="helper-text">Ground the committee\'s scrutiny in real metrics, repositories, and notes. The panel will cross-check your statements directly against these data sources.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)

    try:
        raw_conns = api_client.get_connections(token=token)
        connections = {c["provider"]: c for c in raw_conns}
    except Exception as exc:
        st.error(f"Failed to fetch connected accounts: {exc}")
        connections = {}

    # Four glassmorphic rows (GitHub, Stripe, Google Sheets, Notion)
    providers = [
        ("github", "GitHub", "Allows the VC to inspect commit velocity, repository age, and active contributors."),
        ("stripe", "Stripe", "Enables the Financial Analyst to verify actual MRR, churn rate, and customer count."),
        ("sheets", "Google Sheets", "Allows the Financial Analyst to audit formula logic and financial projections."),
        ("notion", "Notion", "Enables the Market Realist to review internal market research documents and notes."),
    ]

    for key, name, desc in providers:
        is_connected = key in connections

        st.markdown('<div class="panel-card" style="margin-bottom: 14px;">', unsafe_allow_html=True)
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
                    try:
                        api_client.delete_connection(provider=key, token=token)
                        st.toast(f"Disconnected {name}.", icon="ℹ️")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to disconnect {name}: {exc}")
            else:
                auth_url = None
                try:
                    auth_url = api_client.get_authorize_url(provider=key, token=token)
                except Exception:
                    auth_url = None

                if auth_url:
                    st.link_button("Connect", auth_url, use_container_width=True)
                else:
                    if st.button("Connect", key=f"mock_conn_{key}", type="secondary", use_container_width=True):
                        try:
                            api_client.exchange_connection(
                                provider=key,
                                code=f"mock_token_{key}",
                                state=f"provider={key}",
                                redirect_uri="",
                                token=token,
                            )
                            st.toast(f"Connected {name} (mock mode).", icon="✅")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Failed to connect {name}: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)
