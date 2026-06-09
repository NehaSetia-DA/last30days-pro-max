from __future__ import annotations

from urllib.parse import urlparse

from .competitors import competitor_for_host, detect_competitor


THEME_KEYWORDS = {
    "mcp": ["mcp", "model context protocol"],
    "ai-agent": ["ai agent", "agentic", "agents"],
    "browser-automation": ["browser automation", "browser agent", "headless", "playwright"],
    "llm-extraction": ["llm", "extraction", "structured data"],
    "serp": ["serp", "search api", "search results"],
    "data-quality": ["data quality", "validation", "schema"],
}


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def classify_source_type(url: str) -> str:
    host = _host(url)
    path = urlparse(url).path.lower()
    if "reddit.com" in host:
        return "community-reddit"
    if "github.com" in host:
        return "github"
    if "news.ycombinator.com" in host or "ycombinator.com" in host:
        return "community-hn"
    if "x.com" in host or "twitter.com" in host:
        return "social-x"
    if host.startswith("docs.") or "/docs" in path or "docs" in host:
        return "competitor-docs"
    if competitor_for_host(host) is not None:
        return "competitor-site"
    if "/blog" in path or "blog" in host:
        return "blog"
    return "web"


def infer_signal_type(source_type: str, competitor: str, text: str) -> str:
    lower = text.lower()
    if competitor != "None" and source_type in {"competitor-site", "competitor-docs", "blog"}:
        if any(word in lower for word in ["launch", "release", "introducing", "new", "changelog"]):
            return "competitor-shipping"
        return "competitor-positioning"
    if "alternative" in lower or " vs " in lower or "compare" in lower:
        return "comparison"
    if source_type.startswith("community"):
        if any(word in lower for word in ["issue", "problem", "can't", "blocked", "broken", "hard"]):
            return "developer-pain"
        return "community-signal"
    return "market-move"


def infer_theme_tags(text: str) -> list[str]:
    lower = text.lower()
    tags = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            tags.append(tag)
    return tags or ["agentic-web"]


def infer_product_area(text: str) -> str:
    lower = text.lower()
    if "serp" in lower or "search" in lower:
        return "serp"
    if "browser" in lower or "playwright" in lower or "javascript" in lower:
        return "browser"
    if "extract" in lower or "structured" in lower:
        return "extract"
    if "schema" in lower or "quality" in lower or "valid" in lower:
        return "validate"
    if "docs" in lower or "example" in lower or "tutorial" in lower:
        return "docs"
    if "price" in lower or "pricing" in lower:
        return "pricing"
    return "positioning"


def normalize_serp_result(raw: dict, query: str, fetched_at: str, competitors: list[str]) -> dict:
    title = raw.get("title") or "Untitled result"
    url = raw.get("url") or ""
    snippet = raw.get("snippet") or ""
    combined = " ".join([title, url, snippet, query])
    competitor = detect_competitor(title, url, snippet, query, competitors)
    source_type = classify_source_type(url)
    return {
        "evidence_id": "pending",
        "source_type": source_type,
        "competitor": competitor,
        "query": query,
        "serp_rank": raw.get("rank"),
        "title": title,
        "url": url,
        "displayed_url": raw.get("displayedUrl") or _host(url),
        "snippet": snippet,
        "quote": snippet,
        "published_at": raw.get("publishedAt") or "",
        "fetched_at": fetched_at,
        "date_confidence": "medium" if fetched_at else "low",
        "theme_tags": infer_theme_tags(combined),
        "product_area": infer_product_area(combined),
        "signal_type": infer_signal_type(source_type, competitor, combined),
        "confidence": "medium" if source_type != "web" else "low",
        "why_it_matters": build_why_it_matters(competitor, source_type, title),
        "recommended_action": build_recommended_action(competitor, source_type, combined),
    }


def assign_evidence_ids(items: list[dict]) -> list[dict]:
    for index, item in enumerate(items, start=1):
        item["evidence_id"] = f"E{index:03d}"
    return items


def build_why_it_matters(competitor: str, source_type: str, title: str) -> str:
    if competitor != "None" and competitor != "Zyte":
        return f"{competitor} is visible in the agentic web/search landscape for: {title}."
    if source_type.startswith("community"):
        return "Developer/community language may reveal pain, comparison criteria, or hidden feature requests."
    return "SERP-visible evidence affects what builders discover when researching agentic web scraping."


def build_recommended_action(competitor: str, source_type: str, text: str) -> str:
    lower = text.lower()
    if "mcp" in lower:
        return "Map this against Zyte's MCP / agent tooling story and consider a concrete demo or docs page."
    if competitor != "None" and competitor != "Zyte":
        return f"Review {competitor}'s positioning and identify a Zyte counter-example, comparison, or content gap."
    if source_type.startswith("community"):
        return "Convert repeated developer language into docs, examples, or product questions."
    return "Review for product/DevRel positioning relevance."
