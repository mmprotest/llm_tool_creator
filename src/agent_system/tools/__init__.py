"""Built-in tools available to the agent."""

from __future__ import annotations

from .code import run_python
from .web import fetch_url, web_search

__all__ = ["run_python", "web_search", "fetch_url"]


def register_default_tools(tool_manager) -> None:
    """Register default built-in tools with the provided manager."""

    tool_manager.register(
        web_search,
        description="Search the web using DuckDuckGo and return structured results.",
        signature="(query: str, max_results: int = 5) -> List[dict]",
    )
    tool_manager.register(
        fetch_url,
        description="Fetch the raw text content of a web page.",
        signature="(url: str, timeout: int = 15) -> str",
    )
    tool_manager.register(
        run_python,
        description="Execute Python code in an isolated namespace and return locals.",
        signature="(code: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]",
    )
