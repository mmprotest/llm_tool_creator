"""LLM client abstraction used throughout the agent system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Sequence

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

    def chat(
        self,
        messages: Sequence[Message],
        *,
        response_format: Mapping[str, object] | None = None,
    ) -> str:
        """Execute a chat completion request and return the response text."""

        payload = [
            {
                "role": msg.role,
                "content": [{"type": "text", "text": msg.content}],
            }
            for msg in messages
        ]
        request_args: MutableMapping[str, Any] = {
            "model": self._config.model,
            "input": payload,
            "timeout": self._config.request_timeout,
            **self._config.extra,
        }
        if response_format is not None:
            request_args["response_format"] = dict(response_format)
        response = self._client.responses.create(**request_args)
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()
        text_chunks = list(self._extract_text_chunks(response))
        if text_chunks:
            return "".join(text_chunks).strip()
        return ""

    def _extract_text_chunks(self, response: Any) -> Iterable[str]:
        """Yield text segments from a Harmony response object."""

        output = getattr(response, "output", None)
        if not output:
            return
        for item in output:
            contents = getattr(item, "content", None)
            if not contents:
                continue
            for content in contents:
                content_type = getattr(content, "type", None)
                if content_type in {"output_text", "text"}:
                    text = getattr(content, "text", None)
                    if text:
                        yield text

    def simple_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Small helper when only a system and user prompt are required."""

        return self.chat(
            [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ]
        )
