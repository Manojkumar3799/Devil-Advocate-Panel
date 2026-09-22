"""
PDF export router for Devil's Advocate Panel.

Implements endpoint 7:
GET /api/sessions/{session_id}/pdf
"""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.deps import get_current_user
from db.sessions import get_session
from db.transcripts import get_session_transcript
from db.verdicts import get_verdict
from export.pdf import generate_panel_pdf

router = APIRouter(prefix="/sessions", tags=["pdf"])


@router.get("/{session_id}/pdf")
def download_session_pdf(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Generate and stream PDF report for the given session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    if session.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    transcript = get_session_transcript(session_id)
    verdict_row = get_verdict(session_id)
    verdict_weaknesses = verdict_row.get("weaknesses", []) if verdict_row else []

    try:
        pdf_bytes = generate_panel_pdf(
            pitch_text=session.get("pitch_text", ""),
            intensity=session.get("intensity", "normal"),
            transcript=transcript,
            verdict=verdict_weaknesses,
            session_id=session_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(exc)}",
        )

    filename = f"devils_advocate_verdict_{session_id[:8]}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
