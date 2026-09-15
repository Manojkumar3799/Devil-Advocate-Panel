"""Live interrogation session UI handling conversational turns, thinking traces, and replies."""

from __future__ import annotations

import streamlit as st
from langgraph.types import Command
from core.graph import build_graph
from core.state import PERSONA_ORDER
from db.transcripts import save_transcript_entry
from db.sessions import update_session_status
from .components import render_progress_tracker

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
    """Show a graceful Streamlit error banner for graph/LLM failures.

    Preserves any transcript already in session_state — does NOT wipe it.
    Distinguishes billing/auth errors (non-retryable) from transient ones.
    """
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
            "The rounds completed so far are preserved — you can try again below.",
            icon=":material/warning:",
        )
        if st.button("Retry last turn", key="retry_turn_btn", type="secondary"):
            st.rerun()


def render_session_view(user_id: str):
    state = st.session_state.get("panel_state")
    if not state:
        st.warning("No active session found. Please submit a pitch first.")
        if st.button("Submit a pitch", type="primary"):
            st.session_state["active_page"] = "pitch"
            st.rerun()
        return

    # 3 Progress bars fixed at the top per persona (§5: Motion 3)
    render_progress_tracker(state.get("persona_status", {}))

    # Pitch overview expander
    with st.expander("Case file / Submitted pitch", expanded=False):
        st.markdown(f'<p class="constrained-text">{state["pitch_text"]}</p>', unsafe_allow_html=True)

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

        # Is this the latest turn? If so, apply entrance animation (§5: Motion 2)
        is_latest = (i == total_entries - 1)
        card_class = "interrogation-card latest-turn" if is_latest else "interrogation-card"

        # Persona card with 4px radius, 1px solid hairline border
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

        # Reasoning trace in restyled st.expander (collapsed by default, per-persona)
        if thinking:
            with st.expander("Reasoning", expanded=False):
                st.markdown(f'<p class="constrained-text text-secondary" style="font-size: 14px;">{thinking}</p>', unsafe_allow_html=True)

        # Question text in IBM Plex Sans 16px
        st.markdown(f'<div class="question-text">{question}</div>', unsafe_allow_html=True)

        # Founder reply in visually distinct sub-block (--bg-elevated, no border)
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
                transcript[-1]["user_reply"] = user_response.strip()

                if session_id != "local_session":
                    save_transcript_entry(
                        session_id=session_id,
                        persona=transcript[-1]["persona"],
                        round_num=transcript[-1]["round"],
                        thinking_text=transcript[-1].get("thinking", ""),
                        question_text=transcript[-1].get("question", ""),
                        user_reply=user_response.strip(),
                        provider_used=transcript[-1].get("provider_used", ""),
                    )

                with st.spinner("Reviewing your response..."):
                    graph = st.session_state.get("compiled_graph")
                    if not graph:
                        graph = build_graph()
                        st.session_state["compiled_graph"] = graph

                    config = {"configurable": {"thread_id": session_id}}
                    try:
                        updated_state = graph.invoke(Command(resume=user_response.strip()), config=config)
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
                with st.spinner("Panelist is analyzing your pitch..."):
                    graph = st.session_state.get("compiled_graph")
                    if not graph:
                        graph = build_graph()
                        st.session_state["compiled_graph"] = graph

                    config = {"configurable": {"thread_id": session_id}}
                    try:
                        updated_state = graph.invoke(state, config=config)
                        st.session_state["panel_state"] = updated_state
                        if updated_state.get("verdict"):
                            st.session_state["active_page"] = "verdict"
                        st.rerun()
                    except Exception as exc:
                        _handle_graph_error(exc)
