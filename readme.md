# Adaptive LLM Tool Creator

This repository ships a production-ready framework for building autonomous, tool-augmented
agents. The agent can decompose arbitrary goals into actionable plans, decide which tools to
execute, generate new Python tools on demand, and browse the web to gather supporting
information.

## Key capabilities

- **OpenAI native** – Built on top of the official [`openai`](https://pypi.org/project/openai/) SDK
  and compatible with any OpenAI-style endpoint (Azure OpenAI, local proxies, etc.).
- **Reasoned planning** – A planner derives a concise sequence of steps before execution to keep
  the agent focused and auditable.
- **Action policy** – The decision module weighs existing tools against the need to think or create
  a new tool, and is configured to always expose its reasoning.
- **Dynamic tool creation** – Natural-language specifications are translated into executable Python
  helpers which can be cached and re-used across runs.
- **Web research tooling** – DuckDuckGo search and HTTP fetching provide light-weight browsing
  primitives out of the box.
- **Interactive & scripted workflows** – Use the Streamlit control panel for rapid experimentation
  or the CLI/programmatic API for automation.

## Project structure

```
src/
  agent_system/
    config.py        # Dataclasses describing the agent configuration model.
    llm.py           # Thin wrapper around the OpenAI Python client.
    planner.py       # Converts goals into step-by-step plans.
    decider.py       # Chooses whether to think, execute, or create tools with explicit reasoning.
    tooling.py       # Registers built-in tools and manages dynamically generated ones.
    tools/           # Default tools (web search, URL fetcher, Python executor).
    orchestrator.py  # High-level loop coordinating the planner, decider, and tool manager.
    generated_tools.py # Auto-populated with LLM-generated helpers (loaded on start-up).
main.py              # CLI entry point.
streamlit_app.py     # Streamlit UI for interactive experimentation.
```

## Installation

1. **Create a virtual environment** (optional but recommended).

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**.

   ```bash
   pip install -r requirements.txt
   ```

3. **Provide LLM credentials**. The agent reads `OPENAI_API_KEY` and `OPENAI_API_BASE` (or the
   `LLM_API_KEY` / `LLM_API_BASE` fallbacks). For example:

   ```bash
   export OPENAI_API_KEY="your-key"
   export OPENAI_API_BASE="https://api.openai.com/v1"  # optional override
   ```

## Usage

### Streamlit control panel

Launch the interactive UI to configure models, run goals, and inspect step-by-step execution.

```bash
streamlit run streamlit_app.py
```

The sidebar exposes model credentials, planning depth, persistence controls, and advanced OpenAI
parameters. The main area visualises the generated plan, each reasoning step, any dynamically
created tools (including their source code), and the final answer.

### Command line interface

Execute the agent from the terminal:

```bash
python main.py "Plan a weekend trip to Tokyo including a day trip and budget"
```

Optional additional context can be supplied via a text file:

```bash
python main.py "Draft a marketing plan" --context notes/brand_constraints.txt
```

The CLI prints the plan, execution log, tool creations, and any final output.

### Programmatic access

```python
from src import AgentOrchestrator

orchestrator = AgentOrchestrator()
result = orchestrator.run("Summarise the latest research on quantum batteries")
print(result.last_output())
```

## Configuration reference

All runtime settings are encapsulated by `AgentConfig` (`src/agent_system/config.py`). Override the
defaults either programmatically or within the Streamlit sidebar:

- **LLMConfig** – Model name, API key/base URL, timeout, and extra parameters forwarded to
  `openai.ChatCompletion`. Use this to adjust temperature, response format, etc.
- **PlanningConfig** – Maximum number of plan steps and whether the decider must always supply
  reasoning (`require_reasoning=True` raises an error if the thought field is blank).
- **ToolingConfig** – Path to the generated tools module and an `auto_persist` flag controlling
  whether new tools are appended for later reuse.

## Tool persistence & custom tools

- Built-in helpers (`web_search`, `fetch_url`, `run_python`) are registered at startup without being
  written to disk.
- Dynamically generated tools are appended to `src/agent_system/generated_tools.py` when persistence
  is enabled. The file is parsed on initialisation so previously created helpers become immediately
  available in subsequent runs.
- You can register your own utilities by calling `orchestrator.tool_manager.register` with
  `persist=True` if you want them stored alongside generated tools.

## Testing & quality checks

The project is validated using Python's bytecode compiler to ensure all modules import cleanly:

```bash
python -m compileall src streamlit_app.py main.py example_mortgage_agent.py
```

You can also run the agent in a dry run (with mock LLM responses) or add your own tests depending on
your deployment requirements.

## Troubleshooting

- **Empty or failing decisions** – Enable persistence and inspect the execution log to confirm the
  LLM returned a valid JSON payload. The decider enforces non-empty reasoning when
  `require_reasoning=True`.
- **DuckDuckGo limits** – Install `duckduckgo-search` for API-based queries; otherwise the HTML and
  instant-answer fallbacks will be used automatically.
- **OpenAI SDK missing** – Install the [`openai`](https://pypi.org/project/openai/) package and
  provide valid credentials before running the CLI or Streamlit app. The orchestrator surfaces a
  descriptive error if the dependency is unavailable.
- **Network or SSL errors** – Verify proxy/firewall rules and confirm the `OPENAI_API_BASE`
  endpoint is reachable from your environment.
