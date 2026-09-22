"""Live interrogation session UI handling conversational turns, thinking traces, and replies."""

from __future__ import annotations

import streamlit as st

try:
    from .. import api_client
except ImportError:
    import api_client

from .components import render_progress_tracker, render_thinking_dots

PERSONA_META = {
    "vc": {
        "name": "Venture Capitalist",
        "icon": "trending_up",
        "color": "var(--severity-medium)",
    },
    "analyst": {
        "name": "Financial Analyst",
        "icon": "calculate",
        "color": "var(--severity-low)",
    },
    "realist": {
        "name": "Market Realist",
        "icon": "public",
        "color": "var(--severity-high)",
    },
}

_BILLING_KEYWORDS = (
    "permission-denied", "permission denied", "insufficient_quota",
    "invalid_api_key", "incorrect api key", "credits", "quota",
    "403", "401", "billing",
)


def _handle_graph_error(exc: Exception) -> None:
    """Show a graceful Streamlit error banner for graph/LLM failures."""
    err_str = str(exc).lower()
    is_billing = any(kw in err_str for kw in _BILLING_KEYWORDS)

    if is_billing:
        st.error(
            "One of the panel's AI providers is unavailable (billing/credits issue) — "
            "the session could not continue. Check your API provider dashboards "
            "(xAI, Google AI Studio, Groq) and ensure the active API key has credits.",
            icon=":material/credit_card_off:",
        )
    else:
        st.error(
            f"Something went wrong generating this response: `{exc}`\n\n"
            "The rounds completed so far are preserved — you can try submitting your response again.",
            icon=":material/warning:",
        )


def render_session_view(user_id: str):
    token = st.session_state.get("sb_access_token", "")
    state = st.session_state.get("panel_state")
    if not state:
        st.warning("No active session found. Please submit a pitch first.")
        if st.button("Submit a pitch", type="primary"):
            st.session_state["active_page"] = "pitch"
            st.rerun()
        return

    # 3 Progress bars fixed at the top per persona
    render_progress_tracker(state.get("persona_status", {}))

    # Pitch overview expander
    with st.expander("Case file / Submitted pitch", expanded=False):
        st.markdown(f'<p class="constrained-text">{state.get("pitch_text", "")}</p>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

    # Vertical transcript: newest turn at the bottom
    transcript = state.get("transcript", [])
    total_entries = len(transcript)

    for i, entry in enumerate(transcript):
        p_key = entry.get("persona", "vc")
        meta = PERSONA_META.get(p_key, {"name": "Investor", "icon": "info", "color": "var(--accent)"})
        rnd = entry.get("round", 1)
        question = entry.get("question", "")
        thinking = entry.get("thinking", "")
        user_reply = entry.get("user_reply")

        # Is this the latest turn? If so, apply spotlight vignette and ignition
        is_latest = (i == total_entries - 1)
        card_class = "interrogation-card latest-turn active-persona-card" if is_latest else "interrogation-card"

        # Persona card with glassmorphism styling
        st.markdown(
            f"""
            <div class="{card_class}">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center;">
                        <div class="avatar-circle">
                            <span style="color: {meta['color']}; display: inline-flex; align-items: center;">
                                :material/{meta['icon']}:
                            </span>
                        </div>
                        <span class="persona-name-text">{meta['name']}</span>
                    </div>
                    <span class="round-counter-text">Round {rnd} of 3</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Reasoning trace with pulsing thinking indicator
        if thinking:
            with st.expander("Reasoning", expanded=False):
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <div class="thinking-indicator">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </div>
                        <span class="data-mono" style="font-size: 12px; letter-spacing: 0.5px; text-transform: uppercase;">Cognitive Analysis</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f'<p class="constrained-text text-secondary" style="font-size: 14px;">{thinking}</p>', unsafe_allow_html=True)

        # Question text in IBM Plex Sans 16px
        st.markdown(f'<div class="question-text">{question}</div>', unsafe_allow_html=True)

        # Founder reply in visually distinct sub-block
        if user_reply:
            st.markdown(
                f"""
                <div class="founder-reply-box">
                    <span class="text-secondary" style="display: block; font-size: 13px; margin-bottom: 4px;">Founder response</span>
                    {user_reply}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)

    session_id = st.session_state.get("current_session_id", "local_session")

    # Check if verdict reached
    if state.get("verdict"):
        st.success("The panel has concluded the interrogation. Preparing final verdict...")
        st.session_state["active_page"] = "verdict"
        st.rerun()

    has_unanswered = len(transcript) > 0 and transcript[-1].get("user_reply") is None

    if has_unanswered:
        st.markdown('<div class="section-heading">Respond to objection</div>', unsafe_allow_html=True)
        with st.form(key="reply_form", clear_on_submit=True):
            user_response = st.text_area(
                "Your defense",
                label_visibility="collapsed",
                placeholder="Address the numbers, the moat, or the competitive differentiator directly...",
                height=120,
            )
            col_submit, _ = st.columns([4, 8])
            with col_submit:
                submitted = st.form_submit_button("Submit response", type="primary", use_container_width=True)

            if submitted and user_response.strip():
                with st.spinner("Deliberating on your response..."):
                    try:
                        res = api_client.reply_session(
                            session_id=session_id,
                            reply=user_response.strip(),
                            token=token,
                        )
                        updated_state = res["state"]
                        st.session_state["panel_state"] = updated_state
                        if updated_state.get("verdict"):
                            st.session_state["active_page"] = "verdict"
                        st.rerun()
                    except Exception as exc:
                        _handle_graph_error(exc)

    else:
        # Next turn or begin interrogation
        col_next, _ = st.columns([4, 8])
        with col_next:
            turn_label = "Proceed to next turn" if len(transcript) > 0 else "Begin interrogation"
            if st.button(turn_label, type="primary", use_container_width=True):
                with st.spinner("Panelist is preparing interrogation line..."):
                    try:
                        res = api_client.next_turn(
                            session_id=session_id,
                            token=token,
                        )
                        updated_state = res["state"]
                        st.session_state["panel_state"] = updated_state
                        if updated_state.get("verdict"):
                            st.session_state["active_page"] = "verdict"
                        st.rerun()
                    except Exception as exc:
                        _handle_graph_error(exc)
