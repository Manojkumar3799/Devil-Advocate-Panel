"""
LLM fallback chain: xAI Grok (primary) -> Gemini 2.5 Flash -> Groq.

Policy:
  - If a model's API isn't responding (rate limit / quota / timeout),
    retry ONCE on that same model, then fall back to the next model.
  - Once a session has fallen back off Grok, stick with the working
    provider for the rest of the session instead of re-probing Grok.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal
from langchain.chat_models import init_chat_model

Provider = Literal["xai", "google_genai", "groq"]

RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    TimeoutError,
    ConnectionError,
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


def _one_retry(model: Any) -> Any:
    return model.with_retry(
        stop_after_attempt=2,
        retry_if_exception_type=RETRYABLE_EXCEPTIONS,
        wait_exponential_jitter=True,
    )


@dataclass
class PanelLLM:
    """Manages the fallback chain with sticky provider behavior."""

    current_provider: Provider = "xai"

    def __post_init__(self):
        self._chain: dict[str, Any] = {}
        self._order: list[Provider] = ["xai", "google_genai", "groq"]

        # Only initialize models if their API key is present or on-demand
        # We configure them with fallbacks
        self._init_models()

    def _init_models(self):
        # We lazily initialize or initialize with sensible defaults
        models = {}
        try:
            models["xai"] = _one_retry(
                init_chat_model("grok-4", model_provider="xai", temperature=0.7)
            )
        except Exception:
            pass

        try:
            models["google_genai"] = _one_retry(
                init_chat_model("gemini-2.5-flash", model_provider="google_genai", temperature=0.7)
            )
        except Exception:
            pass

        try:
            models["groq"] = _one_retry(
                init_chat_model("llama-3.3-70b-versatile", model_provider="groq", temperature=0.7)
            )
        except Exception:
            pass

        self._chain = models
        # Determine initial starting provider based on available keys
        if "xai" not in self._chain and "google_genai" in self._chain:
            self.current_provider = "google_genai"
        elif "xai" not in self._chain and "groq" in self._chain:
            self.current_provider = "groq"

    def _get_active_chain(self, tools: list[Any] | None = None) -> Any:
        available_providers = [p for p in self._order if p in self._chain]
        if not available_providers:
            raise RuntimeError("No LLM providers configured. Please set at least one API key in .env (XAI_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY).")

        start_idx = 0
        if self.current_provider in available_providers:
            start_idx = available_providers.index(self.current_provider)
        
        chain_providers = available_providers[start_idx:]
        models = [self._chain[p] for p in chain_providers]
        
        primary = models[0]
        fallbacks = models[1:]

        if tools:
            primary = primary.bind_tools(tools)
            fallbacks = [fb.bind_tools(tools) for fb in fallbacks]

        if fallbacks:
            return primary.with_fallbacks(fallbacks, exceptions_to_handle=RETRYABLE_EXCEPTIONS)
        return primary

    def invoke(self, messages: list[Any], tools: list[Any] | None = None) -> tuple[Any, str]:
        """Invoke starting from current_provider.
        
        Returns (response, provider_used).
        """
        chain = self._get_active_chain(tools=tools)
        response = chain.invoke(messages)

        # Detect provider used
        used = getattr(response, "response_metadata", {}).get("model_provider") or self.current_provider
        if used in ("xai", "google_genai", "groq") and used != self.current_provider:
            self.current_provider = used

        return response, str(self.current_provider)
