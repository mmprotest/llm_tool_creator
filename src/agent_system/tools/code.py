"""Code execution helper tools."""

from __future__ import annotations

from typing import Any, Dict, Optional


def run_python(code: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute Python code in an isolated namespace and return locals."""

    if not code:
        raise ValueError("Code snippet must be provided.")
    sandbox: Dict[str, Any] = {}
    if variables:
        sandbox.update(variables)
    exec(code, {}, sandbox)
    return sandbox
