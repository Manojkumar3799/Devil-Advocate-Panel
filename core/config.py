"""
Secrets abstraction: read from st.secrets (Streamlit Cloud) first,
fall back to os.environ (populated by python-dotenv for local dev).

When a key is found in st.secrets but NOT in os.environ, the helper
also writes it into os.environ so that downstream libraries (LangChain,
httpx, etc.) that only read environment variables pick it up automatically.
"""

from __future__ import annotations

import os
from typing import Any


def get_secret(key: str, default: str | None = None) -> str | None:
    """Return the value for *key* from st.secrets or os.environ.

    Resolution order:
    1. st.secrets[key]   — used on Streamlit Community Cloud
    2. os.environ[key]   — used locally via python-dotenv / .env file
    3. *default*         — fallback if neither is set
    """
    # Attempt st.secrets first (available only when running inside Streamlit)
    try:
        import streamlit as st
        val: Any = st.secrets.get(key)
        if val is not None:
            val_str = str(val)
            # Propagate into os.environ so LangChain/httpx pick it up
            if key not in os.environ:
                os.environ[key] = val_str
            return val_str
    except Exception:
        # st.secrets is not available (e.g. running in a plain Python script/test)
        pass

    return os.environ.get(key, default)


def get_app_base_url() -> str:
    """Return the base URL of the deployed application.

    Reads APP_BASE_URL from secrets/env; defaults to http://localhost:8501
    so local development requires no configuration change.
    """
    return get_secret("APP_BASE_URL", "http://localhost:8501") or "http://localhost:8501"
