"""Session history and past evaluation view."""

from __future__ import annotations

import streamlit as st

try:
    from .. import api_client
except ImportError:
    import api_client


def render_history_view(user_id: str):
    token = st.session_state.get("sb_access_token", "")

    st.markdown('<div class="page-title">Pitch history</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="helper-text">Review previous interrogation transcripts and retrieve archived verdict reports.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)

    try:
        sessions = api_client.get_sessions(token=token)
    except Exception as exc:
        st.error(f"Failed to load pitch history: {exc}")
        return

    if not sessions:
        st.markdown('<p class="helper-text">No recorded sessions found. Submit a pitch to start your archive.</p>', unsafe_allow_html=True)
        if st.button("Submit a pitch", type="primary"):
            st.session_state["active_page"] = "pitch"
            st.rerun()
        return

    # List of past sessions per §7
    for s in sessions:
        s_id = s["id"]
        created = s.get("created_at", "")[:10]
        intensity = s.get("intensity", "normal")
        pitch_raw = s.get("pitch_text", "")
        # Truncate to one line
        pitch_snippet = (pitch_raw[:90] + "...") if len(pitch_raw) > 90 else pitch_raw

        with st.expander(f"{pitch_snippet}", expanded=False):
            st.markdown(
                f"""
                <div style="display: flex; gap: 16px; align-items: center; margin-bottom: 12px;">
                    <span class="severity-pill severity-pill-3">{intensity}</span>
                    <span class="data-mono" style="font-size: 13px;">{created}</span>
                </div>
                <div style="margin-bottom: 12px; font-size: 15px; color: var(--text-primary);">
                    {pitch_raw}
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_v, col_dl = st.columns([7, 3])
            try:
                verdict_data = api_client.get_verdict(session_id=s_id, token=token)
            except Exception:
                verdict_data = None

            with col_v:
                if verdict_data and verdict_data.get("weaknesses"):
                    st.markdown('<span style="font-weight: 500; font-size: 14px;">Identified flaws:</span>', unsafe_allow_html=True)
                    for w in verdict_data["weaknesses"]:
                        st.markdown(
                            f'<div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">• [Sev {w.get("severity")}] {w.get("issue")}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown('<span class="helper-text">No formal verdict saved.</span>', unsafe_allow_html=True)

            with col_dl:
                if verdict_data and verdict_data.get("weaknesses"):
                    try:
                        pdf_bytes = api_client.get_session_pdf(session_id=s_id, token=token)
                        st.download_button(
                            label=":material/download: Download PDF",
                            data=pdf_bytes,
                            file_name=f"verdict_{s_id[:8]}.pdf",
                            mime="application/pdf",
                            key=f"dl_{s_id}",
                            type="secondary",
                            use_container_width=True,
                        )
                    except Exception as exc:
                        st.markdown(f'<span class="helper-text">PDF error: {exc}</span>', unsafe_allow_html=True)
