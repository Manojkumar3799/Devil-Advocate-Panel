"""
Verdicts router for Devil's Advocate Panel.

Implements endpoint 6:
GET /api/sessions/{session_id}/verdict
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import get_current_user
from db.sessions import get_session
from db.verdicts import get_verdict

router = APIRouter(prefix="/sessions", tags=["verdicts"])


@router.get("/{session_id}/verdict")
def get_session_verdict(
    session_id: str,
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch verdict for a session, verifying session ownership."""
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

    verdict = get_verdict(session_id)
    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict for session '{session_id}' not found",
        )

    return verdict
