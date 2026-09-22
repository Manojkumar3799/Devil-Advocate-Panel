"""
Session management router for Devil's Advocate Panel.

Implements endpoints 1–5:
1. POST /api/sessions
2. POST /api/sessions/{session_id}/reply
3. POST /api/sessions/{session_id}/next-turn
4. GET  /api/sessions
5. GET  /api/sessions/{session_id}
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from langgraph.types import Command

from backend.deps import get_current_user
from backend.schemas import (
    PanelStateOut,
    SessionCreate,
    SessionCreateResponse,
    SessionReply,
    SessionStateResponse,
)
from core.state import initial_state
from db.connections import get_user_connections
from db.sessions import create_session, get_session, get_user_sessions, update_session_status
from db.transcripts import get_session_transcript, save_transcript_entry

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_graph(request: Request):
    """Retrieve compiled LangGraph from app.state.graph or fallback."""
    if hasattr(request.app.state, "graph") and request.app.state.graph is not None:
        return request.app.state.graph
    from core.graph import get_compiled_graph
    return get_compiled_graph()


def _verify_session_ownership(session_id: str, user_id: str) -> dict[str, Any]:
    """Fetch session from DB and ensure the caller owns it."""
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
    return session


# ---------------------------------------------------------------------------
# Endpoint 1: POST /api/sessions
# ---------------------------------------------------------------------------
@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_session(
    payload: SessionCreate,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Create a new session, initialize LangGraph state, and invoke once."""
    db_session = create_session(
        user_id=user_id,
        pitch_text=payload.pitch_text,
        intensity=payload.intensity,
    )
    if not db_session or "id" not in db_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session in database",
        )

    session_id = db_session["id"]
    user_conns = [c["provider"] for c in get_user_connections(user_id)]

    state = initial_state(
        pitch_text=payload.pitch_text,
        intensity=payload.intensity,
        connected_providers=user_conns,
        user_id=user_id,
    )

    config = {"configurable": {"thread_id": session_id}}
    graph = _get_graph(request)

    try:
        res_state = graph.invoke(state, config)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invoke panel graph: {str(exc)}",
        )

    return SessionCreateResponse(
        session_id=session_id,
        state=PanelStateOut.from_state(res_state),
    )


# ---------------------------------------------------------------------------
# Endpoint 2: POST /api/sessions/{session_id}/reply
# ---------------------------------------------------------------------------
@router.post("/{session_id}/reply", response_model=SessionStateResponse)
def reply_to_session(
    session_id: str,
    payload: SessionReply,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Submit user defense to the pending objection and resume graph execution."""
    _verify_session_ownership(session_id, user_id)
    config = {"configurable": {"thread_id": session_id}}
    graph = _get_graph(request)

    current_snapshot = graph.get_state(config)
    current_state = current_snapshot.values if current_snapshot else None
    if not current_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active graph state found for session {session_id}",
        )

    # Save transcript entry for the just-answered turn
    current_transcript = current_state.get("transcript", [])
    if current_transcript and current_transcript[-1].get("user_reply") is None:
        last_entry = current_transcript[-1]
        save_transcript_entry(
            session_id=session_id,
            persona=last_entry["persona"],
            round_num=last_entry["round"],
            thinking_text=last_entry.get("thinking", ""),
            question_text=last_entry.get("question", ""),
            user_reply=payload.reply.strip(),
            provider_used=last_entry.get("provider_used", ""),
        )

    try:
        updated_state = graph.invoke(Command(resume=payload.reply.strip()), config)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph resume failed: {str(exc)}",
        )

    if updated_state.get("verdict"):
        update_session_status(
            session_id,
            "completed",
            round_count=len(updated_state.get("transcript", [])),
        )

    return SessionStateResponse(state=PanelStateOut.from_state(updated_state))


# ---------------------------------------------------------------------------
# Endpoint 3: POST /api/sessions/{session_id}/next-turn
# ---------------------------------------------------------------------------
@router.post("/{session_id}/next-turn", response_model=SessionStateResponse)
def proceed_next_turn(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Proceed to the next persona turn without resending state."""
    _verify_session_ownership(session_id, user_id)
    config = {"configurable": {"thread_id": session_id}}
    graph = _get_graph(request)

    current_snapshot = graph.get_state(config)
    current_state = current_snapshot.values if current_snapshot else None
    if not current_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active graph state found for session {session_id}",
        )

    try:
        updated_state = graph.invoke(current_state, config)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph next-turn failed: {str(exc)}",
        )

    if updated_state.get("verdict"):
        update_session_status(
            session_id,
            "completed",
            round_count=len(updated_state.get("transcript", [])),
        )

    return SessionStateResponse(state=PanelStateOut.from_state(updated_state))


# ---------------------------------------------------------------------------
# Endpoint 4: GET /api/sessions
# ---------------------------------------------------------------------------
@router.get("", response_model=list[dict[str, Any]])
def list_user_sessions(user_id: str = Depends(get_current_user)):
    """Fetch past sessions for the authenticated user."""
    return get_user_sessions(user_id)


# ---------------------------------------------------------------------------
# Endpoint 5: GET /api/sessions/{session_id}
# ---------------------------------------------------------------------------
@router.get("/{session_id}")
def get_session_detail(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Fetch session row and full transcript."""
    session = _verify_session_ownership(session_id, user_id)
    transcript = get_session_transcript(session_id)
    return {"session": session, "transcript": transcript}
