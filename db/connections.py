"""User connections management for OAuth tokens in Supabase."""

from __future__ import annotations

from typing import Any
from .client import get_supabase_client
from core.timing import timed_stage


def invalidate_user_connections_cache(user_id: str) -> None:
    """Clear the cached connections from session state."""
    try:
        import streamlit as st
        cache_key = f"cached_user_conns_{user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
    except Exception:
        pass


def get_cached_user_connections(user_id: str, force_refresh: bool = False) -> list[dict[str, Any]]:
    """Return user connections cached in st.session_state across reruns."""
    try:
        import streamlit as st
        cache_key = f"cached_user_conns_{user_id}"
        if not force_refresh and cache_key in st.session_state:
            return st.session_state[cache_key]

        with timed_stage(f"Supabase fetch user connections ({user_id[:8] if user_id else 'anon'})"):
            conns = get_user_connections(user_id)
        st.session_state[cache_key] = conns
        return conns
    except Exception:
        return get_user_connections(user_id)


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
        with timed_stage(f"Supabase save connection ({provider})"):
            payload = {
                "user_id": user_id,
                "provider": provider,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
                "metadata": metadata or {},
            }
            client.table("user_connections").upsert(payload, on_conflict="user_id,provider").execute()
        invalidate_user_connections_cache(user_id)
        return True
    except Exception as e:
        print(f"Error saving user connection: {e}")
        return False


def get_user_connections(user_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        with timed_stage(f"Supabase query user_connections ({user_id[:8] if user_id else 'anon'})"):
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
        with timed_stage(f"Supabase query connection ({provider})"):
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
        with timed_stage(f"Supabase delete connection ({provider})"):
            client.table("user_connections").delete().eq("user_id", user_id).eq("provider", provider).execute()
        invalidate_user_connections_cache(user_id)
        return True
    except Exception as e:
        print(f"Error deleting connection: {e}")
        return False

