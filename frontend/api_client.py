"""
Frontend API Client for Devil's Advocate Panel.

Makes HTTP requests to the FastAPI backend.
Every function receives the bearer token as an explicit argument.
st.session_state is NEVER read or referenced within this module.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

BACKEND_BASE_URL = (
    os.environ.get("BACKEND_BASE_URL")
    or "http://localhost:8000"
).rstrip("/")

DEFAULT_TIMEOUT = 120.0


class APIError(Exception):
    """Exception raised for API request failures."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


def _get_client() -> httpx.Client:
    """Create an httpx client with configured base URL and timeout."""
    return httpx.Client(base_url=BACKEND_BASE_URL, timeout=DEFAULT_TIMEOUT)


def _auth_headers(token: str) -> dict[str, str]:
    """Format bearer authentication header."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def _handle_response(resp: httpx.Response) -> Any:
    """Handle error status codes and extract JSON content."""
    if resp.is_success:
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return resp.content
    try:
        err_data = resp.json()
        detail = err_data.get("detail", resp.text)
    except Exception:
        detail = resp.text or resp.reason_phrase
    raise APIError(status_code=resp.status_code, detail=str(detail))


# ---------------------------------------------------------------------------
# Endpoint 1: POST /api/sessions
# ---------------------------------------------------------------------------
def create_session(pitch_text: str, intensity: str, token: str) -> dict[str, Any]:
    """Create a new session, run initial graph turn, and return session_id and state."""
    with _get_client() as client:
        resp = client.post(
            "/api/sessions",
            headers=_auth_headers(token),
            json={"pitch_text": pitch_text, "intensity": intensity},
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 2: POST /api/sessions/{session_id}/reply
# ---------------------------------------------------------------------------
def reply_session(session_id: str, reply: str, token: str) -> dict[str, Any]:
    """Submit founder reply to objection and resume graph execution."""
    with _get_client() as client:
        resp = client.post(
            f"/api/sessions/{session_id}/reply",
            headers=_auth_headers(token),
            json={"reply": reply},
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 3: POST /api/sessions/{session_id}/next-turn
# ---------------------------------------------------------------------------
def next_turn(session_id: str, token: str) -> dict[str, Any]:
    """Advance to the next persona question without resending state."""
    with _get_client() as client:
        resp = client.post(
            f"/api/sessions/{session_id}/next-turn",
            headers=_auth_headers(token),
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 4: GET /api/sessions
# ---------------------------------------------------------------------------
def get_sessions(token: str) -> list[dict[str, Any]]:
    """List all sessions belonging to the authenticated user."""
    with _get_client() as client:
        resp = client.get(
            "/api/sessions",
            headers=_auth_headers(token),
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 5: GET /api/sessions/{session_id}
# ---------------------------------------------------------------------------
def get_session(session_id: str, token: str) -> dict[str, Any]:
    """Fetch session details and full conversation transcript."""
    with _get_client() as client:
        resp = client.get(
            f"/api/sessions/{session_id}",
            headers=_auth_headers(token),
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 6: GET /api/sessions/{session_id}/verdict
# ---------------------------------------------------------------------------
def get_verdict(session_id: str, token: str) -> dict[str, Any]:
    """Fetch verdict assessment for a completed session."""
    with _get_client() as client:
        resp = client.get(
            f"/api/sessions/{session_id}/verdict",
            headers=_auth_headers(token),
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 7: GET /api/sessions/{session_id}/pdf
# ---------------------------------------------------------------------------
def get_session_pdf(session_id: str, token: str) -> bytes:
    """Download compiled PDF report bytes for a session."""
    headers = {"Authorization": f"Bearer {token}"}
    with _get_client() as client:
        resp = client.get(
            f"/api/sessions/{session_id}/pdf",
            headers=headers,
        )
        if not resp.is_success:
            _handle_response(resp)
        return resp.content


# ---------------------------------------------------------------------------
# Endpoint 8: GET /api/connections
# ---------------------------------------------------------------------------
def get_connections(token: str) -> list[dict[str, Any]]:
    """List connected data sources for the authenticated user (no tokens exposed)."""
    with _get_client() as client:
        resp = client.get(
            "/api/connections",
            headers=_auth_headers(token),
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 9: GET /api/connections/{provider}/authorize-url
# ---------------------------------------------------------------------------
def get_authorize_url(provider: str, token: str) -> str:
    """Retrieve OAuth authorization URL for the specified provider."""
    with _get_client() as client:
        resp = client.get(
            f"/api/connections/{provider}/authorize-url",
            headers=_auth_headers(token),
        )
        data = _handle_response(resp)
        return data["url"]


# ---------------------------------------------------------------------------
# Endpoint 10: POST /api/connections/{provider}/exchange
# ---------------------------------------------------------------------------
def exchange_connection(
    provider: str,
    code: str,
    state: str,
    redirect_uri: str,
    token: str,
) -> dict[str, Any]:
    """Exchange OAuth authorization code for credentials and save server-side."""
    with _get_client() as client:
        resp = client.post(
            f"/api/connections/{provider}/exchange",
            headers=_auth_headers(token),
            json={
                "code": code,
                "state": state,
                "redirect_uri": redirect_uri,
            },
        )
        return _handle_response(resp)


# ---------------------------------------------------------------------------
# Endpoint 11: DELETE /api/connections/{provider}
# ---------------------------------------------------------------------------
def delete_connection(provider: str, token: str) -> dict[str, Any]:
    """Disconnect and delete stored credentials for the specified provider."""
    with _get_client() as client:
        resp = client.delete(
            f"/api/connections/{provider}",
            headers=_auth_headers(token),
        )
        return _handle_response(resp)
