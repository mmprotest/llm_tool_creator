"""Web browsing helper tools."""

from __future__ import annotations

from typing import List

import requests

try:  # pragma: no cover - optional dependency
    from duckduckgo_search import DDGS  # type: ignore
except Exception:  # pragma: no cover - fallback when package missing
    DDGS = None


def web_search(query: str, max_results: int = 5) -> List[dict]:
    """Perform a DuckDuckGo search and return structured results."""

    if not query:
        raise ValueError("Query must be provided.")
    results: List[dict] = []
    if DDGS is not None:
        with DDGS() as search:
            for item in search.text(query, max_results=max_results):
                results.append(
                    {
                        "title": item.get("title"),
                        "href": item.get("href"),
                        "body": item.get("body"),
                    }
                )
        return results
    # Simple HTML fallback
    params = {"q": query, "kl": "us-en"}
    response = requests.get("https://duckduckgo.com/html", params=params, timeout=15)
    response.raise_for_status()
    for line in response.text.splitlines():
        if "result__title" in line:
            results.append({"title": line.strip(), "href": None, "body": None})
            if len(results) >= max_results:
                break
    return results


def fetch_url(url: str, timeout: int = 15) -> str:
    """Retrieve the raw text content for ``url``."""

    if not url:
        raise ValueError("URL must be provided.")
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text
