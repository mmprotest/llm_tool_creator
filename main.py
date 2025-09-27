"""Command line interface for running the adaptive agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src import AgentConfig, AgentOrchestrator


def _load_context(context_file: str | None) -> str | None:
    if not context_file:
        return None
    path = Path(context_file)
    if not path.exists():
        raise FileNotFoundError(f"Context file not found: {context_file}")
    return path.read_text(encoding="utf-8")


def _print_result(result: Any) -> None:
    if isinstance(result, (dict, list)):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the adaptive AI agent on a goal.")
    parser.add_argument("goal", help="High level goal for the agent.")
    parser.add_argument("--context", help="Optional path to a text file containing additional context.")
    args = parser.parse_args()

    config = AgentConfig()
    try:
        orchestrator = AgentOrchestrator(config)
    except RuntimeError as exc:
        parser.error(str(exc))
    context = _load_context(args.context)
    result = orchestrator.run(args.goal, context=context)

    print("=== PLAN ===")
    for idx, step in enumerate(result.plan.steps, start=1):
        print(f"{idx}. {step}")

    print("\n=== EXECUTION LOG ===")
    for idx, log in enumerate(result.steps, start=1):
        print(f"Step {idx}: {log.step_description}")
        print(f"  Thought: {log.decision.thought}")
        print(f"  Action: {log.decision.action}")
        if log.decision.tool_name:
            print(f"  Tool: {log.decision.tool_name}")
            if log.decision.arguments:
                print(f"  Arguments: {json.dumps(log.decision.arguments, ensure_ascii=False)}")
        if log.created_tool:
            print(f"  Created tool: {log.created_tool.name} -> {log.created_tool.description}")
        if log.output is not None:
            print("  Output:")
            _print_result(log.output)
        if log.error:
            print(f"  Error: {log.error}")
        print()

    final_answer = result.last_output()
    if final_answer:
        print("=== FINAL ANSWER ===")
        _print_result(final_answer)


if __name__ == "__main__":
    main()
