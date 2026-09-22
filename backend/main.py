"""
FastAPI application entrypoint for Devil's Advocate Panel.

Configures:
- Lifespan startup to compile LangGraph once and store on app.state.graph
- CORS middleware with FRONTEND_BASE_URL
- Health check endpoint at /health
- Mounting of all routers under /api prefix
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

# Load .env for local development (no-op when vars are already set / on cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import connections, pdf, sessions, verdicts
from backend.schemas import HealthResponse
from core.config import get_secret
from core.graph import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compile the LangGraph StateGraph once on application startup."""
    app.state.graph = build_graph()
    yield


app = FastAPI(
    title="Devil's Advocate Panel API",
    description="FastAPI backend for multi-persona LangGraph pitch review",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
frontend_origin = (
    os.environ.get("FRONTEND_BASE_URL")
    or get_secret("FRONTEND_BASE_URL")
    or "http://localhost:8501"
)

allowed_origins = list(
    dict.fromkeys([
        frontend_origin,
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ])
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """Liveness probe returning application status."""
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# Mount Routers under /api
# ---------------------------------------------------------------------------
api_router = APIRouter(prefix="/api")
api_router.include_router(sessions.router)
api_router.include_router(verdicts.router)
api_router.include_router(pdf.router)
api_router.include_router(connections.router)

app.include_router(api_router)
