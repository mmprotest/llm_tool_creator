"""Action decision utilities for the agent system."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .llm import LLMClient, Message
from .tooling import ToolSpec


@dataclass
class ToolProposal:
    """Request describing a tool that should be created."""

    name: str
    purpose: str
    specification: str


@dataclass
class ActionDecision:
    """Decision returned by :class:`ActionDecider`."""

    thought: str
    action: str
    tool_name: Optional[str]
    arguments: Dict[str, object]
    new_tool: Optional[ToolProposal]


class DecisionError(RuntimeError):
    """Raised when the action decider cannot produce a valid decision."""


class ActionDecider:
    """LLM backed policy that decides which tool or strategy to apply."""

    _SYSTEM_PROMPT = """You coordinate an autonomous multi-tool agent.
You must always respond with a valid JSON object.
JSON schema:
{
  "thought": str,
  "action": "use_tool" | "think" | "create_tool",
  "tool_name": str | null,
  "arguments": dict,
  "new_tool": {
      "name": str,
      "purpose": str,
      "specification": str
  } | null
}
The agent can only execute actions through registered tools.
"""

    _RESPONSE_FORMAT = {
        "type": "json_schema",
        "json_schema": {
            "name": "action_decision",
            "schema": {
                "type": "object",
                "properties": {
                    "thought": {"type": "string"},
                    "action": {
                        "type": "string",
                        "enum": ["use_tool", "think", "create_tool"],
                    },
                    "tool_name": {"type": ["string", "null"]},
                    "arguments": {"type": "object"},
                    "new_tool": {
                        "anyOf": [
                            {"type": "null"},
                            {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "purpose": {"type": "string"},
                                    "specification": {"type": "string"},
                                },
                                "required": ["name", "purpose", "specification"],
                                "additionalProperties": False,
                            },
                        ]
                    },
                },
                "required": ["thought", "action", "arguments"],
                "additionalProperties": False,
            },
        },
    }


    def __init__(self, llm: LLMClient, *, require_reasoning: bool = True) -> None:
        """Create a decider.

        Parameters
        ----------
        llm:
            Client used to query the underlying language model.
        require_reasoning:
            When ``True`` the returned decision must include a non-empty ``thought`` field; an empty
            field results in :class:`DecisionError` so the orchestrator can request a retry.
        """

        self._llm = llm
        self._require_reasoning = require_reasoning


    def decide(self, step: str, tools: List[ToolSpec], context: str | None = None) -> ActionDecision:
        """Return the best action for ``step`` based on available tools."""

        tool_descriptions = [
            {
                "name": tool.name,
                "signature": tool.signature,
                "description": tool.description,
            }
            for tool in tools
        ]
        user_prompt = {
            "step": step,
            "available_tools": tool_descriptions,
            "context": context or "",
            "instructions": (
                "Select the best action. Use action 'think' if no tool execution is required "
                "and provide reasoning in the thought field."
            ),
        }

        if self._require_reasoning:
            user_prompt["instructions"] += (
                " Always explain why you selected the action in the 'thought' field before acting."
            )

        response = self._llm.chat(
            [
                Message(role="system", content=self._SYSTEM_PROMPT),
                Message(role="user", content=json.dumps(user_prompt, ensure_ascii=False)),
            ],
            response_format=self._RESPONSE_FORMAT,
        )
        try:
            payload = json.loads(response)
        except json.JSONDecodeError as exc:
            raise DecisionError(f"Invalid JSON from decider: {response}") from exc
        try:
            action = payload["action"]
            thought = payload.get("thought", "")
            tool_name = payload.get("tool_name")
            arguments = payload.get("arguments") or {}
            new_tool_payload = payload.get("new_tool")
        except Exception as exc:
            raise DecisionError(f"Missing keys in decision payload: {payload}") from exc
        new_tool = None
        if new_tool_payload:
            try:
                new_tool = ToolProposal(
                    name=new_tool_payload["name"],
                    purpose=new_tool_payload["purpose"],
                    specification=new_tool_payload["specification"],
                )
            except KeyError as exc:
                raise DecisionError(
                    f"Incomplete new tool description: {new_tool_payload}"
                ) from exc
        if action not in {"use_tool", "think", "create_tool"}:
            raise DecisionError(f"Unsupported action '{action}'.")
        if action == "use_tool" and not tool_name:
            raise DecisionError("Tool action chosen without specifying tool name.")
        if action == "create_tool" and not new_tool:
            raise DecisionError("Tool creation requested without tool proposal.")

        if self._require_reasoning and not thought:
            raise DecisionError("Reasoning is required but the thought field was empty.")

        return ActionDecision(
            thought=thought,
            action=action,
            tool_name=tool_name,
            arguments=arguments,
            new_tool=new_tool,
        )
