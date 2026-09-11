"""Verdict report UI with stacked rows, severity pills, and PDF export."""

from __future__ import annotations

import streamlit as st
from export.pdf import generate_panel_pdf
from db.verdicts import save_verdict
from db.sessions import update_session_status


def render_verdict_view(user_id: str):
    state = st.session_state.get("panel_state")
    if not state or not state.get("verdict"):
        st.warning("No verdict available. Please complete a pitch session first.")
        if st.button("Submit a pitch", type="primary"):
            st.session_state["active_page"] = "pitch"
            st.rerun()
        return

    session_id = st.session_state.get("current_session_id", "local_session")
    verdict = state.get("verdict", [])

    st.markdown('<div class="page-title">Verdict</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="helper-text">The investment committee has concluded their assessment at {state.get("intensity", "normal").lower()} intensity. Vulnerabilities are ranked by risk severity below.</p>',
        unsafe_allow_html=True,
    )

    if session_id != "local_session":
        save_verdict(session_id, verdict)
        update_session_status(session_id, status="completed", round_count=state.get("llm_calls_made", 0))

    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)

    # Sort strictly by severity descending (§7)
    sorted_verdict = sorted(verdict, key=lambda x: int(x.get("severity", 3)), reverse=True)

    # Weaknesses listed as stacked rows separated by hairline dividers (not cards)
    for item in sorted_verdict:
        sev = int(item.get("severity", 3))
        issue = item.get("issue", "")
        fix = item.get("fix", "")

        st.markdown(
            f"""
            <div class="verdict-row">
                <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
                    <span class="severity-pill severity-pill-{sev}">Sev {sev}</span>
                    <span style="font-family: 'IBM Plex Sans', sans-serif; font-size: 16px; font-weight: 500; color: var(--text-primary); line-height: 1.4;">
                        {issue}
                    </span>
                </div>
                <div style="padding-left: 64px; font-family: 'IBM Plex Sans', sans-serif; font-size: 14px; color: var(--text-secondary); line-height: 1.5; max-width: 75ch;">
                    {fix}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)

    col_dl, col_new = st.columns([5, 5])
    with col_dl:
        pdf_bytes = generate_panel_pdf(
            pitch_text=state.get("pitch_text", ""),
            intensity=state.get("intensity", "normal"),
            transcript=state.get("transcript", []),
            verdict=verdict,
            session_id=session_id,
        )
        st.download_button(
            label=":material/download: Download PDF",
            data=pdf_bytes,
            file_name=f"devils_advocate_verdict_{session_id[:8]}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    with col_new:
        if st.button("Start new session", type="secondary", use_container_width=True):
            st.session_state["active_page"] = "pitch"
            st.session_state["panel_state"] = None
            st.session_state["compiled_graph"] = None
            st.rerun()

    # Full conversation recap expander
    with st.expander("Transcript review", expanded=False):
        for entry in state.get("transcript", []):
            st.markdown(f"**{entry.get('persona', '').upper()} Round {entry.get('round', 1)}**")
            st.markdown(f'<p class="constrained-text">{entry.get("question", "")}</p>', unsafe_allow_html=True)
            if entry.get("user_reply"):
                st.markdown(f'<p class="constrained-text text-secondary">Founder: {entry.get("user_reply")}</p>', unsafe_allow_html=True)
            st.markdown("---")
