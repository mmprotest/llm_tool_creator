"""LLM client abstraction used throughout the agent system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Sequence

# ``openai`` is an optional dependency at import time because the execution
# environment used for automated validation does not always provide outbound
# network access.  The CLI and Streamlit app should therefore fail gracefully
# with a descriptive error instead of raising ``ModuleNotFoundError`` during
# module import.  We resolve the import lazily and surface a helpful message
# if the SDK is missing.
try:  # pragma: no cover - import guarded for runtime environments
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - triggered when SDK unavailable
    OpenAI = None  # type: ignore[assignment]

from .config import LLMConfig


@dataclass(frozen=True)
class Message:
    """Container representing a chat message."""

    role: str
    content: str


class LLMClient:
    """Thin wrapper around the official OpenAI Python client."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        api_key = config.api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = config.api_base or os.getenv("OPENAI_API_BASE") or os.getenv("LLM_API_BASE")
        client_kwargs: Dict[str, Any] = {}
        if OpenAI is None:
            raise RuntimeError(
                "The 'openai' package is required to run the agent. Install the official "
                "OpenAI Python SDK (pip install openai) and ensure network access is "
                "available before executing the orchestrator."
            )
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = OpenAI(**client_kwargs)

    @property
    def model(self) -> str:
        """Return the model identifier."""

        return self._config.model

    def chat(self, messages: Sequence[Message]) -> str:
        """Execute a chat completion request and return the response text."""

        payload = [{"role": msg.role, "content": msg.content} for msg in messages]
        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=payload,
            timeout=self._config.request_timeout,
            **self._config.extra,
        )
        choice = response.choices[0]
        return (choice.message.content or "").strip()

    def simple_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Small helper when only a system and user prompt are required."""

        return self.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ]
        )
