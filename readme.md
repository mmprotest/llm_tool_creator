# Adaptive LLM Tool Creator

This project contains a modular agent system capable of planning, creating Python tools,
and executing them to solve complex problems. The agent combines a planner, decision
policy, dynamic tool manager, and built-in web browsing utilities.

## Features

- **Planning** – Generates multi-step plans for arbitrary goals using an OpenAI-compatible LLM.
- **Action selection** – Chooses between thinking, executing a tool, or creating a new tool.
- **Dynamic tool creation** – Automatically generates Python helper functions based on natural
  language specifications and loads them at runtime.
- **Web interaction** – Ships with DuckDuckGo search and URL fetching utilities to enable
  online research.
- **Python execution** – Includes a sandboxed Python executor for quick calculations or data
  wrangling.

## Requirements

- Python 3.10+
- [`openai`](https://pypi.org/project/openai/) Python SDK configured with API access.
- Optional: [`duckduckgo-search`](https://pypi.org/project/duckduckgo-search/) for richer search results.

Set the following environment variables or adjust `AgentConfig.llm` to point at your preferred
OpenAI-compatible endpoint:

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

## Usage

Run the CLI with a goal statement:

```bash
python main.py "Plan a weekend trip to Tokyo including a day trip and budget"
```

To provide additional context, create a text file and pass the path via `--context`.

The CLI prints the generated plan, execution log, and final answer (if produced).

## Programmatic Example

```python
from src import AgentOrchestrator

orchestrator = AgentOrchestrator()
goal = "Summarise the latest research on quantum batteries"
result = orchestrator.run(goal)
print(result.last_output())
```

## Extending the Agent

- Register custom Python functions via `orchestrator.tool_manager.register`.
- Persist generated tools inside `src/agent_system/generated_tools.py` (auto-managed).
- Modify prompts or behaviour by editing modules within `src/agent_system/`.
