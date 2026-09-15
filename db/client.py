"""Supabase client initialization and singleton wrappers."""

from __future__ import annotations

from typing import Any
from core.config import get_secret

_supabase_client = None
_supabase_admin_client = None


def get_supabase_client() -> Any:
    """Return an initialized Supabase user client using the anon key (SUPABASE_KEY).

    Prefers SUPABASE_KEY so that PostgreSQL Row Level Security (RLS) policies
    are enforced. Falls back to SUPABASE_SERVICE_KEY only if anon key is not set.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    supabase_url = get_secret("SUPABASE_URL")
    supabase_key = get_secret("SUPABASE_KEY") or get_secret("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        return None


def get_supabase_admin_client() -> Any:
    """Return an initialized Supabase admin client using the service role key (SUPABASE_SERVICE_KEY).

    Bypasses RLS. Intended strictly for administrative/batch operations (e.g. database seeding).
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    supabase_url = get_secret("SUPABASE_URL")
    admin_key = get_secret("SUPABASE_SERVICE_KEY") or get_secret("SUPABASE_KEY")

    if not supabase_url or not admin_key:
        return None

    try:
        from supabase import create_client
        _supabase_admin_client = create_client(supabase_url, admin_key)
        return _supabase_admin_client
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase admin client: {e}")
        return None
