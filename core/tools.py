"""Tool definitions for the Devil's Advocate Panel.

Real connector tools are wired here — each tool is instantiated with the
user's actual OAuth access token fetched from the database.  If a provider
is not connected, no tool is attached for that persona: the LLM reasons
from pitch text alone rather than receiving fabricated mock data.
"""

from __future__ import annotations

from typing import Callable
from langchain_core.tools import tool
from .state import Persona
from core.config import get_secret


def _rag_retrieve_tool() -> Callable:
    """Live benchmark retriever backed by Supabase pgvector (with in-process fallback)."""
    from db.rag import retrieve_benchmarks

    @tool("benchmark_corpus_search", description="Search startup benchmark, unit economics, and post-mortem corpus")
    def _tool(query: str) -> str:
        results = retrieve_benchmarks(query, top_k=3)
        if not results:
            return "No benchmark data available."
        lines = []
        for r in results:
            src = r.get("source", "Unknown source")
            content = r.get("content", "")
            lines.append(f"[{src}] {content}")
        return "\n".join(lines)

    return _tool


def get_tools_for_persona(persona: Persona, user_id: str) -> list[Callable]:
    """Return real tool instances bound to the user's connected accounts.

    Parameters
    ----------
    persona:
        Which panel member is being instantiated.
    user_id:
        The authenticated user's ID.  Used to look up their OAuth tokens
        from the database so real API calls can be made.

    Notes
    -----
    * If a provider is not connected, **no tool is attached** — the persona
      reasons from pitch text alone rather than seeing ``[MOCK ...]`` strings.
    * Expired / revoked tokens produce a user-readable error string that the
      LLM can incorporate into its response (e.g. "GitHub connection expired").
    """
    from db.connections import get_user_connections

    # Build a quick lookup: provider_name -> connection record
    connections: dict[str, dict] = {}
    if user_id:
        try:
            connections = {c["provider"]: c for c in get_user_connections(user_id)}
        except Exception as e:
            print(f"Warning: could not fetch user connections for tools: {e}")

    tools: list[Callable] = []

    if persona == "vc":
        if "github" in connections:
            from connectors.github_tools import make_github_tool
            token = connections["github"].get("access_token", "")
            if token:
                tools.append(make_github_tool(token))

    elif persona == "analyst":
        if "stripe" in connections:
            from connectors.stripe_tools import make_stripe_tool
            token = connections["stripe"].get("access_token", "")
            if token:
                tools.append(make_stripe_tool(token))

        if "sheets" in connections:
            from connectors.sheets_tools import make_sheets_tool
            token = connections["sheets"].get("access_token", "")
            if token:
                tools.append(make_sheets_tool(token))

        # RAG benchmark search is always available (falls back gracefully when Supabase absent)
        tools.append(_rag_retrieve_tool())

    elif persona == "realist":
        if "notion" in connections:
            from connectors.notion_tools import make_notion_tool
            token = connections["notion"].get("access_token", "")
            if token:
                tools.append(make_notion_tool(token))

        # Tavily live market search (optional)
        if get_secret("TAVILY_API_KEY"):
            try:
                from langchain_tavily import TavilySearch
                tools.append(TavilySearch(max_results=3))
            except ImportError:
                pass

    return tools
