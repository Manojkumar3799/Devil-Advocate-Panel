"""
Pydantic schemas for the Devil's Advocate Panel backend.

All models mirror core/state.py TypedDicts field-for-field so the LangGraph
state can be serialised to JSON and sent to the Streamlit frontend unchanged.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared literals — kept identical to core/state.py
# ---------------------------------------------------------------------------

Intensity = Literal["light", "normal", "heavy", "no_mercy"]
Persona = Literal["vc", "analyst", "realist"]


# ---------------------------------------------------------------------------
# State models (mirroring core/state.py TypedDicts field-for-field)
# ---------------------------------------------------------------------------

class PersonaStatusOut(BaseModel):
    """Mirrors core.state.PersonaStatus"""
    resolved: bool
    round: int


class TranscriptEntryOut(BaseModel):
    """Mirrors core.state.TranscriptEntry"""
    persona: Persona | Literal["verdict"]
    round: int
    thinking: str
    question: str
    user_reply: str | None = None
    provider_used: str


class WeaknessOut(BaseModel):
    """Mirrors core.state.Weakness"""
    issue: str
    severity: int  # 1–5
    fix: str


class PanelStateOut(BaseModel):
    """Mirrors core.state.PanelState"""
    pitch_text: str
    intensity: Intensity
    user_id: str
    connected_providers: list[str]
    persona_status: dict[str, PersonaStatusOut]
    current_persona_idx: int
    transcript: list[TranscriptEntryOut]
    llm_calls_made: int
    pending_user_reply: str | None = None
    verdict: list[WeaknessOut] | None = None

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "PanelStateOut":
        """Convert a raw LangGraph PanelState dict to this Pydantic model."""
        return cls(
            pitch_text=state["pitch_text"],
            intensity=state["intensity"],
            user_id=state["user_id"],
            connected_providers=state["connected_providers"],
            persona_status={
                k: PersonaStatusOut(**v)
                for k, v in state["persona_status"].items()
            },
            current_persona_idx=state["current_persona_idx"],
            transcript=[TranscriptEntryOut(**e) for e in state["transcript"]],
            llm_calls_made=state["llm_calls_made"],
            pending_user_reply=state.get("pending_user_reply"),
            verdict=(
                [WeaknessOut(**w) for w in state["verdict"]]
                if state.get("verdict") else None
            ),
        )


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    pitch_text: str
    intensity: Literal["light", "normal", "heavy", "no_mercy"] = "normal"


class SessionReply(BaseModel):
    reply: str


class ConnectionExchange(BaseModel):
    code: str
    state: str
    redirect_uri: str


# ---------------------------------------------------------------------------
# Response Models / Envelopes
# ---------------------------------------------------------------------------

class SessionCreateResponse(BaseModel):
    session_id: str
    state: PanelStateOut


class SessionStateResponse(BaseModel):
    state: PanelStateOut


class ConnectionResponse(BaseModel):
    provider: str
    connected: bool = True
    created_at: str | None = None


class AuthorizeUrlResponse(BaseModel):
    url: str


class ExchangeResponse(BaseModel):
    success: bool
    provider: str


class HealthResponse(BaseModel):
    status: str
