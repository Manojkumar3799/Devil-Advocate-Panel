"""LangGraph StateGraph orchestration for the Devil's Advocate Panel."""

from __future__ import annotations

import json
import re
from typing import Any

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import (
    PanelState,
    Persona,
    PERSONA_ORDER,
    MAX_ROUNDS_PER_PERSONA,
    all_personas_done,
    call_budget_exhausted,
)
from .prompts import build_persona_system_prompt, VERDICT_SYSTEM_PROMPT
from .llm import PanelLLM
from .reasoning import extract_reasoning
from .tools import get_tools_for_persona

_RESOLVED_RE = re.compile(r"\n?RESOLVED:\s*(true|false)\s*$", re.IGNORECASE)


def _split_resolved_marker(answer: str) -> tuple[str, bool]:
    match = _RESOLVED_RE.search(answer)
    if not match:
        return answer.strip(), False
    resolved = match.group(1).lower() == "true"
    visible = _RESOLVED_RE.sub("", answer).strip()
    return visible, resolved


def make_persona_node(persona: Persona, llm: PanelLLM):
    def node(state: PanelState) -> PanelState:
        system_prompt = build_persona_system_prompt(persona, state["intensity"])
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Founder's Pitch:\n{state['pitch_text']}"),
        ]

        # Append prior conversation history for this persona
        for entry in state["transcript"]:
            if entry["persona"] != persona:
                continue
            messages.append(AIMessage(content=entry["question"]))
            if entry["user_reply"]:
                messages.append(HumanMessage(content=entry["user_reply"]))

        # If there's a pending user reply passed directly, include it
        if state.get("pending_user_reply"):
            messages.append(HumanMessage(content=state["pending_user_reply"]))
            state["pending_user_reply"] = None

        tools = get_tools_for_persona(persona, state["user_id"])
        response, provider_used = llm.invoke(messages, tools=tools)
        thinking, raw_answer = extract_reasoning(response, provider_used)
        visible_answer, resolved = _split_resolved_marker(raw_answer)

        status = state["persona_status"][persona]
        status["round"] += 1
        status["resolved"] = resolved

        transcript_entry = {
            "persona": persona,
            "round": status["round"],
            "thinking": thinking,
            "question": visible_answer,
            "user_reply": None,
            "provider_used": provider_used,
        }
        state["transcript"].append(transcript_entry)
        state["llm_calls_made"] += 1

        if resolved or status["round"] >= MAX_ROUNDS_PER_PERSONA or call_budget_exhausted(state):
            return state

        # Interrupt for human input
        reply = interrupt({
            "persona": persona,
            "question": visible_answer,
            "thinking": thinking,
            "round": status["round"],
        })
        state["transcript"][-1]["user_reply"] = reply
        return state

    return node


def router_node(state: PanelState) -> PanelState:
    while state["current_persona_idx"] < len(PERSONA_ORDER):
        persona = PERSONA_ORDER[state["current_persona_idx"]]
        status = state["persona_status"][persona]
        if status["resolved"] or status["round"] >= MAX_ROUNDS_PER_PERSONA:
            state["current_persona_idx"] += 1
            continue
        break
    return state


def route_after(state: PanelState) -> str:
    if call_budget_exhausted(state) or all_personas_done(state) or state["current_persona_idx"] >= len(PERSONA_ORDER):
        return "verdict"
    return PERSONA_ORDER[state["current_persona_idx"]]


def make_verdict_node(llm: PanelLLM):
    def node(state: PanelState) -> PanelState:
        transcript_lines = []
        for e in state["transcript"]:
            line = f"[{e['persona'].upper()} Round {e['round']}]\nChallenge: {e['question']}"
            if e.get("user_reply"):
                line += f"\nFounder Response: {e['user_reply']}"
            transcript_lines.append(line)
        
        transcript_text = "\n\n".join(transcript_lines)
        messages = [
            SystemMessage(content=VERDICT_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Intensity: {state['intensity']}\n\nPitch:\n{state['pitch_text']}\n\nTranscript:\n{transcript_text}"
            ),
        ]
        response, provider_used = llm.invoke(messages)
        state["llm_calls_made"] += 1
        
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)

        # Parse JSON output from content
        try:
            # Strip markdown json blocks if present
            cleaned = re.sub(r"^```json\s*", "", content.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"^```\s*$", "", cleaned, flags=re.MULTILINE).strip()
            parsed = json.loads(cleaned)
            state["verdict"] = parsed.get("weaknesses", [])
        except Exception:
            state["verdict"] = [
                {
                    "issue": "Synthesis completed with unstructured response.",
                    "severity": 3,
                    "fix": "Review transcript details and clarify unit economics."
                }
            ]
        return state

    return node


def build_graph(checkpointer=None):
    llm = PanelLLM()
    graph = StateGraph(PanelState)

    for persona in PERSONA_ORDER:
        graph.add_node(persona, make_persona_node(persona, llm))
    graph.add_node("router", router_node)
    graph.add_node("verdict", make_verdict_node(llm))

    graph.add_edge(START, PERSONA_ORDER[0])
    for persona in PERSONA_ORDER:
        graph.add_edge(persona, "router")
    
    graph.add_conditional_edges(
        "router",
        route_after,
        {**{p: p for p in PERSONA_ORDER}, "verdict": "verdict"},
    )
    graph.add_edge("verdict", END)

    if checkpointer is None:
        checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
