"""Dynamic tool creation and execution utilities."""

from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import ToolingConfig
from .llm import LLMClient


@dataclass
class ToolSpec:
    """Description of a tool available to the agent."""

    name: str
    description: str
    signature: str
    code: str
    callable: Callable[..., Any]


class ToolExecutionError(RuntimeError):
    """Raised when a tool invocation fails."""


class ToolManager:
    """Stores and manages dynamically created tools."""

    def __init__(self, config: ToolingConfig) -> None:
        self._config = config
        self._tools: Dict[str, ToolSpec] = {}
        self._generated_module = Path(config.generated_module_path)
        if self._config.auto_persist:
            self._ensure_generated_module()

        self._load_persisted_tools()

    # ------------------------------------------------------------------
    # Registration & execution
    # ------------------------------------------------------------------

    def register(
        self,
        func: Callable[..., Any],
        description: str,
        signature: str | None = None,
        *,
        persist: bool = False,
    ) -> ToolSpec:
        """Register an existing callable as a tool."""

        try:
            code = inspect.getsource(func)
        except (OSError, TypeError):
            code = f"# Source unavailable for {func.__name__}\\n"
        spec = ToolSpec(
            name=func.__name__,
            description=description,
            signature=signature or str(inspect.signature(func)),
            code=code,
            callable=func,
        )
        self._tools[spec.name] = spec

        if self._config.auto_persist and persist:
            self._append_to_generated_module(code)
        return spec

    def get(self, name: str) -> ToolSpec:
        """Return the registered tool specification."""

        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def available_tools(self) -> List[ToolSpec]:
        """Return a list of available tools."""

        return list(self._tools.values())

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered tool and return the result."""

        try:
            tool = self.get(name)
            return tool.callable(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - best effort logging
            raise ToolExecutionError(f"Tool '{name}' failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Dynamic creation
    # ------------------------------------------------------------------

    def create_tool(
        self,
        llm: LLMClient,
        specification: str,
        expected_name: Optional[str] = None,
    ) -> ToolSpec:
        """Generate and register a tool based on an LLM specification."""

        system_prompt = (
            "You generate production-ready Python helper functions. "
            "Respond ONLY with valid Python code defining the function."
        )
        user_prompt = (
            "Create a Python function that satisfies the specification below. "
            "Use a descriptive docstring that explains inputs and return values.\\n\\n"
            f"{specification.strip()}"
        )
        code = llm.simple_completion(system_prompt, user_prompt)
        if expected_name:
            code = self._enforce_function_name(code, expected_name)
        func = self._load_function_from_code(code, expected_name)
        signature = str(inspect.signature(func))
        description = inspect.getdoc(func) or "No description provided."

        return self._store_tool(
            func=func,
            description=description,
            signature=signature,
            code=code,
            persist=self._config.auto_persist,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_generated_module(self) -> None:
        module_path = self._generated_module
        if not module_path.exists():
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text("# Generated tool functions.\\n\\n", encoding="utf-8")

    def _append_to_generated_module(self, code: str) -> None:
        module_path = self._generated_module
        module_path.parent.mkdir(parents=True, exist_ok=True)
        with module_path.open("a", encoding="utf-8") as handle:
            handle.write("\\n" + code.strip() + "\\n")

    def _store_tool(
        self,
        *,
        func: Callable[..., Any],
        description: str,
        signature: str,
        code: str,
        persist: bool,
    ) -> ToolSpec:
        spec = ToolSpec(
            name=func.__name__,
            description=description,
            signature=signature,
            code=code,
            callable=func,
        )
        self._tools[spec.name] = spec
        if persist:
            self._append_to_generated_module(code)
        return spec

    def _load_function_from_code(
        self, code: str, expected_name: Optional[str]
    ) -> Callable[..., Any]:
        namespace: Dict[str, Any] = {}
        exec(textwrap.dedent(code), namespace)
        functions = {name: obj for name, obj in namespace.items() if callable(obj)}
        if expected_name:
            if expected_name not in functions:
                raise ValueError(
                    f"Generated code does not define the expected function '{expected_name}'."
                )
            return functions[expected_name]
        if not functions:
            raise ValueError("No callable objects were generated.")
        if len(functions) > 1:
            first_name = sorted(functions.keys())[0]
            return functions[first_name]
        return next(iter(functions.values()))

    def _enforce_function_name(self, code: str, expected_name: str) -> str:
        lines = code.splitlines()
        for index, line in enumerate(lines):
            if line.strip().startswith("def "):
                indent = line[: line.index("def ")]
                rest = line.strip().split("def ", 1)[1]
                if "(" not in rest:
                    raise ValueError("Malformed function definition from LLM.")
                remainder = rest[rest.index("(") :]
                lines[index] = f"{indent}def {expected_name}{remainder}"
                return "\\n".join(lines)
        raise ValueError("Unable to find function definition in generated code.")

    def _load_persisted_tools(self) -> None:
        if not self._generated_module.exists():
            return
        source = self._generated_module.read_text(encoding="utf-8")
        if not source.strip():
            return
        module = ast.parse(source)
        lines = source.splitlines()
        namespace: Dict[str, Any] = {}
        exec(source, namespace)
        for node in module.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            start = node.lineno - 1
            end = (node.end_lineno or node.lineno) - 1
            code_snippet = "\\n".join(lines[start : end + 1])
            func = namespace.get(node.name)
            if not callable(func):
                continue
            description = inspect.getdoc(func) or "No description provided."
            signature = str(inspect.signature(func))
            self._store_tool(
                func=func,
                description=description,
                signature=signature,
                code=code_snippet,
                persist=False,
            )
