"""
LLM fallback chain: Gemini (primary) -> xAI Grok -> Groq.

Policy:
  - If a model's API isn't responding (rate limit / quota / timeout),
    retry ONCE on that same model, then fall back to the next model.
  - Once a session has fallen back to a different provider, stick with
    the working one for the rest of the session.
  - The provider order is configurable via LLM_PROVIDER_ORDER env var
    (comma-separated, e.g. "xai,google_genai,groq") so switching back
    to Grok-primary is a one-line change once credits are restored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal
from langchain.chat_models import init_chat_model

# Configurable provider order — override with LLM_PROVIDER_ORDER=xai,google_genai,groq
# to restore Grok as primary once credits are available.
DEFAULT_ORDER = ["google_genai", "xai", "groq"]
_order_override = os.environ.get("LLM_PROVIDER_ORDER")  # e.g. "xai,google_genai,groq"
PROVIDER_ORDER: list[str] = _order_override.split(",") if _order_override else DEFAULT_ORDER

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

    current_provider: Provider = PROVIDER_ORDER[0]  # type: ignore[assignment]

    def __post_init__(self):
        self._chain: dict[str, Any] = {}
        self._order: list[str] = list(PROVIDER_ORDER)

        # Only initialize models if their API key is present or on-demand
        # We configure them with fallbacks
        self._init_models()

    def _init_models(self):
        # Store underlying chat models directly so tools can be bound via bind_tools
        models = {}
        try:
            models["xai"] = init_chat_model("grok-4", model_provider="xai", temperature=0.7)
        except Exception:
            pass

        try:
            models["google_genai"] = init_chat_model("gemini-2.5-flash", model_provider="google_genai", temperature=0.7)
        except Exception:
            pass

        try:
            models["groq"] = init_chat_model("llama-3.3-70b-versatile", model_provider="groq", temperature=0.7)
        except Exception:
            pass

        self._chain = models
        # Snap current_provider to the first available in PROVIDER_ORDER
        for p in self._order:
            if p in self._chain:
                self.current_provider = p  # type: ignore[assignment]
                break

    def _get_active_chain(self, tools: list[Any] | None = None) -> Any:
        available_providers = [p for p in self._order if p in self._chain]
        if not available_providers:
            raise RuntimeError("No LLM providers configured. Please set at least one API key in .env (XAI_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY).")

        start_idx = 0
        if self.current_provider in available_providers:
            start_idx = available_providers.index(self.current_provider)
        
        chain_providers = available_providers[start_idx:]
        models = [self._chain[p] for p in chain_providers]

        if tools:
            models = [m.bind_tools(tools) if hasattr(m, "bind_tools") else m for m in models]

        # Wrap each model with retry
        models = [_one_retry(m) for m in models]

        primary = models[0]
        fallbacks = models[1:]

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
