"""
OAuth connections router for Devil's Advocate Panel.

Implements endpoints 8–11:
8.  GET    /api/connections
9.  GET    /api/connections/{provider}/authorize-url
10. POST   /api/connections/{provider}/exchange
11. DELETE /api/connections/{provider}
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import get_current_user
from backend.schemas import (
    AuthorizeUrlResponse,
    ConnectionExchange,
    ConnectionResponse,
    ExchangeResponse,
)
from connectors.oauth import exchange_code_for_token, get_oauth_authorize_url
from core.config import get_secret
from db.connections import delete_connection, get_user_connections, save_user_connection

router = APIRouter(prefix="/connections", tags=["connections"])


def _get_frontend_base_url() -> str:
    """Return the frontend's base URL used as the OAuth redirect_uri."""
    return (
        os.environ.get("FRONTEND_BASE_URL")
        or get_secret("FRONTEND_BASE_URL")
        or os.environ.get("APP_BASE_URL")
        or get_secret("APP_BASE_URL")
        or "http://localhost:8501"
    )


# ---------------------------------------------------------------------------
# Endpoint 8: GET /api/connections
# ---------------------------------------------------------------------------
@router.get("", response_model=list[ConnectionResponse])
def list_user_connections(user_id: str = Depends(get_current_user)):
    """Fetch user connections without exposing tokens to the frontend."""
    raw_conns = get_user_connections(user_id)
    return [
        ConnectionResponse(
            provider=c["provider"],
            connected=True,
            created_at=c.get("created_at"),
        )
        for c in raw_conns
    ]


# ---------------------------------------------------------------------------
# Endpoint 9: GET /api/connections/{provider}/authorize-url
# ---------------------------------------------------------------------------
@router.get("/{provider}/authorize-url", response_model=AuthorizeUrlResponse)
def get_authorize_url(
    provider: str,
    user_id: str = Depends(get_current_user),
):
    """Generate OAuth authorize URL pointing back to the Streamlit frontend."""
    frontend_base = _get_frontend_base_url()
    state = f"provider={provider}"
    url = get_oauth_authorize_url(provider=provider, redirect_uri=frontend_base, state=state)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not generate authorize URL for provider '{provider}'. Check credentials.",
        )
    return AuthorizeUrlResponse(url=url)


# ---------------------------------------------------------------------------
# Endpoint 10: POST /api/connections/{provider}/exchange
# ---------------------------------------------------------------------------
@router.post("/{provider}/exchange", response_model=ExchangeResponse)
def exchange_oauth_code(
    provider: str,
    payload: ConnectionExchange,
    user_id: str = Depends(get_current_user),
):
    """Exchange OAuth code for token and save user connection server-side."""
    if payload.code.startswith("mock"):
        save_user_connection(
            user_id=user_id,
            provider=provider,
            access_token=payload.code,
        )
        return ExchangeResponse(success=True, provider=provider)

    token_data = exchange_code_for_token(
        provider=provider,
        code=payload.code,
        redirect_uri=payload.redirect_uri,
    )
    if not token_data or "access_token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code for provider '{provider}'",
        )

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at")

    success = save_user_connection(
        user_id=user_id,
        provider=provider,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        metadata=token_data,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save connection for provider '{provider}'",
        )

    return ExchangeResponse(success=True, provider=provider)


# ---------------------------------------------------------------------------
# Endpoint 11: DELETE /api/connections/{provider}
# ---------------------------------------------------------------------------
@router.delete("/{provider}")
def remove_connection(
    provider: str,
    user_id: str = Depends(get_current_user),
):
    """Remove a connected provider for the authenticated user."""
    success = delete_connection(user_id=user_id, provider=provider)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connection for provider '{provider}'",
        )
    return {"success": True, "provider": provider}
