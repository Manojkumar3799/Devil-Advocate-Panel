"""OAuth authentication helpers and token exchange for third-party connectors."""

from __future__ import annotations

import os
import urllib.parse
from typing import Any
import httpx
from dotenv import load_dotenv

load_dotenv()

# Base OAuth configurations
OAUTH_CONFIGS = {
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
        "client_secret": os.environ.get("GITHUB_CLIENT_SECRET", ""),
        "scope": "read:user repo",
    },
    "stripe": {
        "auth_url": "https://connect.stripe.com/oauth/authorize",
        "token_url": "https://connect.stripe.com/oauth/token",
        "client_id": os.environ.get("STRIPE_CLIENT_ID", ""),
        "client_secret": os.environ.get("STRIPE_CLIENT_SECRET", ""),
        "scope": "read_only",
    },
    "sheets": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        "scope": "https://www.googleapis.com/auth/spreadsheets.readonly",
    },
    "notion": {
        "auth_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "client_id": os.environ.get("NOTION_CLIENT_ID", ""),
        "client_secret": os.environ.get("NOTION_CLIENT_SECRET", ""),
        "scope": "",
    },
}


def get_oauth_authorize_url(provider: str, redirect_uri: str, state: str) -> str | None:
    cfg = OAUTH_CONFIGS.get(provider)
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
    cfg = OAUTH_CONFIGS.get(provider)
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
                return resp.json()
            else:
                print(f"Failed to exchange OAuth token for {provider}: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Exception exchanging OAuth code for {provider}: {e}")
    return None
