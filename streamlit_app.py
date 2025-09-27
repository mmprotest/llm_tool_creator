"""Streamlit UI for interacting with the adaptive agent system."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, Optional

import streamlit as st

from src.agent_system.config import AgentConfig, LLMConfig, PlanningConfig, ToolingConfig
from src.agent_system.orchestrator import AgentOrchestrator, AgentRunResult, StepLog


st.set_page_config(page_title="Adaptive Agent Control Panel", layout="wide")


def _serialise_step(log: StepLog) -> Dict[str, Any]:
    """Convert a :class:`StepLog` into a Streamlit friendly dictionary."""

    created_tool = None
    if log.created_tool is not None:
        created_tool = {
            "name": log.created_tool.name,
            "description": log.created_tool.description,
            "signature": log.created_tool.signature,
            "code": log.created_tool.code,
        }
    return {
        "step_description": log.step_description,
        "decision": {
            "thought": log.decision.thought,
            "action": log.decision.action,
            "tool_name": log.decision.tool_name,
            "arguments": log.decision.arguments,
        },
        "output": log.output,
        "created_tool": created_tool,
        "error": log.error,
    }


def _serialise_result(result: AgentRunResult) -> Dict[str, Any]:
    """Convert the agent result into serialisable primitives."""

    return {
        "plan_steps": list(result.plan.steps),
        "steps": [_serialise_step(log) for log in result.steps],
        "final_output": result.last_output(),
    }


def _config_signature(config: AgentConfig) -> str:
    """Return a stable hashable signature for a config dataclass."""

    return json.dumps(asdict(config), sort_keys=True, default=str)


def _build_agent_config(
    *,
    model: str,
    api_key: Optional[str],
    api_base: Optional[str],
    request_timeout: int,
    planning_steps: int,
    require_reasoning: bool,
    auto_persist_tools: bool,
    generated_module_path: str,
    extra_json: str,
) -> AgentConfig:
    """Create an :class:`AgentConfig` using sidebar settings."""

    extra: Dict[str, Any] = {}
    if extra_json.strip():
        try:
            parsed = json.loads(extra_json)
            if not isinstance(parsed, dict):
                raise ValueError("Additional parameters must be a JSON object.")
            extra = parsed
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse additional parameters: {exc.msg}") from exc
    llm_config = LLMConfig(
        model=model.strip() or "gpt-4o-mini",
        api_key=api_key or None,
        api_base=api_base or None,
        request_timeout=request_timeout,
        extra=extra,
    )
    planning_config = PlanningConfig(
        max_plan_steps=planning_steps,
        require_reasoning=require_reasoning,
    )
    tooling_config = ToolingConfig(
        generated_module_path=generated_module_path.strip() or ToolingConfig().generated_module_path,
        auto_persist=auto_persist_tools,
    )
    return AgentConfig(
        llm=llm_config,
        planning=planning_config,
        tooling=tooling_config,
    )


st.title("Adaptive Agent Control Panel")
st.write(
    "Configure the agent, define a goal, and watch the planner create tools and execute "
    "steps to achieve it. Provide an API key compatible with the OpenAI SDK to run live "
    "sessions."
)

with st.sidebar:
    st.header("Model configuration")
    model_name = st.text_input("Model", value="gpt-4o-mini")
    api_key = st.text_input("API key", type="password", help="Stored only in the current session.")
    api_base = st.text_input("API base", placeholder="https://api.openai.com/v1")
    timeout = st.number_input("Request timeout (s)", min_value=30, max_value=600, value=300, step=30)
    st.header("Planning")
    max_steps = st.slider("Maximum plan steps", min_value=1, max_value=12, value=8)
    require_reasoning = st.checkbox("Require reasoning", value=True)
    st.header("Tools")
    auto_persist = st.checkbox("Persist generated tools", value=True)
    generated_path = st.text_input(
        "Generated module path", value=ToolingConfig().generated_module_path
    )
    st.header("Advanced")
    extra_parameters = st.text_area(
        "Additional OpenAI parameters (JSON)",
        placeholder='{"temperature": 0.2}',
        height=100,
    )

st.subheader("Define the task")
goal = st.text_area("Goal", placeholder="Break down and solve a complex objective...", height=120)
context = st.text_area(
    "Optional context", placeholder="Background details, previous outputs, constraints...", height=120
)

run_button = st.button("Run agent", type="primary", use_container_width=True)

if run_button:
    if not goal.strip():
        st.warning("Please enter a goal before running the agent.")
    else:
        try:
            agent_config = _build_agent_config(
                model=model_name,
                api_key=api_key,
                api_base=api_base,
                request_timeout=int(timeout),
                planning_steps=int(max_steps),
                require_reasoning=bool(require_reasoning),
                auto_persist_tools=bool(auto_persist),
                generated_module_path=generated_path,
                extra_json=extra_parameters,
            )
        except ValueError as config_error:
            st.error(str(config_error))
        else:
            signature = _config_signature(agent_config)
            if (
                "_agent_signature" not in st.session_state
                or st.session_state["_agent_signature"] != signature
            ):
                st.session_state["_orchestrator"] = AgentOrchestrator(agent_config)
                st.session_state["_agent_signature"] = signature
            orchestrator: AgentOrchestrator = st.session_state["_orchestrator"]
            with st.spinner("Running agent..."):
                try:
                    result = orchestrator.run(goal.strip(), context=context.strip() or None)
                except Exception as exc:  # pragma: no cover - runtime safety
                    st.session_state["_last_result"] = None
                    st.session_state["_last_error"] = str(exc)
                else:
                    st.session_state["_last_result"] = _serialise_result(result)
                    st.session_state["_last_error"] = None

if st.session_state.get("_last_error"):
    st.error(st.session_state["_last_error"])

result_payload = st.session_state.get("_last_result")
if result_payload:
    st.subheader("Plan overview")
    plan_steps = result_payload["plan_steps"]
    if plan_steps:
        for index, step in enumerate(plan_steps, start=1):
            st.markdown(f"**{index}.** {step}")
    else:
        st.info("No plan steps were generated.")

    st.subheader("Execution log")
    for idx, step in enumerate(result_payload["steps"], start=1):
        header = f"Step {idx}: {step['step_description']}"
        with st.expander(header, expanded=idx == len(result_payload["steps"])):
            decision = step["decision"]
            st.markdown(f"**Thought:** {decision['thought'] or '—'}")
            st.markdown(f"**Action:** `{decision['action']}`")
            if decision["tool_name"]:
                st.markdown(f"**Tool:** `{decision['tool_name']}`")
            if decision["arguments"]:
                st.markdown("**Arguments:**")
                st.json(decision["arguments"])
            if step["output"] is not None:
                st.markdown("**Output:**")
                st.write(step["output"])
            if step["created_tool"]:
                created = step["created_tool"]
                st.markdown(
                    f"**Created tool:** `{created['name']}` – {created['description']}"
                )
                st.markdown(f"Signature: `{created['signature']}`")
                st.code(created["code"], language="python")
            if step["error"]:
                st.error(step["error"])

    final_output = result_payload["final_output"]
    if final_output is not None:
        st.subheader("Final output")
        st.write(final_output)

if "_orchestrator" in st.session_state:
    with st.sidebar:
        st.markdown("---")
        st.header("Registered tools")
        tool_manager = st.session_state["_orchestrator"].tool_manager
        tools = tool_manager.available_tools()
        if tools:
            for tool in tools:
                st.markdown(f"**{tool.name}** {tool.signature}")
                st.caption(tool.description)
        else:
            st.caption("No tools registered yet.")
