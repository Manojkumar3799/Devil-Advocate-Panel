"""Session CRUD operations for Supabase."""

from __future__ import annotations

from typing import Any
from .client import get_supabase_client


def create_session(user_id: str, pitch_text: str, intensity: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("sessions").insert({
            "user_id": user_id,
            "pitch_text": pitch_text,
            "intensity": intensity,
            "status": "active",
        }).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error creating session: {e}")
    return None


def update_session_status(session_id: str, status: str, round_count: int | None = None) -> bool:
    client = get_supabase_client()
    if not client:
        return False
    try:
        payload: dict[str, Any] = {"status": status}
        if round_count is not None:
            payload["round_count"] = round_count
        client.table("sessions").update(payload).eq("id", session_id).execute()
        return True
    except Exception as e:
        print(f"Error updating session status: {e}")
        return False


def get_user_sessions(user_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = client.table("sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching user sessions: {e}")
        return []


def get_session(session_id: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("sessions").select("*").eq("id", session_id).single().execute()
        return res.data
    except Exception as e:
        print(f"Error fetching session {session_id}: {e}")
        return None
