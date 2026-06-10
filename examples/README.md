# Examples — using Last30Days Pro Max

You **don't run commands** day-to-day. After a one-time setup, you talk to Claude
in plain English and it calls the right tool for you. This page is a copy-paste
playbook for the **Marketing** and **Product** teams.

## Setup (once, ~2 minutes)

```bash
# 1. install
pip install "git+https://github.com/NehaSetia-DA/last30days-pro-max.git"

# 2. connect it to Claude (Code or Desktop). For live web data, add your Zyte key:
claude mcp add last30days -e ZYTE_API_KEY=YOUR_KEY -- last30days-pro-max-mcp
```

Then **restart Claude** and start asking. No key? Skip it and add `use mock mode`
to any prompt for an instant, free preview of the format.

> Tip: not technical? Run the bundled `./setup.sh` from the repo folder — it wires
> everything up and prints these prompts for you.

---

## 🎯 Marketing playbook

Paste any of these into Claude:

| Goal | Prompt |
|---|---|
| **Read a competitor's positioning** | *"Run a competitor report on Firecrawl and summarize how they're marketing to AI agents."* |
| **Find content gaps** | *"What 'X vs Apify' comparison content exists right now, and where's the gap for Zyte to publish?"* |
| **Spot the narrative** | *"Across Apify and Firecrawl, what's the dominant way the market frames the choice between them?"* |
| **Track week-over-week** | *"Run this again and tell me what changed since last week — new pages, fading topics, ranking shifts."* |
| **Ship a deliverable** | *"Turn that into a one-page PDF for the team."* |

**What you get back:** an indexed brief where every claim links to a real source
(competitor blogs, Reddit threads, agent directories), plus a short list of
recommended actions — and a shareable PDF if you ask for one.

---

## 🛠️ Product playbook

| Goal | Prompt |
|---|---|
| **Hear what developers want** | *"Run a listening report on 'MCP web scraping' — what are developers actually asking for?"* |
| **Find the pain** | *"What pain points show up around anti-bot and browser automation for AI agents?"* |
| **Compare a feature surface** | *"Compare how Apify and Firecrawl position their MCP servers."* |
| **Scan the dev channels** | *"Pull the Hacker News and Reddit discussion on agentic web scraping from the last 30 days."* |
| **Watch the space** | *"What new tools or entrants showed up in the agent web-scraping conversation this month?"* |

**What you get back:** developer-signal evidence (Hacker News + Reddit + search),
classified by theme and competitor, with the real threads and posts cited.

---

## What a report looks like

See [`sample-brief.md`](sample-brief.md) for a full example (generated in mock
mode, so it uses deterministic sample data — live runs return real, current web
evidence in the same shape).

## The tools under the hood

When you ask in plain English, Claude picks from these (you never call them directly):

- `run_report` — the full pipeline, returns a brief + evidence *(start here)*
- `build_query_pack` — the competitor-aware search plan
- `search_serp` — one search query via the Zyte Search API
- `normalize_evidence` — classify raw results into evidence
- `generate_report` — render the indexed brief from evidence

Add `use mock mode` to any request to run free, offline, and instantly.
