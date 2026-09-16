"""Supabase client initialization and singleton wrappers with resource caching."""

from __future__ import annotations

from typing import Any
from core.config import get_secret
from core.timing import timed_stage

_supabase_client = None
_supabase_admin_client = None


def _create_client_raw(url: str, key: str) -> Any:
    from supabase import create_client
    return create_client(url, key)


try:
    import streamlit as st
    _create_client_cached = st.cache_resource(show_spinner=False)(_create_client_raw)
except Exception:
    _create_client_cached = _create_client_raw


def get_supabase_client() -> Any:
    """Return an initialized Supabase user client using the anon key (SUPABASE_KEY).

    Cached via @st.cache_resource across Streamlit reruns.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    supabase_url = get_secret("SUPABASE_URL")
    supabase_key = get_secret("SUPABASE_KEY") or get_secret("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        return None

    try:
        with timed_stage("Supabase user client init"):
            _supabase_client = _create_client_cached(supabase_url, supabase_key)
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
        with timed_stage("Supabase admin client init"):
            _supabase_admin_client = _create_client_cached(supabase_url, admin_key)
        return _supabase_admin_client
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase admin client: {e}")
        return None

