"""User connections management for OAuth tokens in Supabase."""

from __future__ import annotations

from typing import Any
from .client import get_supabase_client


def save_user_connection(
    user_id: str,
    provider: str,
    access_token: str,
    refresh_token: str | None = None,
    expires_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    client = get_supabase_client()
    if not client:
        return False
    try:
        payload = {
            "user_id": user_id,
            "provider": provider,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "metadata": metadata or {},
        }
        client.table("user_connections").upsert(payload, on_conflict="user_id,provider").execute()
        return True
    except Exception as e:
        print(f"Error saving user connection: {e}")
        return False


def get_user_connections(user_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = client.table("user_connections").select("*").eq("user_id", user_id).execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching user connections: {e}")
        return []


def get_connection(user_id: str, provider: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = (
            client.table("user_connections")
            .select("*")
            .eq("user_id", user_id)
            .eq("provider", provider)
            .maybe_single()
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"Error fetching connection {provider}: {e}")
        return None


def delete_connection(user_id: str, provider: str) -> bool:
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("user_connections").delete().eq("user_id", user_id).eq("provider", provider).execute()
        return True
    except Exception as e:
        print(f"Error deleting connection: {e}")
        return False
