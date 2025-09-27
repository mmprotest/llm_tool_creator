"""High level orchestration logic for the adaptive agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from .config import AgentConfig
from .decider import ActionDecider, ActionDecision, DecisionError
from .llm import LLMClient
from .planner import Plan, TaskPlanner
from .tooling import ToolManager, ToolSpec
from .tools import register_default_tools


@dataclass
class StepLog:
    """Represents the outcome of a single reasoning step."""

    step_description: str
    decision: ActionDecision
    output: Any = None
    created_tool: Optional[ToolSpec] = None
    error: Optional[str] = None


@dataclass
class AgentRunResult:
    """Aggregate result for an agent run."""

    plan: Plan
    steps: List[StepLog] = field(default_factory=list)

    def last_output(self) -> Any:
        """Return the output of the final step if available."""

        for step in reversed(self.steps):
            if step.output is not None:
                return step.output
        return None


class AgentOrchestrator:
    """Coordinates planning, tool creation, and execution."""

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self._config = config or AgentConfig()
        self._llm = LLMClient(self._config.llm)
        self._planner = TaskPlanner(self._llm, self._config.planning)
        self._tool_manager = ToolManager(self._config.tooling)
        register_default_tools(self._tool_manager)
        self._decider = ActionDecider(
            self._llm, require_reasoning=self._config.planning.require_reasoning
        )

    @property
    def tool_manager(self) -> ToolManager:
        """Expose the underlying tool manager."""

        return self._tool_manager

    def run(self, goal: str, context: str | None = None) -> AgentRunResult:
        """Execute the full planning and action loop for ``goal``."""

        plan = self._planner.create_plan(goal, context=context)
        result = AgentRunResult(plan=plan)
        for step in plan.steps:
            tools = self._tool_manager.available_tools()
            try:
                decision = self._decider.decide(step, tools, context=context)
            except DecisionError as exc:
                result.steps.append(
                    StepLog(
                        step_description=step,
                        decision=ActionDecision("", "think", None, {}, None),
                        error=str(exc),
                    )
                )
                continue
            log_entry = StepLog(step_description=step, decision=decision)
            try:
                if decision.action == "use_tool" and decision.tool_name:
                    log_entry.output = self._tool_manager.execute(
                        decision.tool_name, **decision.arguments
                    )
                elif decision.action == "create_tool" and decision.new_tool:
                    created = self._tool_manager.create_tool(
                        self._llm,
                        decision.new_tool.specification,
                        expected_name=decision.new_tool.name,
                    )
                    log_entry.created_tool = created
                    if decision.arguments:
                        log_entry.output = self._tool_manager.execute(
                            created.name, **decision.arguments
                        )
                # action "think" simply records the thought
            except Exception as exc:  # pragma: no cover - runtime safety
                log_entry.error = str(exc)
            result.steps.append(log_entry)
        return result
