"""
LLM fallback chain: xAI Grok (primary) -> Gemini 2.5 Flash -> Groq.

Policy (per user decision):
  - If a model's API isn't responding (rate limit / quota / timeout),
    retry ONCE on that same model, then fall back to the next model.
  - Once a session has fallen back off Grok, stick with the working
    provider for the rest of the session instead of re-probing Grok
    on every turn (avoids wasting a call+retry on an exhausted daily quota).

Also normalizes "thinking" extraction across providers, since each one
exposes reasoning differently:
  - xAI Grok: separate `reasoning_content` in additional_kwargs
  - Gemini 2.5 Flash (thinking mode): thought-marked parts
  - Groq reasoning models: often inline <think>...</think> in content,
    sometimes no real trace at all -- degrade gracefully, don't fake it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from langchain.chat_models import init_chat_model

Provider = Literal["xai", "google_genai", "groq"]

# Exceptions worth retrying / falling back on. Kept narrow on purpose --
# a bad prompt or an auth error should NOT be silently masked by
# switching providers three times.
RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    # Most provider SDKs raise a RateLimitError / APIStatusError subclassing
    # these OpenAI-compatible base classes when hit through LangChain's
    # unified client. Import lazily so this module doesn't hard-require
    # every SDK to be installed.
)

try:
    from openai import RateLimitError as _OpenAIRateLimitError
    from openai import APITimeoutError as _OpenAIAPITimeoutError
    from openai import APIConnectionError as _OpenAIAPIConnectionError

    RETRYABLE_EXCEPTIONS = RETRYABLE_EXCEPTIONS + (
        _OpenAIRateLimitError,
        _OpenAIAPITimeoutError,
        _OpenAIAPIConnectionError,
    )
except ImportError:
    pass


def _one_retry(model):
    """Wrap a model so ONE retry happens on the same model before giving up
    (giving up here just means: with_fallbacks moves to the next model)."""
    return model.with_retry(
        stop_after_attempt=2,  # 1 original call + 1 retry
        retry_if_exception_type=RETRYABLE_EXCEPTIONS,
        wait_exponential_jitter=True,
    )


@dataclass
class PanelLLM:
    """Holds the fallback chain and tracks which provider is currently answering,
    so a session can 'stick' with a working fallback instead of re-probing Grok
    every turn."""

    current_provider: Provider = "xai"

    def __post_init__(self):
        self._chain = {
            "xai": _one_retry(
                init_chat_model("grok-4", model_provider="xai", temperature=0.8)
            ),
            "google_genai": _one_retry(
                init_chat_model(
                    "gemini-2.5-flash",
                    model_provider="google_genai",
                    temperature=0.8,
                )
            ),
            "groq": _one_retry(
                init_chat_model(
                    "llama-3.3-70b-versatile",
                    model_provider="groq",
                    temperature=0.8,
                )
            ),
        }
        self._order: list[Provider] = ["xai", "google_genai", "groq"]

    def _remaining_chain_from(self, provider: Provider):
        start = self._order.index(provider)
        models = [self._chain[p] for p in self._order[start:]]
        primary, *fallbacks = models
        if fallbacks:
            return primary.with_fallbacks(
                fallbacks, exceptions_to_handle=RETRYABLE_EXCEPTIONS
            )
        return primary

    def invoke(self, messages, tools=None):
        """Invoke starting from current_provider (sticky after first fallback).
        Returns (response, provider_used)."""
        model = self._remaining_chain_from(self.current_provider)
        if tools:
            model = model.bind_tools(tools)

        response = model.invoke(messages)

        used = getattr(response, "response_metadata", {}).get("model_provider")
        if used and used != self.current_provider:
            self.current_provider = used  # stick with whatever actually answered

        return response, self.current_provider

    def stream(self, messages, tools=None):
        """Streaming variant. NOTE: fallback only reliably triggers on
        pre-stream errors (auth/429/timeout before the first token) -- a
        failure mid-stream is surfaced to the caller as an exception rather
        than silently restarted on a fallback model, per the agreed default
        (simpler than a full restart-on-fallback UX)."""
        model = self._remaining_chain_from(self.current_provider)
        if tools:
            model = model.bind_tools(tools)
        yield from model.stream(messages)


def extract_reasoning(response, provider: Provider) -> tuple[str, str]:
    """Return (thinking_text, answer_text), normalized across providers.
    Returns "" for thinking_text if no genuine trace is available -- the UI
    should show 'reasoning unavailable' rather than faking one."""
    kwargs = getattr(response, "additional_kwargs", {}) or {}

    if provider == "xai":
        return kwargs.get("reasoning_content", ""), response.content

    if provider == "google_genai":
        parts = kwargs.get("parts", []) or []
        thoughts = [p.get("text", "") for p in parts if p.get("thought")]
        return "\n".join(t for t in thoughts if t), response.content

    if provider == "groq":
        content = response.content or ""
        if "<think>" in content and "</think>" in content:
            thinking, _, answer = content.partition("</think>")
            thinking = thinking.replace("<think>", "").strip()
            return thinking, answer.strip()
        return "", content  # no genuine trace from this model -- degrade gracefully

    return "", response.content
