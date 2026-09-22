"""Verdict report UI with stacked rows, severity pills, and PDF export."""

from __future__ import annotations

import streamlit as st

try:
    from .. import api_client
except ImportError:
    import api_client


def render_verdict_view(user_id: str):
    token = st.session_state.get("sb_access_token", "")
    state = st.session_state.get("panel_state")
    session_id = st.session_state.get("current_session_id")

    # If state or verdict missing, attempt to fetch via API if session_id is present
    verdict = None
    if state and state.get("verdict"):
        verdict = state.get("verdict")
    elif session_id:
        try:
            verdict_data = api_client.get_verdict(session_id=session_id, token=token)
            verdict = verdict_data.get("weaknesses", [])
        except Exception:
            verdict = None

    if not verdict:
        st.warning("No verdict available. Please complete a pitch session first.")
        if st.button("Submit a pitch", type="primary"):
            st.session_state["active_page"] = "pitch"
            st.rerun()
        return

    session_id = session_id or "local_session"
    intensity = state.get("intensity", "normal") if state else "normal"

    st.markdown('<div class="page-title">Verdict</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="helper-text">The investment committee has concluded their assessment at {intensity.lower()} intensity. Vulnerabilities are ranked by risk severity below.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)

    # Sort strictly by severity descending
    sorted_verdict = sorted(verdict, key=lambda x: int(x.get("severity", 3)), reverse=True)

    sev_color_map = {
        1: "low",
        2: "low",
        3: "medium",
        4: "high",
        5: "critical",
    }

    # Weaknesses listed as glassmorphic cards with animated horizontal severity gauges
    for idx, item in enumerate(sorted_verdict):
        sev = int(item.get("severity", 3))
        issue = item.get("issue", "")
        fix = item.get("fix", "")
        target_pct = min(100, int((sev / 5.0) * 100))
        delay_ms = idx * 100
        sev_token = sev_color_map.get(sev, "medium")

        st.markdown(
            f"""
            <div class="verdict-row-card">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap;">
                    <span class="severity-pill severity-pill-{sev}">Sev {sev}</span>
                    <div class="severity-gauge-track" title="Severity {sev} of 5">
                        <div class="severity-gauge-fill" style="--target-width: {target_pct}%; background-color: var(--severity-{sev_token}); animation-delay: {delay_ms}ms;"></div>
                    </div>
                    <span style="font-family: 'IBM Plex Sans', sans-serif; font-size: 16px; font-weight: 500; color: var(--text-primary); line-height: 1.4; flex: 1;">
                        {issue}
                    </span>
                </div>
                <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 14px; color: var(--text-secondary); line-height: 1.5; max-width: 75ch; padding-left: 2px;">
                    {fix}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)

    col_dl, col_new = st.columns([5, 5])
    with col_dl:
        try:
            pdf_bytes = api_client.get_session_pdf(session_id=session_id, token=token)
            st.download_button(
                label=":material/download: Download PDF",
                data=pdf_bytes,
                file_name=f"devils_advocate_verdict_{session_id[:8]}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Could not prepare PDF: {exc}")

    with col_new:
        if st.button("Start new session", type="secondary", use_container_width=True):
            st.session_state["active_page"] = "pitch"
            st.session_state["panel_state"] = None
            st.session_state["current_session_id"] = None
            st.rerun()

    # Full conversation recap expander
    transcript = state.get("transcript", []) if state else []
    if transcript:
        with st.expander("Transcript review", expanded=False):
            for entry in transcript:
                st.markdown(f"**{entry.get('persona', '').upper()} Round {entry.get('round', 1)}**")
                st.markdown(f'<p class="constrained-text">{entry.get("question", "")}</p>', unsafe_allow_html=True)
                if entry.get("user_reply"):
                    st.markdown(f'<p class="constrained-text text-secondary">Founder: {entry.get("user_reply")}</p>', unsafe_allow_html=True)
                st.markdown("---")
