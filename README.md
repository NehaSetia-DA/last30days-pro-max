# Last30Days Pro Max

> Competitor-aware product listening for the agentic web, powered by Zyte Search API.

## One-line idea

**Last30Days Pro Max** asks:

> What are developers, competitors, communities, and the search landscape saying and doing right now around agentic web scraping — and what should Zyte build, write, position, or respond to next?

This is not a generic trend report. It is a **full indexed product + competitor intelligence report** with evidence.

## Why this exists

The original [`mvanhorn/last30days-skill`](https://github.com/mvanhorn/last30days-skill) proves a powerful pattern:

```text
recent public signal → normalized evidence → ranked clusters → grounded brief
```

The Zyte-native Pro Max version sharpens that into:

```text
fresh SERP discovery → page/evidence extraction → competitor/product taxonomy → indexed report → action list
```

The goal is not to clone every source from `last30days-skill`. The goal is to make Zyte's Search API and extraction layer visible as the reliable web-data layer for agentic research.

## What it tracks

### Competitors

Default competitor set:

- Apify
- Firecrawl
- Nimble
- Bright Data
- ScraperAPI
- Browserbase
- ScrapeGraphAI
- Tavily
- Exa

Add later after entity verification:

- Pridedata / PrideData / PriceData — exact competitor identity still needs confirming.

### Seed keywords

Default seed keywords are based on Neha's preferred set:

```text
MCP web scraping
AI agent web scraping
LLM web data extraction
Firecrawl alternatives
Apify vs Firecrawl
browser automation web data agent
```

The query planner expands these with competitor-specific queries such as:

```text
"Apify" "MCP" OR "AI agent" OR "web scraping"
"Firecrawl" "LLM" "web data"
"Nimble" alternatives
"Apify" vs "Firecrawl"
"Zyte" "AI agent" "web scraping"
```

## Current status

This folder is a **working V0/V1 scaffold**:

- stdlib-only Python package
- deterministic `--mock` mode
- optional live Zyte Search API mode via `ZYTE_API_KEY`
- query pack generation
- SERP result normalization
- competitor/source/theme classification
- full indexed Markdown report generation
- evidence CSV/JSONL output
- unit tests using `unittest`

It is intentionally small so Claude Code, Hermes, or a human developer can extend it without inheriting the full complexity of `last30days-skill`.

## Folder structure

```text
last30days-pro-max/
  README.md
  CLAUDE.md
  pyproject.toml
  last30days_pro_max/
    __init__.py
    cli.py
    normalize.py
    query_pack.py
    report.py
    zyte_search.py
  tests/
    test_normalize.py
    test_query_pack.py
    test_report.py
  docs/
    implementation-plan.md
  outputs/
    ... generated reports live here
```

## Install

The package is **stdlib-only**, so install is fast and dependency-free.

```bash
# From a built wheel (build once: `python3 -m build` -> dist/*.whl)
pip install dist/last30days_pro_max-0.1.0-py3-none-any.whl

# Or editable, for development
pip install -e .

# Or straight from an internal Git remote
pip install "git+https://<your-internal-host>/last30days-pro-max.git"
```

After install, two commands are on your `PATH`:

```bash
last30days-pro-max          # the report CLI
last30days-pro-max-mcp      # the MCP server
```

Register the MCP with Claude Code — once installed, no `PYTHONPATH` needed:

```bash
claude mcp add last30days -e ZYTE_API_KEY=YOUR_KEY -- last30days-pro-max-mcp
```

**No install?** Run the bundled `./setup.sh` from the repo folder — it wires the
MCP into Claude Code and Claude Desktop directly (Zyte key optional; mock mode
needs none).

## Quickstart: mock mode

Run this first. It does not require credentials.

```bash
cd last30days-pro-max
python3 -m last30days_pro_max.cli \
  --mock \
  --topic "agentic web scraping" \
  --query-limit 3 \
  --run-id demo-mock
```

Expected output:

```text
Report written to outputs/demo-mock
```

Generated files:

```text
outputs/demo-mock/
  brief.md
  evidence.csv
  evidence.jsonl
  queries_used.json
  raw_serp_results.json
  run_metadata.json
```

Open the report:

```bash
open outputs/demo-mock/brief.md
```

## Live Zyte Search API mode

Set your Zyte API key:

```bash
export ZYTE_API_KEY="..."
```

Run:

```bash
python3 -m last30days_pro_max.cli \
  --topic "agentic web scraping" \
  --query-limit 6 \
  --max-results 10 \
  --domain "google.com" \
  --run-id live-agentic-web-scraping
```

Notes:

- `domain` must be a Zyte Search API supported search domain. **`google.com` is
  live-confirmed** (returns `200` with organic results) and is the CLI default;
  `search.engine.com` is only a docs placeholder and returns `400 Domain Not
  Supported`. Other engines (Bing, DuckDuckGo) were also rejected — contact Zyte
  support for the full supported-domain list.
- `max-results` should start low while testing because request weight scales with result count.
- The live SERP endpoint is slow (~tens of seconds) and intermittently returns
  HTTP 500; the client retries transient 5xx/timeout failures automatically.
- Use `--query-limit` during early development to avoid burning credits.

## CLI options

```bash
python3 -m last30days_pro_max.cli --help
```

Important options:

- `--mock`: use deterministic sample data, no Zyte API call.
- `--topic`: report topic.
- `--days`: date window label. V0 labels the report; V1 should enforce freshness filters where source dates exist.
- `--competitors`: comma-separated override competitor list.
- `--seed-keywords`: comma-separated override keyword list.
- `--domain`: Zyte Search API search domain.
- `--max-results`: organic results per query.
- `--query-limit`: cap number of generated queries for cheap spikes.
- `--extract`: after SERP discovery, fetch the top URLs via Zyte API `/extract`
  and attach page-level quotes (richer than snippets). Adds an
  `extracted_pages.jsonl` artifact. Costs extra Zyte credits in live mode;
  deterministic and free under `--mock`.
- `--extract-top`: max unique URLs to extract when `--extract` is set (default 5).
- `--db`: SQLite path for run history (default `<output-dir>/last30days.db`). Each
  run is stored so section 2 can diff against the previous run on the same topic
  and label evidence **new / recurring / fading / rank-changed**.
- `--no-store`: disable run persistence and delta comparison for this run.
- `--hn`: add direct **Hacker News** developer signal via the public Algolia API
  (no key required). Searches each seed keyword, returns HN discussion permalinks
  with points/comments, and respects `--days` as a real freshness window.
- `--hn-max`: HN stories per seed keyword when `--hn` is set (default 5).
- `--reddit`: add **Reddit** developer signal — **Zyte-native, no Reddit key**.
  Runs a `site:reddit.com <keyword>` query through the Zyte Search API and keeps
  the Reddit threads. Degrades gracefully if a call fails (logs a warning, never
  crashes the run). `--mock` is deterministic.
  - **Why via Google/Zyte and not Reddit directly:** Reddit `403`s
    unauthenticated bots, and testing showed its `.json` endpoints (search,
    listing, post) also `520` ("website ban") through Zyte's `httpResponseBody`
    *and* `browserHtml` tiers. But Zyte *can* fetch individual Reddit **post
    pages**, and Google has Reddit fully indexed — so a `site:reddit.com` SERP
    query is the reliable, credential-free path, and `--extract` can still pull
    page-level quotes from the discovered threads.
- `--reddit-max`: Reddit threads per seed keyword when `--reddit` is set (default 5).
- `--output-dir`: where generated run folders are written.
- `--run-id`: stable folder name for the run.

## MCP server (agent-callable tools)

The pipeline is also exposed over the **Model Context Protocol** so an agent can
drive it directly. The server is stdlib-only (JSON-RPC 2.0 over stdio, no MCP SDK
dependency):

```bash
python3 -m last30days_pro_max.mcp_server
```

Tools exposed (`tools/list`):

- `build_query_pack(seed_keywords, competitors)` — the competitor-aware query pack.
- `search_serp(query, domain, max_results, mock)` — one Zyte SERP query.
- `normalize_evidence(raw_results, query, competitors)` — classify raw results into evidence.
- `generate_report(evidence, topic, …)` — render the indexed Markdown brief.
- `run_report(topic, mock, query_limit, …)` — full pipeline end-to-end; returns the brief plus evidence. Use `mock=true` for a credential-free demo.

Register it with an MCP client (e.g. Claude Desktop / Claude Code) by pointing the
client at the command above. Every tool honors `mock` where applicable, so the
server is fully demoable without credentials.

## What the report contains

The generated `brief.md` is indexed:

```text
0. Index
1. Executive Summary
2. What Changed This Month
3. Developer Signal
4. Competitor Intelligence Index
5. Keyword / SERP Landscape
6. Agentic Web Themes
7. Product Opportunities for Zyte
8. Content / DevRel Opportunities
9. Competitive Threats and Gaps
10. Recommended Actions This Week
11. Evidence Index
12. Appendix: Raw Queries, Source Coverage, Warnings
```

Each evidence item is assigned an ID like `E001` and carries:

```json
{
  "evidence_id": "E001",
  "source_type": "competitor-site|community-reddit|github|blog|web|...",
  "competitor": "Apify|Firecrawl|Nimble|...|None",
  "query": "...",
  "serp_rank": 1,
  "title": "...",
  "url": "...",
  "snippet": "...",
  "fetched_at": "...",
  "theme_tags": ["mcp", "ai-agent"],
  "product_area": "serp|browser|extract|validate|docs|pricing|positioning",
  "signal_type": "competitor-shipping|competitor-positioning|developer-pain|comparison|market-move",
  "confidence": "high|medium|low",
  "why_it_matters": "...",
  "recommended_action": "..."
}
```

## Test command

```bash
python3 -m unittest discover -s tests -v
```

## Senior-dev build philosophy

Build the smallest thing that proves the loop:

```text
Zyte Search API discovers public evidence
→ evidence is normalized and classified
→ report is indexed and actionable
→ Zyte team can decide what to build/write/respond to
```

Do not start with:

- full `last30days-skill` clone
- UI
- TikTok/Instagram/Polymarket
- perfect X coverage
- Letta memory
- multi-agent debate
- scheduler/watchlist

Those become later layers after the first report is useful.

## V1 next steps

1. **Confirm live Zyte Search API domain.** Replace `search.engine.com` with a supported production domain from Zyte docs/internal setup.
2. **Entity resolution.** Add canonical domains/docs/blog/changelog/GitHub orgs for each competitor.
3. **Page extraction.** After SERP discovery, fetch/extract top URLs using Zyte API `/extract` or another internal Zyte mechanism.
4. **Better source connectors.** Add Reddit/HN/GitHub direct connectors for stronger developer/community signal.
5. **Historical persistence.** Store each run in SQLite, then add “new / recurring / fading / ranking changed.”
6. **Report quality.** Replace heuristic recommendations with LLM synthesis over the evidence pack.
7. **MCP wrapper.** Expose the pipeline as tools an agent can call.

## V2: Idea 2 layer

Once V1 reports are saved over time, add SERP drift and competitor watch:

- new competitor pages this week
- repeated themes
- fading themes
- ranking changes
- new SERP competitors
- new agentic positioning moves
- what changed since last run

Then the product becomes recurring intelligence, not a one-off report.

## Positioning line

> **Last30Days Pro Max is not just product listening. It is competitor-aware product listening for the agentic web.**
