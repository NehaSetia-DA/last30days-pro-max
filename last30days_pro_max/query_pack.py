from __future__ import annotations

import re


DEFAULT_SEED_KEYWORDS = [
    "MCP web scraping",
    "AI agent web scraping",
    "LLM web data extraction",
    "Firecrawl alternatives",
    "Apify vs Firecrawl",
    "browser automation web data agent",
]

DEFAULT_COMPETITORS = [
    "Apify",
    "Firecrawl",
    "Nimble",
    "Bright Data",
    "ScraperAPI",
    "Browserbase",
    "ScrapeGraphAI",
    "Tavily",
    "Exa",
]


def quote_phrase(phrase: str) -> str:
    """Quote a search phrase, preserving explicit boolean-ish user terms lightly."""
    cleaned = " ".join(phrase.strip().split())
    if not cleaned:
        return ""
    words = cleaned.split()
    # Keep common operator phrase structure useful for SERP search.
    if len(words) == 3 and words[1].lower() == "vs":
        return f'"{words[0]}" vs "{words[2]}"'
    if cleaned.lower() == "mcp web scraping":
        return '"MCP" "web scraping"'
    if cleaned.lower() == "ai agent web scraping":
        return '"AI agent" "web scraping"'
    if cleaned.lower() == "llm web data extraction":
        return '"LLM" "web data extraction"'
    if cleaned.lower() == "browser automation web data agent":
        return '"browser automation" "web data" "agent"'
    return f'"{cleaned}"'


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "topic"


def build_query_pack(seed_keywords: list[str] | None = None, competitors: list[str] | None = None) -> list[str]:
    """Build a compact query pack from Neha's seed keywords plus competitors.

    The goal is not to create infinite search. It is to create enough breadth to
    surface agentic-web narratives, competitor positioning, alternatives, and
    comparison pages.
    """
    seed_keywords = seed_keywords or DEFAULT_SEED_KEYWORDS
    competitors = competitors or DEFAULT_COMPETITORS

    queries: list[str] = []
    for keyword in seed_keywords:
        quoted = quote_phrase(keyword)
        if quoted:
            queries.append(quoted)

    for competitor in competitors:
        queries.append(f'"{competitor}" "MCP" OR "AI agent" OR "web scraping"')
        queries.append(f'"{competitor}" "LLM" "web data"')
        queries.append(f'"{competitor}" alternatives')

    # Pairwise comparisons for the highest-signal named competitors.
    for left, right in zip(competitors, competitors[1:]):
        queries.append(f'"{left}" vs "{right}"')
    if "Apify" in competitors and "Firecrawl" in competitors:
        queries.append('"Apify" vs "Firecrawl"')
    if "Zyte" not in competitors:
        queries.append('"Zyte" "Firecrawl" OR "Apify"')
        queries.append('"Zyte" "AI agent" "web scraping"')

    deduped: list[str] = []
    seen = set()
    for query in queries:
        key = query.lower()
        if key not in seen:
            deduped.append(query)
            seen.add(key)
    return deduped
