from __future__ import annotations

import base64
import gzip
import json
import os
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


MOCK_RESULTS = [
    {
        "rank": 1,
        "title": "Firecrawl MCP server for AI agents",
        "url": "https://www.firecrawl.dev/blog/mcp-server",
        "snippet": "Firecrawl introduces MCP tooling so agents can search, crawl, and extract web data.",
        "displayedUrl": "firecrawl.dev/blog/mcp-server",
    },
    {
        "rank": 2,
        "title": "Apify actors for AI agent workflows",
        "url": "https://blog.apify.com/ai-agents-web-scraping/",
        "snippet": "Apify positions Actors as tools for browser automation and AI agent web scraping.",
        "displayedUrl": "blog.apify.com",
    },
    {
        "rank": 3,
        "title": "Nimble Browser and AI data agents",
        "url": "https://www.nimbleway.com/blog/ai-agent-web-data",
        "snippet": "Nimble discusses browser automation infrastructure for AI agents collecting public web data.",
        "displayedUrl": "nimbleway.com/blog",
    },
    {
        "rank": 4,
        "title": "Discussion: Firecrawl alternatives for scraping with LLMs",
        "url": "https://www.reddit.com/r/webscraping/comments/mock/firecrawl_alternatives/",
        "snippet": "Developers compare Firecrawl, Apify, Zyte, Browserbase, and ScrapeGraphAI for LLM extraction.",
        "displayedUrl": "reddit.com/r/webscraping",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def search_zyte(
    query: str,
    *,
    domain: str,
    max_results: int,
    api_key: str | None = None,
    mock: bool = False,
    retries: int = 3,
    backoff: float = 2.0,
) -> dict:
    """Call Zyte Search API, or return deterministic mock data.

    Mock mode is intentionally first-class so the project can be built, tested,
    and handed to Claude without needing Zyte credentials on day one.

    The live SERP endpoint intermittently returns HTTP 500 and is slow, so
    transient 5xx/timeout failures are retried (``retries`` attempts with a
    linear ``backoff``). Permanent 4xx errors (e.g. an unsupported ``domain``)
    fail fast without retrying.
    """
    if mock:
        return {
            "status": "mock",
            "url": f"https://{domain}/search?q={query}",
            "fetchedAt": utc_now(),
            "organicResults": MOCK_RESULTS[:max(1, min(max_results, len(MOCK_RESULTS)))],
        }

    # Zyte requires maxResults to be a multiple of 10 within [10, 100]; an
    # out-of-range value 400s ("Format of field maxResults is invalid").
    valid_max = max(10, min(100, ((max_results + 5) // 10) * 10))
    return zyte_post(
        "search",
        {"domain": domain, "query": query, "include": ["organic"], "maxResults": valid_max},
        api_key=api_key,
        retries=retries,
        backoff=backoff,
    )


def zyte_post(
    path: str,
    payload: dict,
    *,
    api_key: str | None = None,
    retries: int = 3,
    backoff: float = 2.0,
) -> dict:
    """POST ``payload`` to ``https://api.zyte.com/v1/{path}`` and parse the JSON.

    Shared by the Search (``search``) and extraction (``extract``) endpoints.
    Handles Basic auth, gzip decompression, and retry-on-transient-failure:
    5xx/timeouts are retried (``retries`` attempts, linear ``backoff``); 4xx
    fails fast since it is permanent (bad domain, bad request, etc.).
    """
    api_key = api_key or os.environ.get("ZYTE_API_KEY")
    if not api_key:
        raise RuntimeError("ZYTE_API_KEY is required unless --mock is used")

    body = json.dumps(payload).encode("utf-8")
    token = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        f"https://api.zyte.com/v1/{path}",
        data=body,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": "last30days-pro-max/0.1",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            # Live Zyte calls are slow; 60s timed out in testing, 120s succeeds.
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
                # We advertise Accept-Encoding: gzip, and Zyte responds gzipped;
                # urllib does not auto-decompress, so do it before decoding.
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                detail = exc.read().decode("utf-8", "ignore")
                raise RuntimeError(
                    f"Zyte API /{path} failed: HTTP {exc.code}: {detail[:500]}"
                ) from exc
            last_error = exc  # 5xx is transient — retry.
        except (urllib.error.URLError, socket.timeout) as exc:
            last_error = exc  # network/timeout — retry.
        if attempt < retries - 1:
            time.sleep(backoff * (attempt + 1))
    raise RuntimeError(
        f"Zyte API /{path} failed after {retries} attempt(s): {last_error}"
    ) from last_error
