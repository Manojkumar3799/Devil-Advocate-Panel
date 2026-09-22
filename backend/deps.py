"""
Authentication dependencies for the Devil's Advocate Panel FastAPI backend.

Verifies Supabase JWT bearer tokens passed from the frontend and returns user_id.
The admin client is used strictly for JWT verification; data operations go
through standard db client functions.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db.client import get_supabase_admin_client

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Verify Supabase JWT bearer token and extract user_id.

    Raises HTTPException(401) on missing, invalid, or expired tokens.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    admin_client = get_supabase_admin_client()
    if not admin_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable (Supabase admin client not initialized)",
        )

    try:
        user_response = admin_client.auth.get_user(token)
        if not user_response or not getattr(user_response, "user", None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = str(user_response.user.id)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user in token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
