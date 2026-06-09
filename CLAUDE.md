# CLAUDE.md

You are helping build **Last30Days Pro Max**, a Zyte-native competitor-aware product listening engine for the agentic web.

## Product intent

Do not turn this into a generic trend scraper. The product question is:

> What are developers, competitors, communities, and the search landscape saying and doing right now around agentic web scraping — and what should Zyte build, write, position, or respond to next?

The output should be a full indexed report with evidence, not a loose summary.

## Important context

This project is inspired by `mvanhorn/last30days-skill`, but it should not clone it source-for-source.

The Zyte-native shape is:

```text
fresh SERP discovery
→ page/evidence extraction
→ competitor/product taxonomy
→ indexed report
→ action list
```

## Development rules

- Keep V1 small and useful.
- Use TDD for new behavior: write failing tests first, then implementation.
- Keep the package stdlib-only unless a dependency clearly pays for itself.
- Preserve deterministic `--mock` mode so the demo works without credentials.
- Use `python3 -m unittest discover -s tests -v` as the baseline test command.
- Avoid adding UI, scheduler, Letta, multi-agent orchestration, TikTok, Instagram, or Polymarket in V1.

## Current highest-value next tasks

1. Confirm the real Zyte Search API `domain` value to use instead of placeholder `search.engine.com`.
2. Add canonical competitor metadata:
   - domains
   - docs URLs
   - blog URLs
   - changelog/release URLs
   - GitHub orgs
3. Add page extraction after SERP discovery.
4. Add SQLite persistence for V2 deltas.
5. Add direct Reddit/HN/GitHub connectors for stronger developer signal.
6. Add LLM synthesis over `evidence.jsonl` once the deterministic evidence pack is reliable.

## Definition of done for a change

- Tests pass.
- Mock mode still generates a report.
- Report includes evidence IDs.
- Generated artifacts remain inspectable:
  - `brief.md`
  - `evidence.csv`
  - `evidence.jsonl`
  - `queries_used.json`
  - `raw_serp_results.json`
  - `run_metadata.json`
