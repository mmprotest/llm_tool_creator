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
- [`streamlit`](https://streamlit.io/) for the interactive control panel.
- Optional: [`duckduckgo-search`](https://pypi.org/project/duckduckgo-search/) for richer search results.

Install the dependencies and export your API credentials (or adjust `AgentConfig.llm` to match
your OpenAI-compatible endpoint):

```bash
pip install openai streamlit duckduckgo-search
export OPENAI_API_KEY="your-key"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

## Usage

### Streamlit control panel

Launch the interactive UI to configure the agent, run goals, and inspect execution logs:

```bash
streamlit run streamlit_app.py
```

Use the sidebar to choose the model, provide API keys, adjust planning parameters, and toggle
automatic tool persistence. The main panel shows the generated plan, execution steps, tools
created on-the-fly, and the final output.

### Command line interface

Run the CLI with a goal statement:

```bash
python main.py "Plan a weekend trip to Tokyo including a day trip and budget"
```

To provide additional context, create a text file and pass the path via `--context`. The CLI
prints the generated plan, execution log, and final answer (if produced).

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
