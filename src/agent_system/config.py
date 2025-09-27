"""Configuration objects and constants for the agent system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LLMConfig:
    """Configuration required to instantiate an LLM client."""

    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    request_timeout: int = 300
    extra: Dict[str, object] = field(default_factory=dict)


@dataclass
class PlanningConfig:
    """Configuration for planning behaviour."""

    max_plan_steps: int = 8
    require_reasoning: bool = True


@dataclass
class ToolingConfig:

    """Configuration for dynamic tool management.

    Attributes
    ----------
    generated_module_path:
        Location on disk where dynamically generated helpers are persisted.
    auto_persist:
        When ``True`` newly created tools are appended to ``generated_module_path`` and reloaded on
        subsequent runs.
    """
=======
    """Configuration for dynamic tool management."""


    generated_module_path: str = "src/agent_system/generated_tools.py"
    auto_persist: bool = True


@dataclass
class AgentConfig:
    """Aggregate configuration for the full agent orchestration pipeline."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)
    tooling: ToolingConfig = field(default_factory=ToolingConfig)
    verbose: bool = True
