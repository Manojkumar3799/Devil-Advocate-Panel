"""Reasoning extraction and normalization utilities across LLM providers."""

from __future__ import annotations

import re
from typing import Any


def extract_reasoning(response: Any, provider: str) -> tuple[str, str]:
    """Extract (thinking_text, answer_text) normalized across providers.
    
    If no thinking trace is available, returns ("", answer_text).
    """
    content = getattr(response, "content", "")
    if isinstance(content, list):
        # Handle cases where content is a list of blocks/parts
        text_parts = []
        thought_parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "thinking" or part.get("thought"):
                    thought_parts.append(part.get("thinking") or part.get("text", ""))
                elif "text" in part:
                    text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        content_str = "\n".join(text_parts)
        if thought_parts:
            return "\n".join(thought_parts).strip(), content_str.strip()
    else:
        content_str = str(content)

    kwargs = getattr(response, "additional_kwargs", {}) or {}

    # xAI Grok (reasoning_content)
    if provider in ("xai", "grok"):
        thinking = kwargs.get("reasoning_content") or ""
        if thinking:
            return str(thinking).strip(), content_str.strip()

    # Google GenAI (thought parts or metadata)
    if provider in ("google_genai", "gemini"):
        parts = kwargs.get("parts", []) or []
        thoughts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("thought")]
        if thoughts:
            return "\n".join(thoughts).strip(), content_str.strip()

    # Groq or DeepSeek / Qwen models that use <think> tags
    if "<think>" in content_str and "</think>" in content_str:
        match = re.search(r"<think>(.*?)</think>", content_str, re.DOTALL)
        if match:
            thinking = match.group(1).strip()
            answer = re.sub(r"<think>.*?</think>", "", content_str, flags=re.DOTALL).strip()
            return thinking, answer

    return "", content_str.strip()
