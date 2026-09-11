"""
LangGraph assembly for the Devil's Advocate Panel.

Flow (sequential personas, per user decision):
  persona_node(vc) --interrupt--> [user replies] --> persona_node(vc) reacts
    --> router --> persona_node(analyst) --interrupt--> ... --> router
    --> persona_node(realist) --interrupt--> ... --> router --> verdict_node

`interrupt()` pauses the graph after a persona asks its question, waiting for
the Streamlit layer to resume with the founder's reply (see run_demo.py for
the resume pattern). This is the standard LangGraph human-in-the-loop pattern
and is what lets the same graph definition work in a CLI script now and in
Streamlit later without restructuring.
"""

from __future__ import annotations

import json
import re

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
from .llm import PanelLLM, extract_reasoning

_RESOLVED_RE = re.compile(r"\n?RESOLVED:\s*(true|false)\s*$", re.IGNORECASE)


def _split_resolved_marker(answer: str) -> tuple[str, bool]:
    """Personas are instructed to end their answer with a RESOLVED: true/false
    marker line. Strip it out for display and parse the flag. Defaults to
    False (keep grilling) if the model forgot the marker -- fail toward more
    scrutiny, not less."""
    match = _RESOLVED_RE.search(answer)
    if not match:
        return answer.strip(), False
    resolved = match.group(1).lower() == "true"
    visible = _RESOLVED_RE.sub("", answer).strip()
    return visible, resolved


# ---------------------------------------------------------------------------
# Tools -- gated per persona by what the founder has connected.
# github/stripe/sheets/notion are MCP-backed (stubbed here; swap in real MCP
# client calls once the OAuth connector layer is wired up). Tavily is bound
# directly as a native LangChain tool, per the earlier design decision.
# ---------------------------------------------------------------------------


def _mock_mcp_tool(name: str, description: str):
    """Placeholder standing in for a real MCP tool call. Replace with the
    actual MCP client invocation once user_connections + MCP wiring exists."""
    from langchain_core.tools import tool

    @tool(name, description=description)
    def _tool(query: str) -> str:
        return f"[MOCK {name} result for: {query}] -- replace with real MCP call"

    return _tool


def _rag_retrieve_tool():
    """Placeholder for the static benchmark-corpus retriever (pgvector).
    Replace with a real Supabase/pgvector similarity search."""
    from langchain_core.tools import tool

    @tool("benchmark_corpus_search", description="Search startup benchmark/failure-case corpus")
    def _tool(query: str) -> str:
        return f"[MOCK benchmark corpus result for: {query}]"

    return _tool


def _tools_for(persona: Persona, connected_providers: list[str]):
    tools = []
    if persona == "vc" and "github" in connected_providers:
        tools.append(_mock_mcp_tool("github_activity", "Check repo commit activity, age, contributors"))
    if persona == "analyst":
        if "stripe" in connected_providers:
            tools.append(_mock_mcp_tool("stripe_revenue", "Check real MRR, revenue, churn"))
        if "sheets" in connected_providers:
            tools.append(_mock_mcp_tool("sheets_model", "Read the founder's financial model spreadsheet"))
        tools.append(_rag_retrieve_tool())
    if persona == "realist":
        if "notion" in connected_providers:
            tools.append(_mock_mcp_tool("notion_research", "Read the founder's market research docs"))
        try:
            from langchain_tavily import TavilySearch

            tools.append(TavilySearch(max_results=5))
        except ImportError:
            pass  # TAVILY_API_KEY not configured / package not installed -- skip silently
    return tools


# ---------------------------------------------------------------------------
# Persona node factory
# ---------------------------------------------------------------------------


def make_persona_node(persona: Persona, llm: PanelLLM):
    def node(state: PanelState) -> PanelState:
        system_prompt = build_persona_system_prompt(persona, state["intensity"])

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=state["pitch_text"])]
        # fold in this persona's prior turns for context
        for entry in state["transcript"]:
            if entry["persona"] != persona:
                continue
            messages.append(AIMessage(content=entry["question"]))
            if entry["user_reply"]:
                messages.append(HumanMessage(content=entry["user_reply"]))

        tools = _tools_for(persona, state["connected_providers"])
        response, provider_used = llm.invoke(messages, tools=tools)
        thinking, raw_answer = extract_reasoning(response, provider_used)
        visible_answer, resolved = _split_resolved_marker(raw_answer)

        status = state["persona_status"][persona]
        status["round"] += 1
        status["resolved"] = resolved

        state["transcript"].append(
            {
                "persona": persona,
                "round": status["round"],
                "thinking": thinking,
                "question": visible_answer,
                "user_reply": None,
                "provider_used": provider_used,
            }
        )
        state["llm_calls_made"] += 1

        if resolved or status["round"] >= MAX_ROUNDS_PER_PERSONA:
            return state  # router will advance to the next persona

        # pause here -- Streamlit resumes this with the founder's reply
        reply = interrupt({"persona": persona, "question": visible_answer})
        state["transcript"][-1]["user_reply"] = reply
        return state

    return node


# ---------------------------------------------------------------------------
# Router -- advances current_persona_idx, or routes to verdict
# ---------------------------------------------------------------------------


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
    if call_budget_exhausted(state) or all_personas_done(state):
        return "verdict"
    return PERSONA_ORDER[state["current_persona_idx"]]


# ---------------------------------------------------------------------------
# Verdict node
# ---------------------------------------------------------------------------


def make_verdict_node(llm: PanelLLM):
    def node(state: PanelState) -> PanelState:
        transcript_text = "\n\n".join(
            f"[{e['persona']} round {e['round']}] Q: {e['question']}\nFounder reply: {e['user_reply']}"
            for e in state["transcript"]
        )
        messages = [
            SystemMessage(content=VERDICT_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Intensity: {state['intensity']}\n\nPitch:\n{state['pitch_text']}\n\nTranscript:\n{transcript_text}"
            ),
        ]
        response, provider_used = llm.invoke(messages)
        state["llm_calls_made"] += 1
        try:
            parsed = json.loads(response.content)
            state["verdict"] = parsed["weaknesses"]
        except (json.JSONDecodeError, KeyError):
            state["verdict"] = [
                {"issue": "Verdict parsing failed", "severity": 3, "fix": "Retry verdict generation"}
            ]
        return state

    return node


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def build_graph():
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

    checkpointer = MemorySaver()  # swap for a Postgres/Supabase checkpointer later
    return graph.compile(checkpointer=checkpointer)
