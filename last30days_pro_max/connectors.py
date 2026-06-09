"""Direct developer-signal connectors.

SERP discovery under-represents community discussion. This module adds direct
connectors that return results in the same shape as ``zyte_search.search_zyte``
(a payload with ``organicResults`` of ``{rank, title, url, snippet,
displayedUrl}``) so they flow through the existing normalize pipeline unchanged.

First connector: **Hacker News** via the public Algolia API (no auth, no key),
which also supports a real freshness window — giving ``--days`` actual teeth.
Reddit/GitHub/X are deliberately deferred until their auth stories are settled
(see the implementation plan: add one connector at a time).
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from .zyte_search import search_zyte, utc_now

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

# Deterministic developer-signal sample for --mock (no network).
HN_MOCK_RESULTS = [
    {
        "rank": 1,
        "title": "Show HN: An MCP server for web scraping with Firecrawl",
        "url": "https://news.ycombinator.com/item?id=40000001",
        "snippet": "152 points, 88 comments on Hacker News. Links to https://github.com/example/mcp-scraper.",
        "displayedUrl": "news.ycombinator.com",
    },
    {
        "rank": 2,
        "title": "Ask HN: Best way to extract structured data for LLM agents?",
        "url": "https://news.ycombinator.com/item?id=40000002",
        "snippet": "97 points, 140 comments on Hacker News. Developers debate Apify vs Firecrawl vs Zyte for agent web data.",
        "displayedUrl": "news.ycombinator.com",
    },
    {
        "rank": 3,
        "title": "Browser automation is hard: lessons from building an AI agent",
        "url": "https://news.ycombinator.com/item?id=40000003",
        "snippet": "210 points, 175 comments on Hacker News. Playwright, headless browsers, and bot-detection pain.",
        "displayedUrl": "news.ycombinator.com",
    },
]


def _hit_to_result(rank: int, hit: dict) -> dict:
    object_id = hit.get("objectID", "")
    title = hit.get("title") or hit.get("story_title") or "Hacker News story"
    points = hit.get("points") or 0
    comments = hit.get("num_comments") or 0
    snippet = f"{points} points, {comments} comments on Hacker News."
    external = hit.get("url")
    if external:
        snippet += f" Links to {external}."
    story_text = (hit.get("story_text") or "").strip()
    if story_text:
        snippet += f" {story_text[:200]}"
    return {
        "rank": rank,
        "title": title,
        # Point at the HN discussion so it classifies as community-hn.
        "url": f"https://news.ycombinator.com/item?id={object_id}",
        "snippet": snippet,
        "displayedUrl": "news.ycombinator.com",
    }


def search_hn(
    query: str,
    *,
    max_results: int = 10,
    mock: bool = False,
    days: int | None = None,
    timeout: int = 30,
) -> dict:
    """Search Hacker News stories for ``query`` and return SERP-shaped results."""
    if mock:
        return {
            "status": "mock-hn",
            "url": f"{HN_SEARCH_URL}?query={query}",
            "fetchedAt": utc_now(),
            "organicResults": HN_MOCK_RESULTS[: max(1, min(max_results, len(HN_MOCK_RESULTS)))],
        }

    params = {"query": query, "tags": "story", "hitsPerPage": max_results}
    if days:
        cutoff = int(time.time()) - days * 86400
        params["numericFilters"] = f"created_at_i>{cutoff}"
    url = f"{HN_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "last30days-pro-max/0.1", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    results = [_hit_to_result(i, hit) for i, hit in enumerate(data.get("hits", []), start=1)]
    return {
        "status": "ok",
        "url": url,
        "fetchedAt": utc_now(),
        "organicResults": results,
    }


# Deterministic Reddit developer-signal sample for --mock (no network).
REDDIT_MOCK_RESULTS = [
    {
        "rank": 1,
        "title": "Firecrawl alternatives for scraping with LLMs?",
        "url": "https://www.reddit.com/r/webscraping/comments/mock1/firecrawl_alternatives/",
        "snippet": "r/webscraping · 84 points, 53 comments. Developers compare Firecrawl, Apify, Zyte, and Browserbase for agent web data.",
        "displayedUrl": "reddit.com/r/webscraping",
    },
    {
        "rank": 2,
        "title": "Is anyone using MCP servers for production web scraping?",
        "url": "https://www.reddit.com/r/LocalLLaMA/comments/mock2/mcp_servers_scraping/",
        "snippet": "r/LocalLLaMA · 121 points, 67 comments. Discussion of MCP tooling reliability for AI agent data extraction.",
        "displayedUrl": "reddit.com/r/LocalLLaMA",
    },
    {
        "rank": 3,
        "title": "Bot detection keeps breaking my AI agent's browser automation",
        "url": "https://www.reddit.com/r/webscraping/comments/mock3/bot_detection_agents/",
        "snippet": "r/webscraping · 59 points, 41 comments. Pain around headless browsers, proxies, and anti-bot blocks.",
        "displayedUrl": "reddit.com/r/webscraping",
    },
]


def search_reddit(
    query: str,
    *,
    max_results: int = 10,
    mock: bool = False,
    domain: str = "google.com",
    api_key: str | None = None,
    days: int | None = None,
) -> dict:
    """Discover Reddit threads for ``query`` via Zyte (Zyte-native, no Reddit key).

    Reddit's own endpoints 403/520-ban bots — even through Zyte's anti-ban tiers
    (search/listing/post ``.json`` all return "website ban"). Google, however,
    has Reddit fully indexed, so we run a ``site:reddit.com`` query through the
    Zyte Search API and keep the Reddit results. This stays entirely Zyte-native
    and needs no Reddit credentials. (``days`` is accepted for signature parity
    but Google SERP has no reliable date filter here.) Degrades gracefully on
    failure instead of crashing the run.
    """
    if mock:
        return {
            "status": "mock-reddit",
            "url": f"https://www.google.com/search?q=site:reddit.com+{query}",
            "fetchedAt": utc_now(),
            "organicResults": REDDIT_MOCK_RESULTS[: max(1, min(max_results, len(REDDIT_MOCK_RESULTS)))],
        }

    serp_query = f"site:reddit.com {query}"
    try:
        payload = search_zyte(serp_query, domain=domain, max_results=max_results, api_key=api_key)
    except Exception as exc:  # noqa: BLE001 - optional connector must not crash the run
        return {
            "status": "error",
            "url": serp_query,
            "error": f"{type(exc).__name__}: {exc}"[:300],
            "fetchedAt": utc_now(),
            "organicResults": [],
        }

    results = []
    for raw in payload.get("organicResults", []):
        url = raw.get("url") or ""
        if "reddit.com" not in url:
            continue
        results.append({
            "rank": len(results) + 1,
            "title": raw.get("title") or "Reddit thread",
            "url": url,
            "snippet": raw.get("snippet") or "",
            "displayedUrl": raw.get("displayedUrl") or "reddit.com",
        })
    return {
        "status": "ok",
        "url": serp_query,
        "fetchedAt": payload.get("fetchedAt") or utc_now(),
        "organicResults": results,
    }
