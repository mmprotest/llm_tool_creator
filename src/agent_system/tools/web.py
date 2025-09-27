"""Web browsing helper tools."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

_DDG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
}

try:  # pragma: no cover - optional dependency
    from duckduckgo_search import DDGS  # type: ignore
except Exception:  # pragma: no cover - fallback when package missing
    DDGS = None


@dataclass
class SearchResult:
    """Structure for parsed DuckDuckGo search results."""

    title: str
    href: Optional[str]
    body: Optional[str]

    def as_dict(self) -> dict:
        return {"title": self.title, "href": self.href, "body": self.body}


def web_search(query: str, max_results: int = 5) -> List[dict]:
    """Perform a DuckDuckGo search and return structured results."""

    if not query:
        raise ValueError("Query must be provided.")

    results: List[SearchResult] = []

    if DDGS is not None:
        with DDGS() as search:
            for item in search.text(query, max_results=max_results):
                results.append(
                    SearchResult(
                        title=(item.get("title") or "").strip(),
                        href=item.get("href"),
                        body=(item.get("body") or None),
                    )
                )
        if results:
            return [result.as_dict() for result in results]

    results.extend(_duckduckgo_html_fallback(query, max_results))
    if not results:
        results.extend(_duckduckgo_instant_answer_fallback(query, max_results))
    return [result.as_dict() for result in results[:max_results]]


def fetch_url(url: str, timeout: int = 15) -> str:
    """Retrieve the raw text content for ``url``."""

    if not url:
        raise ValueError("URL must be provided.")
    response = requests.get(url, timeout=timeout, headers=_DDG_HEADERS)
    response.raise_for_status()
    return response.text


def _duckduckgo_html_fallback(query: str, max_results: int) -> Iterable[SearchResult]:
    params = {"q": query, "kl": "us-en"}
    response = requests.get(
        "https://duckduckgo.com/html", params=params, timeout=15, headers=_DDG_HEADERS
    )
    response.raise_for_status()
    html_text = response.text
    pattern = re.compile(
        r"<a[^>]+class=\"result__a[^\"]*\"[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )
    snippet_pattern = re.compile(
        r"<a[^>]+class=\"result__snippet[^\"]*\"[^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )
    titles = list(pattern.finditer(html_text))
    snippets = list(snippet_pattern.finditer(html_text))

    def normalise_href(href: str) -> str:
        href = html.unescape(href)
        if href.startswith("/l/?"):
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            if "uddg" in params:
                return unquote(params["uddg"][0])
            return urljoin("https://duckduckgo.com", href)
        return href

    results: List[SearchResult] = []
    for index, match in enumerate(titles):
        if len(results) >= max_results:
            break
        href_raw, title_raw = match.groups()
        title = _strip_html(title_raw)
        href = normalise_href(href_raw)
        body = None
        if index < len(snippets):
            body = _strip_html(snippets[index].group(1)) or None
        results.append(SearchResult(title=title, href=href, body=body))
    return results


def _duckduckgo_instant_answer_fallback(query: str, max_results: int) -> Iterable[SearchResult]:
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    response = requests.get(
        "https://api.duckduckgo.com/", params=params, timeout=15, headers=_DDG_HEADERS
    )
    response.raise_for_status()
    data = response.json()
    results: List[SearchResult] = []
    abstract = data.get("AbstractText")
    abstract_url = data.get("AbstractURL")
    heading = data.get("Heading")
    if abstract:
        results.append(
            SearchResult(
                title=(heading or abstract),
                href=abstract_url,
                body=abstract,
            )
        )
    for topic in data.get("RelatedTopics", []) or []:
        if not isinstance(topic, dict):
            continue
        if "Topics" in topic:
            for subtopic in topic.get("Topics", []) or []:
                if not isinstance(subtopic, dict):
                    continue
                text = subtopic.get("Text")
                url = subtopic.get("FirstURL")
                if text and url:
                    results.append(SearchResult(title=text, href=url, body=text))
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break
        else:
            text = topic.get("Text")
            url = topic.get("FirstURL")
            if text and url:
                results.append(SearchResult(title=text, href=url, body=text))
                if len(results) >= max_results:
                    break
    return results[:max_results]


def _strip_html(raw_html: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", raw_html)
    return html.unescape(cleaned).strip()
