"""OAuth authentication helpers and token exchange for third-party connectors."""

from __future__ import annotations

import urllib.parse
from typing import Any
import httpx

from core.config import get_secret, get_app_base_url


# Base OAuth configurations — credentials read via get_secret() so the same
# code works locally (via .env / python-dotenv) and on Streamlit Cloud (via st.secrets).
OAUTH_CONFIGS = {
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "client_id": None,   # resolved lazily via _cfg()
        "client_secret": None,
        "scope": "read:user repo",
    },
    "stripe": {
        "auth_url": "https://connect.stripe.com/oauth/authorize",
        "token_url": "https://connect.stripe.com/oauth/token",
        "client_id": None,
        "client_secret": None,
        "scope": "read_only",
    },
    "sheets": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "client_id": None,
        "client_secret": None,
        "scope": "https://www.googleapis.com/auth/spreadsheets.readonly",
    },
    "notion": {
        "auth_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "client_id": None,
        "client_secret": None,
        "scope": "",
    },
}

# Map provider keys to the secret names for their credentials
_PROVIDER_SECRET_KEYS: dict[str, tuple[str, str]] = {
    "github": ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"),
    "stripe": ("STRIPE_CLIENT_ID", "STRIPE_CLIENT_SECRET"),
    "sheets": ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"),
    "notion": ("NOTION_CLIENT_ID", "NOTION_CLIENT_SECRET"),
}


def _resolved_cfg(provider: str) -> dict[str, Any] | None:
    """Return the OAuth config for *provider* with credentials resolved from secrets."""
    base = OAUTH_CONFIGS.get(provider)
    if not base:
        return None
    id_key, secret_key = _PROVIDER_SECRET_KEYS[provider]
    cfg = dict(base)
    cfg["client_id"] = get_secret(id_key, "") or ""
    cfg["client_secret"] = get_secret(secret_key, "") or ""
    return cfg


def get_oauth_authorize_url(provider: str, redirect_uri: str, state: str) -> str | None:
    cfg = _resolved_cfg(provider)
    if not cfg or not cfg["client_id"]:
        return None

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    }
    if cfg["scope"]:
        params["scope"] = cfg["scope"]
    if provider == "sheets":
        params["access_type"] = "offline"
        params["prompt"] = "consent"

    return f"{cfg['auth_url']}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(provider: str, code: str, redirect_uri: str) -> dict[str, Any] | None:
    cfg = _resolved_cfg(provider)
    if not cfg or not cfg["client_id"] or not cfg["client_secret"]:
        return None

    headers = {"Accept": "application/json"}
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(cfg["token_url"], data=data, headers=headers)
            if resp.status_code == 200:
                result = resp.json()
                # GitHub returns errors inside a 200 JSON body with an "error" key
                if "error" in result:
                    print(f"OAuth token error for {provider}: {result}")
                    return None
                return result
            else:
                print(f"Failed to exchange OAuth token for {provider}: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Exception exchanging OAuth code for {provider}: {e}")
    return None
