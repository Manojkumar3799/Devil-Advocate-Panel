"""LangGraph state schema for Devil's Advocate Panel."""

from __future__ import annotations

from typing import Literal, TypedDict

Intensity = Literal["light", "normal", "heavy", "no_mercy"]
Persona = Literal["vc", "analyst", "realist"]

PERSONA_ORDER: list[Persona] = ["vc", "analyst", "realist"]
MAX_ROUNDS_PER_PERSONA = 3
MAX_LLM_CALLS_PER_SESSION = 12


class PersonaStatus(TypedDict):
    resolved: bool
    round: int  # rounds completed so far for this persona


class TranscriptEntry(TypedDict):
    persona: Persona | Literal["verdict"]
    round: int
    thinking: str
    question: str
    user_reply: str | None
    provider_used: str


class Weakness(TypedDict):
    issue: str
    severity: int  # 1-5
    fix: str


class PanelState(TypedDict):
    pitch_text: str
    intensity: Intensity
    user_id: str                        # needed by tools to look up real OAuth tokens
    connected_providers: list[str]      # e.g. ["github", "stripe", "sheets", "notion"]

    persona_status: dict[Persona, PersonaStatus]
    current_persona_idx: int  # index into PERSONA_ORDER -- drives sequential order

    transcript: list[TranscriptEntry]
    llm_calls_made: int

    pending_user_reply: str | None  # set by the UI layer, cleared once consumed

    verdict: list[Weakness] | None


def initial_state(pitch_text: str, intensity: Intensity = "normal", connected_providers: list[str] | None = None, user_id: str = "") -> PanelState:
    return PanelState(
        pitch_text=pitch_text,
        intensity=intensity,
        user_id=user_id,
        connected_providers=connected_providers or [],
        persona_status={p: PersonaStatus(resolved=False, round=0) for p in PERSONA_ORDER},
        current_persona_idx=0,
        transcript=[],
        llm_calls_made=0,
        pending_user_reply=None,
        verdict=None,
    )


def all_personas_done(state: PanelState) -> bool:
    return all(
        s["resolved"] or s["round"] >= MAX_ROUNDS_PER_PERSONA
        for s in state["persona_status"].values()
    )


def call_budget_exhausted(state: PanelState) -> bool:
    return state["llm_calls_made"] >= MAX_LLM_CALLS_PER_SESSION
