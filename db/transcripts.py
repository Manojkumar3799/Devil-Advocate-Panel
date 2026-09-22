"""Transcript CRUD operations for Supabase."""

from __future__ import annotations

from typing import Any
from .client import get_supabase_admin_client as get_supabase_client


def save_transcript_entry(
    session_id: str,
    persona: str,
    round_num: int,
    thinking_text: str,
    question_text: str,
    user_reply: str | None = None,
    provider_used: str | None = None,
) -> dict[str, Any] | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("transcript_entries").insert({
            "session_id": session_id,
            "persona": persona,
            "round": round_num,
            "thinking_text": thinking_text,
            "question_text": question_text,
            "user_reply": user_reply,
            "provider_used": provider_used,
        }).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error saving transcript entry: {e}")
    return None


def get_session_transcript(session_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = (
            client.table("transcript_entries")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error getting session transcript: {e}")
        return []
