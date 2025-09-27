"""Planning utilities for the agent system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .config import PlanningConfig
from .llm import LLMClient, Message


@dataclass
class Plan:
    """Structured plan returned by :class:`TaskPlanner`."""

    goal: str
    steps: List[str]


class PlanningError(RuntimeError):
    """Raised when the planner is unable to produce a plan."""


class TaskPlanner:
    """Derives a multi-step plan for a given goal using an LLM."""

    _SYSTEM_PROMPT = """You are a meticulous planner helping an autonomous AI agent.
Generate a clear, numbered plan to achieve the given goal.
Keep steps focused on actions the agent can perform via tools or reasoning.
Return between 1 and {max_steps} steps.
"""

    def __init__(self, llm: LLMClient, config: PlanningConfig) -> None:
        self._llm = llm
        self._config = config

    def create_plan(self, goal: str, context: str | None = None) -> Plan:
        """Create a plan for ``goal`` optionally taking extra context."""

        user_prompt = f"Goal: {goal.strip()}\n"
        if context:
            user_prompt += f"Context: {context.strip()}\n"
        user_prompt += (
            "Respond with a numbered list. Each line should describe a single step "
            "starting with the step number followed by a colon."
        )
        response = self._llm.chat(
            [
                Message(
                    role="system",
                    content=self._SYSTEM_PROMPT.format(max_steps=self._config.max_plan_steps),
                ),
                Message(role="user", content=user_prompt),
            ]
        )
        steps = self._parse_plan(response)
        if not steps:
            raise PlanningError("Planner returned an empty plan.")
        return Plan(goal=goal, steps=steps)

    def _parse_plan(self, raw_response: str) -> List[str]:
        lines = [line.strip() for line in raw_response.splitlines() if line.strip()]
        steps: List[str] = []
        for line in lines:
            if ":" in line:
                _, action = line.split(":", 1)
                action = action.strip()
            else:
                action = line
            if action:
                steps.append(action)
            if len(steps) >= self._config.max_plan_steps:
                break
        return steps
