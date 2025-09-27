"""LLM client abstraction used throughout the agent system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Sequence

from openai import OpenAI

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
