"""Supabase client initialization and singleton wrapper."""

from __future__ import annotations

import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

_supabase_client = None


def get_supabase_client() -> Any:
    """Return an initialized Supabase client, or None if credentials are not configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        return None
