# LLM Tool Creator

Modular agent system that plans, decides, and dynamically generates Python helper tools to solve complex goals. The agent integrates planning, reasoning, and execution while offering both interactive and programmatic interfaces.

## Key capabilities

- **OpenAI-native** – Uses the official [`openai`](https://pypi.org/project/openai/) SDK and works with any OpenAI-compatible endpoint (Azure OpenAI, local proxies, etc.).
- **Reasoned planning** – Builds concise, auditable plans before acting so the agent stays on track.
- **Transparent decisions** – The action policy chooses between thinking, using a tool, or creating a new one while exposing its internal reasoning.
- **Dynamic tool creation** – Natural-language specifications are converted into Python helpers that can be persisted and reused across runs.
- **Built-in web tooling** – DuckDuckGo search and HTTP fetching utilities support lightweight research.
- **Flexible workflows** – Control the agent via the Streamlit dashboard, CLI, or direct Python API.

## Project structure

```
src/
  agent_system/
    config.py          # Dataclasses describing the agent configuration model.
    llm.py             # Thin wrapper around the OpenAI Python client.
    planner.py         # Converts goals into step-by-step plans.
    decider.py         # Chooses whether to think, execute, or create tools with explicit reasoning.
    tooling.py         # Registers built-in tools and manages dynamically generated ones.
    tools/             # Default tools (web search, URL fetcher, Python executor).
    orchestrator.py    # High-level loop coordinating the planner, decider, and tool manager.
    generated_tools.py # Auto-populated with LLM-generated helpers (loaded on start-up).
main.py                # CLI entry point.
streamlit_app.py       # Streamlit UI for interactive experimentation.
```

## Installation

1. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure LLM credentials** – set `OPENAI_API_KEY` and optionally `OPENAI_API_BASE` (or the fallback `LLM_API_KEY` / `LLM_API_BASE` variables):

   ```bash
   export OPENAI_API_KEY="your-key"
   export OPENAI_API_BASE="https://api.openai.com/v1"  # optional override
   ```

## Usage

### Streamlit control panel

Launch the interactive UI to configure models, run goals, and inspect step-by-step execution:

```bash
streamlit run streamlit_app.py
```

The sidebar exposes credentials, planning depth, persistence controls, and advanced OpenAI parameters. The main pane visualises the generated plan, each reasoning step, any dynamically created tools (with source code), and the final answer.

### Command line interface

Run the agent from the terminal with a goal statement:

```bash
python main.py "Plan a weekend trip to Tokyo including a day trip and budget"
```

Optional context can be supplied via a text file:

```bash
python main.py "Draft a marketing plan" --context notes/brand_constraints.txt
```

### Programmatic access

```python
from src import AgentOrchestrator

goal = "Summarise the latest research on quantum batteries"
orchestrator = AgentOrchestrator()
result = orchestrator.run(goal)
print(result.last_output())
```

## Configuration reference

Runtime settings live in `AgentConfig` (`src/agent_system/config.py`). Override defaults programmatically or through the Streamlit sidebar:

- **LLMConfig** – Model name, API key/base URL, timeout, and additional OpenAI parameters.
- **PlanningConfig** – Maximum plan steps and whether the decider must always provide reasoning (`require_reasoning`).
- **ToolingConfig** – Generated tools path and `auto_persist` flag controlling persistence.
- **AgentConfig.max_decision_attempts** – Number of times the orchestrator will retry the
  action-selection step when the model returns an invalid decision.

## Tool persistence & custom tools

- Built-in helpers (`web_search`, `fetch_url`, `run_python`) are registered at startup without being written to disk.
- Dynamically generated tools are appended to `src/agent_system/generated_tools.py` when persistence is enabled and are reloaded automatically on start-up.
- Register custom utilities by calling `orchestrator.tool_manager.register` and pass `persist=True` to store them alongside generated tools.

## Testing

Use Python's bytecode compiler to ensure modules import cleanly:

```bash
python -m compileall src streamlit_app.py main.py example_mortgage_agent.py
```

## Troubleshooting

- **Decision errors** – When `require_reasoning=True`, the decider raises an error if the model omits a `thought`. Inspect the execution log in Streamlit or the CLI output.
- **DuckDuckGo limits** – Install `duckduckgo-search` for richer API-based results; otherwise HTML and instant-answer fallbacks are used.
- **Network/SSL issues** – Verify proxy settings and confirm the configured `OPENAI_API_BASE` endpoint is reachable.
