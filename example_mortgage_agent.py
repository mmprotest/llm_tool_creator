"""Example usage of the adaptive agent for a financial query."""

from __future__ import annotations

from src import AgentOrchestrator


if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    goal = (
        "I have a mortgage of $735,000 with 27 years remaining at 6.14% annual interest. "
        "Repayments are fortnightly. Determine the minimum repayment."
    )
    result = orchestrator.run(goal)
    print("Final answer:", result.last_output())
