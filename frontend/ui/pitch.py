"""Pitch submission and intensity configuration UI."""

from __future__ import annotations

import streamlit as st

try:
    from .. import api_client
except ImportError:
    import api_client

SAMPLE_PITCH = (
    "We are building DevPulse, an AI agent orchestration engine for engineering teams. "
    "We automatically fix CI/CD build failures and suggest pull requests. "
    "We currently have $8k MRR with 14 enterprise design partners and are raising $1.5M at a $12M cap."
)


def render_pitch_view(user_id: str):
    token = st.session_state.get("sb_access_token", "")

    st.markdown('<div class="page-title">Submit your pitch</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="helper-text">Present your core thesis, traction, and fundraising terms. The panel will examine every assumption.</p>',
        unsafe_allow_html=True,
    )

    pitch_text = st.text_area(
        "Pitch details",
        value=st.session_state.get("draft_pitch", SAMPLE_PITCH),
        height=180,
        label_visibility="collapsed",
        placeholder="Enter your startup pitch...",
    )

    st.markdown('<div class="section-heading">Select intensity</div>', unsafe_allow_html=True)

    intensities = [
        ("light", "Light", "Constructive wit. Accepts plausible reasoning with minimal follow-ups."),
        ("normal", "Normal", "Direct and skeptical. Demands concrete figures before accepting."),
        ("heavy", "Heavy", "Mocking weak claims. Actively searches for discrepancies."),
        ("no_mercy", "No mercy", "Adversarial register. Vague claims become high-severity flaws."),
    ]

    selected_intensity = st.session_state.get("selected_intensity", "normal")

    cols = st.columns(4)
    for i, (key, title, desc) in enumerate(intensities):
        with cols[i]:
            is_selected = selected_intensity == key
            selected_class = f"selected intensity-{key}" if is_selected else f"intensity-{key}"
            st.markdown(
                f"""
                <div class="intensity-card {selected_class}">
                    <div class="intensity-title">{title}</div>
                    <div class="intensity-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_label = f":material/check_circle: Selected" if is_selected else "Select"
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"int_btn_{key}", type=btn_type, use_container_width=True):
                st.session_state["selected_intensity"] = key
                st.rerun()

    current_intensity = st.session_state.get("selected_intensity", "normal")

    # Display connected data sources note via backend API
    try:
        conns = api_client.get_connections(token=token)
        user_conns = [c["provider"] for c in conns]
    except Exception:
        user_conns = []

    if user_conns:
        conn_names = ", ".join([c.capitalize() for c in user_conns])
        st.markdown(f'<p class="helper-text" style="margin-top: 24px;">:material/link: Connected accounts: {conn_names}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="helper-text" style="margin-top: 24px;">:material/info: No external accounts connected. Evaluation will rely on pitch text and live market data.</p>', unsafe_allow_html=True)

    # Primary CTA Button: Start interrogation
    submit_disabled = len(pitch_text.strip()) < 50
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    if st.button("Start interrogation", type="primary", disabled=submit_disabled, use_container_width=True):
        with st.spinner("Submitting pitch and convening investment committee..."):
            try:
                res = api_client.create_session(
                    pitch_text=pitch_text,
                    intensity=current_intensity,
                    token=token,
                )
                session_id = res["session_id"]
                panel_state = res["state"]

                st.session_state["current_session_id"] = session_id
                st.session_state["pitch_text"] = pitch_text
                st.session_state["intensity"] = current_intensity
                st.session_state["connected_providers"] = user_conns
                st.session_state["panel_state"] = panel_state
                st.session_state["active_page"] = "session"
                st.session_state["session_active"] = True
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to initiate panel session: {exc}")

    if submit_disabled:
        st.markdown('<p class="helper-text" style="color: var(--severity-high) !important;">Please provide at least 50 characters in your pitch before submitting.</p>', unsafe_allow_html=True)
