"""Verdict CRUD operations for Supabase."""

from __future__ import annotations

from typing import Any
from .client import get_supabase_admin_client as get_supabase_client


def save_verdict(session_id: str, weaknesses: list[dict[str, Any]], pdf_url: str | None = None) -> dict[str, Any] | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("verdicts").upsert({
            "session_id": session_id,
            "weaknesses": weaknesses,
            "pdf_url": pdf_url,
        }).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error saving verdict: {e}")
    return None


def update_pdf_url(session_id: str, pdf_url: str) -> bool:
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("verdicts").update({"pdf_url": pdf_url}).eq("session_id", session_id).execute()
        return True
    except Exception as e:
        print(f"Error updating PDF url: {e}")
        return False


def get_verdict(session_id: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("verdicts").select("*").eq("session_id", session_id).single().execute()
        return res.data
    except Exception as e:
        print(f"Error getting verdict: {e}")
        return None
