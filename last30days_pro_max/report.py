from __future__ import annotations

from collections import defaultdict


SECTION_INDEX = [
    "1. Executive Summary",
    "2. What Changed This Month",
    "3. Developer Signal",
    "4. Competitor Intelligence Index",
    "5. Keyword / SERP Landscape",
    "6. Agentic Web Themes",
    "7. Product Opportunities for Zyte",
    "8. Content / DevRel Opportunities",
    "9. Competitive Threats and Gaps",
    "10. Recommended Actions This Week",
    "11. Evidence Index",
    "12. Appendix: Raw Queries, Source Coverage, Warnings",
]


def group_by(items: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        grouped[item.get(key) or "Unknown"].append(item)
    return dict(grouped)


def build_indexed_report(
    *,
    topic: str,
    competitors: list[str],
    seed_keywords: list[str],
    evidence: list[dict],
    date_range: str,
    run_id: str,
    deltas: dict | None = None,
) -> str:
    by_competitor = group_by(evidence, "competitor")
    by_theme: dict[str, list[dict]] = defaultdict(list)
    for item in evidence:
        for tag in item.get("theme_tags", []):
            by_theme[tag].append(item)

    lines: list[str] = []
    lines.append("# Last30Days Pro Max: Agentic Web Scraping Market + Competitor Intelligence Report")
    lines.append("")
    lines.append(f"- **Run ID:** `{run_id}`")
    lines.append(f"- **Date range:** {date_range}")
    lines.append(f"- **Topic:** {topic}")
    lines.append("- **Audience:** Zyte Product, DevRel, Marketing, Sales")
    lines.append(f"- **Evidence items:** {len(evidence)}")
    lines.append("")

    lines.append("## 0. Index")
    lines.extend(f"- [{section}](#{_anchor(section)})" for section in SECTION_INDEX)
    lines.append("")

    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This run scans fresh public-web evidence for agentic web scraping, competitor positioning, and developer/community signals. Treat this report as a decision aid, not a final truth: every recommendation links back to evidence IDs in the Evidence Index.")
    lines.append("")
    top_competitors = [c for c in competitors if by_competitor.get(c)]
    if top_competitors:
        lines.append(f"- Competitors surfaced in evidence: {', '.join(top_competitors)}.")
    lines.append(f"- Strongest recurring themes: {', '.join(sorted(by_theme)[:8]) or 'none yet'}.")
    lines.append("- Core Zyte question: what should we build, write, position, or respond to next?")
    lines.append("")

    lines.append("## 2. What Changed This Month")
    lines.append("")
    _render_changed_section(lines, evidence, deltas)
    lines.append("")

    lines.append("## 3. Developer Signal")
    lines.append("")
    developer_items = [item for item in evidence if item.get("source_type", "").startswith("community")]
    if developer_items:
        for item in developer_items[:10]:
            lines.append(f"- **{item['evidence_id']}** — {item['snippet']}  ")
            lines.append(f"  Action: {item['recommended_action']}")
    else:
        lines.append("- No community/developer-specific evidence surfaced yet. Add Reddit/HN/GitHub queries or authenticated X in the next run.")
    lines.append("")

    lines.append("## 4. Competitor Intelligence Index")
    lines.append("")
    for idx, competitor in enumerate(competitors, start=1):
        lines.append(f"### 4.{idx} {competitor}")
        items = by_competitor.get(competitor, [])
        if not items:
            lines.append("- No strong evidence surfaced in this run.")
        for item in items[:8]:
            lines.append(f"- **{item['evidence_id']}** [{item['title']}]({item['url']})")
            lines.append(f"  - Signal: {item['signal_type']} · Source: {item['source_type']} · Confidence: {item['confidence']}")
            lines.append(f"  - Why it matters: {item['why_it_matters']}")
            lines.append(f"  - Zyte action: {item['recommended_action']}")
        lines.append("")

    lines.append("## 5. Keyword / SERP Landscape")
    lines.append("")
    by_query = group_by(evidence, "query")
    for keyword in seed_keywords:
        lines.append(f"- Seed keyword: `{keyword}`")
    lines.append("")
    for query, items in list(by_query.items())[:20]:
        lines.append(f"- `{query}` → {len(items)} evidence item(s); top: {items[0]['title']}")
    lines.append("")

    lines.append("## 6. Agentic Web Themes")
    lines.append("")
    for theme, items in sorted(by_theme.items(), key=lambda pair: len(pair[1]), reverse=True):
        ids = ", ".join(item["evidence_id"] for item in items[:8])
        lines.append(f"- **{theme}** — {len(items)} item(s): {ids}")
    lines.append("")

    lines.append("## 7. Product Opportunities for Zyte")
    lines.append("")
    lines.append("- Build demos and docs where competitors are claiming agentic/web-data language but Zyte has deeper extraction, browser, SERP, or reliability credibility.")
    lines.append("- Convert repeated developer complaints into product questions: access, freshness, extraction accuracy, schema quality, browser automation, and MCP/tooling.")
    lines.append("- Add evidence-backed comparison pages only where the report shows actual developer search/comparison demand.")
    lines.append("")

    lines.append("## 8. Content / DevRel Opportunities")
    lines.append("")
    lines.append("- Publish one concrete build post from the strongest theme, not a generic AI-agent essay.")
    lines.append("- Turn competitor-visible keywords into Zyte demos: Search API discovery → extraction → evidence pack → report.")
    lines.append("- Create short posts from developer-language snippets, preserving the real phrasing.")
    lines.append("")

    lines.append("## 9. Competitive Threats and Gaps")
    lines.append("")
    visible_competitors = [c for c in competitors if by_competitor.get(c)]
    if visible_competitors:
        lines.append(f"- Visible competitors in this run: {', '.join(visible_competitors)}.")
    lines.append("- Watch for competitors owning simple agent-facing language while Zyte explains deeper infrastructure too abstractly.")
    lines.append("- Watch for MCP/search/browser automation pages that become category entry points.")
    lines.append("")

    lines.append("## 10. Recommended Actions This Week")
    lines.append("")
    unique_actions = []
    for item in evidence:
        action = item.get("recommended_action", "")
        if action and action not in unique_actions:
            unique_actions.append(action)
    for action in unique_actions[:8]:
        lines.append(f"- {action}")
    lines.append("")

    lines.append("## 11. Evidence Index")
    lines.append("")
    for item in evidence:
        lines.append(f"### {item['evidence_id']} — {item['title']}")
        lines.append(f"- URL: {item['url']}")
        lines.append(f"- Query: `{item['query']}`")
        lines.append(f"- Competitor: {item['competitor']}")
        lines.append(f"- Source type: {item['source_type']}")
        lines.append(f"- SERP rank: {item.get('serp_rank', '')}")
        lines.append(f"- Snippet: {item.get('snippet', '')}")
        quote = item.get("quote", "")
        if quote and quote != item.get("snippet", ""):
            lines.append(f"- Quote (extracted): {quote}")
        lines.append(f"- Tags: {', '.join(item.get('theme_tags', []))}")
        lines.append(f"- Why it matters: {item.get('why_it_matters', '')}")
        lines.append(f"- Recommended action: {item.get('recommended_action', '')}")
        lines.append("")

    lines.append("## 12. Appendix: Raw Queries, Source Coverage, Warnings")
    lines.append("")
    lines.append("### Raw seed keywords")
    for keyword in seed_keywords:
        lines.append(f"- {keyword}")
    lines.append("")
    source_counts = group_by(evidence, "source_type")
    lines.append("### Source coverage")
    for source, items in sorted(source_counts.items()):
        lines.append(f"- {source}: {len(items)}")
    lines.append("")
    lines.append("### Warnings")
    lines.append("- Live Zyte Search API calls are the default (requires `ZYTE_API_KEY`). Pass `--mock` to use deterministic sample data instead.")
    lines.append("- SERP-discovered social results are incomplete; use authenticated Reddit/X/HN/GitHub connectors for stronger community coverage.")
    lines.append("- Historical delta sections require stored previous runs.")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def _render_changed_section(lines: list[dict], evidence: list[dict], deltas: dict | None) -> None:
    if not deltas or deltas.get("previous_run_id") is None:
        if deltas is not None:
            lines.append("No previous run stored for this topic yet — this run is the baseline. Re-run later to see new / recurring / fading / rank-changed deltas.")
        else:
            lines.append("Historical comparison is disabled for this run (no run store). Run with persistence enabled to diff against the previous run.")
        for item in evidence[:5]:
            lines.append(f"- **{item['evidence_id']}** — {item['title']} ({item.get('competitor', 'None')})")
        return

    lines.append(
        f"Compared against previous run `{deltas['previous_run_id']}` "
        f"({deltas.get('previous_created_at', '')})."
    )
    lines.append("")
    lines.append(f"- **New** this run: {len(deltas['new'])}")
    for item in deltas["new"][:8]:
        lines.append(f"  - {item.get('evidence_id', '')} {item.get('title', '')} ({item.get('competitor', 'None')})")
    lines.append(f"- **Recurring** (also in previous run): {len(deltas['recurring'])}")
    lines.append(f"- **Fading candidates** (in previous run, absent now): {len(deltas['fading'])}")
    for item in deltas["fading"][:8]:
        lines.append(f"  - {item.get('title', '')} (was rank {item.get('serp_rank', '')})")
    lines.append(f"- **Rank changed**: {len(deltas['rank_changed'])}")
    for change in deltas["rank_changed"][:8]:
        lines.append(
            f"  - {change.get('title', '')}: rank {change['old_rank']} → {change['new_rank']}"
        )


def _anchor(section: str) -> str:
    return section.lower().replace(".", "").replace("/", "").replace(" ", "-")
