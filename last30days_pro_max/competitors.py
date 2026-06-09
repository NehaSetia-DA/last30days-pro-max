"""Canonical competitor registry and entity detection.

This replaces the old order-dependent string heuristics with a structured
registry plus a relevance-ranked detector. Attribution is:

1. domain-first  — if a page is *on* a competitor's domain, that's the
   competitor (highest confidence);
2. otherwise relevance-ranked — weight a mention by where it appears
   (title > url > snippet/query), tie-broken by earliest position, not by
   the order competitors happen to be listed in.

Registry metadata kept conservative: ``domains``, ``keywords`` and
``github_orgs`` are high-confidence; ``docs_urls`` / ``blog_urls`` /
``changelog_urls`` are filled only where the canonical pattern is well known
and left empty otherwise rather than guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(frozen=True)
class Competitor:
    name: str
    domains: list[str]
    docs_urls: list[str] = field(default_factory=list)
    blog_urls: list[str] = field(default_factory=list)
    changelog_urls: list[str] = field(default_factory=list)
    github_orgs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


REGISTRY: list[Competitor] = [
    Competitor(
        name="Apify",
        domains=["apify.com"],
        docs_urls=["https://docs.apify.com"],
        blog_urls=["https://blog.apify.com"],
        github_orgs=["apify"],
        keywords=["apify"],
    ),
    Competitor(
        name="Firecrawl",
        domains=["firecrawl.dev"],
        docs_urls=["https://docs.firecrawl.dev"],
        blog_urls=["https://www.firecrawl.dev/blog"],
        changelog_urls=["https://www.firecrawl.dev/changelog"],
        github_orgs=["mendableai", "firecrawl"],
        keywords=["firecrawl"],
    ),
    Competitor(
        name="Nimble",
        domains=["nimbleway.com"],
        docs_urls=["https://docs.nimbleway.com"],
        blog_urls=["https://www.nimbleway.com/blog"],
        github_orgs=["Nimbleway"],
        keywords=["nimbleway", "nimble"],
    ),
    Competitor(
        name="Bright Data",
        domains=["brightdata.com"],
        docs_urls=["https://docs.brightdata.com"],
        blog_urls=["https://brightdata.com/blog"],
        github_orgs=["luminati-io", "brightdata"],
        keywords=["bright data", "brightdata", "luminati"],
    ),
    Competitor(
        name="ScraperAPI",
        domains=["scraperapi.com"],
        docs_urls=["https://docs.scraperapi.com"],
        blog_urls=["https://www.scraperapi.com/blog"],
        github_orgs=["scraperapi"],
        keywords=["scraperapi", "scraper api"],
    ),
    Competitor(
        name="Browserbase",
        domains=["browserbase.com"],
        docs_urls=["https://docs.browserbase.com"],
        blog_urls=["https://www.browserbase.com/blog"],
        github_orgs=["browserbase"],
        keywords=["browserbase"],
    ),
    Competitor(
        name="ScrapeGraphAI",
        domains=["scrapegraphai.com"],
        docs_urls=["https://docs.scrapegraphai.com"],
        github_orgs=["ScrapeGraphAI"],
        keywords=["scrapegraphai", "scrapegraph"],
    ),
    Competitor(
        name="Tavily",
        domains=["tavily.com"],
        docs_urls=["https://docs.tavily.com"],
        blog_urls=["https://blog.tavily.com"],
        github_orgs=["tavily-ai"],
        keywords=["tavily"],
    ),
    Competitor(
        name="Exa",
        domains=["exa.ai"],
        docs_urls=["https://docs.exa.ai"],
        github_orgs=["exa-labs"],
        keywords=["exa"],
    ),
    Competitor(
        name="Zyte",
        domains=["zyte.com"],
        docs_urls=["https://docs.zyte.com"],
        blog_urls=["https://www.zyte.com/blog"],
        github_orgs=["zytedata", "scrapy"],
        keywords=["zyte", "scrapinghub"],
    ),
]


_BY_NAME = {c.name.lower(): c for c in REGISTRY}

# Field weights for relevance ranking: a mention in the title says far more
# about what a result is *about* than a passing mention in a snippet.
_FIELD_WEIGHTS = (("title", 3), ("url", 2), ("snippet", 1), ("query", 1))


def by_name(name: str) -> Competitor | None:
    """Case-insensitive registry lookup by canonical name."""
    return _BY_NAME.get((name or "").lower())


def normalize_host(host: str) -> str:
    """Lower-case a host and strip a leading ``www.``."""
    return host.lower().removeprefix("www.")


def host_of(url: str) -> str:
    return normalize_host(urlparse(url).netloc)


def competitor_for_host(host: str, names: list[str] | None = None) -> str | None:
    """Return the competitor whose domain owns ``host`` (incl. subdomains)."""
    host = normalize_host(host)
    allowed = {n.lower() for n in names} if names is not None else None
    for competitor in REGISTRY:
        if allowed is not None and competitor.name.lower() not in allowed:
            continue
        for domain in competitor.domains:
            domain = domain.lower()
            if host == domain or host.endswith("." + domain):
                return competitor.name
    return None


def _keywords_for(name: str) -> list[str]:
    entry = by_name(name)
    if entry and entry.keywords:
        return entry.keywords
    # Custom competitor not in the registry: fall back to its own name.
    return [name.lower()]


def _matches(text: str, keyword: str) -> bool:
    return re.search(r"\b" + re.escape(keyword) + r"\b", text) is not None


def _first_position(text: str, keywords: list[str]) -> int:
    best = len(text)
    for keyword in keywords:
        match = re.search(r"\b" + re.escape(keyword) + r"\b", text)
        if match is not None:
            best = min(best, match.start())
    return best


def detect_competitor(
    title: str,
    url: str,
    snippet: str,
    query: str,
    names: list[str],
) -> str:
    """Attribute a SERP result to a competitor, or ``"None"``.

    Domain ownership wins outright; otherwise the active competitors are
    relevance-ranked by weighted field mentions, tie-broken by the earliest
    position of a mention (never by list order).
    """
    domain_match = competitor_for_host(host_of(url), names)
    if domain_match:
        return domain_match

    fields = {
        "title": (title or "").lower(),
        "url": (url or "").lower(),
        "snippet": (snippet or "").lower(),
        "query": (query or "").lower(),
    }
    combined = " ".join(fields.values())

    ranked = []
    for name in names:
        keywords = _keywords_for(name)
        score = 0
        for field_name, weight in _FIELD_WEIGHTS:
            if any(_matches(fields[field_name], kw) for kw in keywords):
                score += weight
        if score:
            ranked.append((score, _first_position(combined, keywords), name))

    if not ranked:
        return "None"

    # Highest score first; ties broken by earliest mention, then stable.
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2]
