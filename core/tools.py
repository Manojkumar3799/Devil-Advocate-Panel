"""Tool definitions for the Devil's Advocate Panel."""

from __future__ import annotations

import os
from typing import Callable
from langchain_core.tools import tool
from .state import Persona


def _mock_mcp_tool(name: str, description: str) -> Callable:
    """Mock connector tool for Phase 1. Replaced with live connectors in Phase 4."""
    @tool(name, description=description)
    def _tool(query: str) -> str:
        return f"[MOCK {name} data for query: '{query}']"
    return _tool


def _rag_retrieve_tool() -> Callable:
    """Mock benchmark retriever tool for Phase 1. Replaced in Phase 5."""
    @tool("benchmark_corpus_search", description="Search startup benchmark, unit economics, and post-mortem corpus")
    def _tool(query: str) -> str:
        return f"[MOCK benchmark search result for '{query}': Median SaaS CAC payback is 14 months; Series A median ARR is $1.8M.]"
    return _tool


def get_tools_for_persona(persona: Persona, connected_providers: list[str]) -> list[Callable]:
    """Return tool instances bound to the specific persona given connected accounts."""
    tools: list[Callable] = []

    if persona == "vc":
        if "github" in connected_providers:
            tools.append(_mock_mcp_tool("github_activity", "Analyze repository commit frequency, PR velocity, and contributors"))

    elif persona == "analyst":
        if "stripe" in connected_providers:
            tools.append(_mock_mcp_tool("stripe_revenue", "Query live Stripe metrics: MRR, net revenue, and subscriber churn"))
        if "sheets" in connected_providers:
            tools.append(_mock_mcp_tool("sheets_model", "Inspect the founder's Google Sheet financial model and formulas"))
        tools.append(_rag_retrieve_tool())

    elif persona == "realist":
        if "notion" in connected_providers:
            tools.append(_mock_mcp_tool("notion_research", "Search founder's internal Notion workspace for market research notes"))
        
        # Check if Tavily is available
        if os.environ.get("TAVILY_API_KEY"):
            try:
                from langchain_tavily import TavilySearch
                tools.append(TavilySearch(max_results=3))
            except ImportError:
                pass

    return tools
