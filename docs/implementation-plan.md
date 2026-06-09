# Last30Days Pro Max Implementation Plan

> **For Claude/Hermes:** Implement task-by-task with TDD. Keep V1 small and evidence-first.

**Goal:** Build a Zyte-native product + competitor intelligence report engine for agentic web scraping.

**Architecture:** Start with SERP discovery through Zyte Search API, normalize evidence into JSONL/CSV, classify by competitor/theme/source type, and generate an indexed Markdown report. Add extraction, persistence, and MCP only after V1 report quality is useful.

**Tech Stack:** Python 3.9+ stdlib, Zyte Search API, unittest, JSONL/CSV/Markdown artifacts.

---

## Task 1: Confirm Zyte Search API live configuration

**Objective:** Replace placeholder `search.engine.com` with the correct supported search domain and validate one live request.

**Files:**
- Modify: `README.md`
- Modify: `last30days_pro_max/cli.py`
- Test: add or update `tests/test_cli_defaults.py`

**Steps:**
1. Check Zyte Search API docs/internal docs for supported `domain` values.
2. Write a test asserting the default domain is the selected value.
3. Run the test and verify it fails if the code still uses the placeholder.
4. Update CLI default.
5. Run tests.
6. Run one live query with `ZYTE_API_KEY` and `--query-limit 1 --max-results 10`.

**Verification:**

```bash
python3 -m unittest discover -s tests -v
ZYTE_API_KEY=... python3 -m last30days_pro_max.cli --topic "MCP web scraping" --query-limit 1 --max-results 10 --run-id live-smoke
```

Expected: `outputs/live-smoke/brief.md` exists and has evidence items from Zyte Search API.

---

## Task 2: Add competitor entity registry

**Objective:** Create a structured competitor registry so entity detection is not only string heuristics.

**Files:**
- Create: `last30days_pro_max/competitors.py`
- Modify: `last30days_pro_max/normalize.py`
- Test: `tests/test_competitors.py`

**Data model:**

```python
@dataclass(frozen=True)
class Competitor:
    name: str
    domains: list[str]
    docs_urls: list[str]
    blog_urls: list[str]
    github_orgs: list[str]
    keywords: list[str]
```

**Initial entries:**
- Apify
- Firecrawl
- Nimble
- Bright Data
- ScraperAPI
- Browserbase
- ScrapeGraphAI
- Tavily
- Exa

**Verification:**

```bash
python3 -m unittest tests.test_competitors -v
python3 -m unittest discover -s tests -v
```

---

## Task 3: Add page extraction layer

**Objective:** After SERP discovery, fetch/extract high-value URLs so the report can cite page-level evidence beyond snippets.

**Files:**
- Create: `last30days_pro_max/extract.py`
- Modify: `last30days_pro_max/cli.py`
- Test: `tests/test_extract.py`

**Design:**
- V1 function: `extract_pages(urls, mock=False)`.
- In mock mode, return deterministic extracted text.
- In live mode, call Zyte API `/extract` or a confirmed internal wrapper.
- Write `extracted_pages.jsonl`.
- Add extracted quote to evidence item if available.

**Verification:**

```bash
python3 -m last30days_pro_max.cli --mock --query-limit 2 --run-id extract-mock
```

Expected: generated report has quotes richer than SERP snippets.

---

## Task 4: Add SQLite persistence for run-over-run deltas

**Objective:** Store evidence across runs to enable Idea 2: new/recurring/fading/ranking-changed sections.

**Files:**
- Create: `last30days_pro_max/store.py`
- Modify: `last30days_pro_max/cli.py`
- Modify: `last30days_pro_max/report.py`
- Test: `tests/test_store.py`

**Schema:**

```sql
runs(run_id TEXT PRIMARY KEY, topic TEXT, created_at TEXT, days INTEGER)
evidence(evidence_id TEXT, run_id TEXT, url TEXT, query TEXT, title TEXT, snippet TEXT, competitor TEXT, source_type TEXT, serp_rank INTEGER, content_hash TEXT)
```

**Delta labels:**
- new
- recurring
- fading candidate
- rank changed

**Verification:**

Run two mock reports with modified mock data and assert report section 2 contains delta language.

---

## Task 5: Add direct developer-signal connectors

**Objective:** Strengthen “what developers are saying” beyond SERP-indexed snippets.

**Candidates:**
- Hacker News public API / Algolia endpoint
- GitHub Search API or `gh` CLI
- Reddit direct connector if access is approved
- X only if authenticated tooling is approved

**Rule:** Add one connector at a time with tests and source-specific normalization.

---

## Task 6: Add MCP wrapper

**Objective:** Expose the reliable evidence pipeline as agent-callable tools.

**Potential tools:**

```text
build_query_pack(topic, competitors, seed_keywords)
zyte_search_serp(query, domain, max_results)
normalize_evidence(raw_results)
write_indexed_report(evidence, audience)
save_evidence_pack(evidence)
```

**Do this only after CLI V1 proves useful.**

---

## Stop-doing list for V1

Do not add:

- UI
- scheduler
- TikTok/Instagram/Polymarket
- multi-agent debate
- Letta/memory framework
- complex RRF/reranking
- perfect social coverage

The V1 proof is simple:

> Can Zyte Search API + evidence normalization produce a useful competitor-aware report that Zyte product/DevRel would actually read?
