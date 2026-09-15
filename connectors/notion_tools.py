"""Notion tool connector using OAuth access tokens."""

from __future__ import annotations

import httpx
from langchain_core.tools import tool


def make_notion_tool(access_token: str):
    @tool("notion_research", description="Search internal Notion pages for founder market research and roadmap notes")
    def notion_research(query: str) -> str:
        """Search Notion database/pages for matching query."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                payload = {"query": query, "page_size": 5}
                res = client.post("https://api.notion.com/v1/search", json=payload, headers=headers)
                if res.status_code == 401:
                    return "Notion connection expired or token revoked — no workspace data available."
                if res.status_code != 200:
                    return f"Notion API error ({res.status_code}): {res.text}"
                results = res.json().get("results", [])
                snippets = []
                for item in results:
                    title_obj = item.get("properties", {}).get("title", {}).get("title", [])
                    title = title_obj[0].get("plain_text", "Untitled") if title_obj else "Page"
                    snippets.append(f"- {title} (ID: {item.get('id')})")
                return f"Notion Search Results for '{query}':\n" + ("\n".join(snippets) if snippets else "No pages found.")
        except Exception as e:
            return f"Error searching Notion: {e}"

    return notion_research
