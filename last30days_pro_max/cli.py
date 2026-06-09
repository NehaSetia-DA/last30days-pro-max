from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from .connectors import search_hn, search_reddit
from .extract import extract_pages
from .normalize import assign_evidence_ids, normalize_serp_result
from .query_pack import DEFAULT_COMPETITORS, DEFAULT_SEED_KEYWORDS, build_query_pack, slugify
from .report import build_indexed_report
from .store import compute_deltas, connect, save_run
from .zyte_search import search_zyte, utc_now


def parse_csv_arg(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [part.strip() for part in value.split(",") if part.strip()]


def date_range_label(days: int) -> str:
    today = date.today()
    start = today - timedelta(days=days)
    return f"{start.isoformat()} → {today.isoformat()}"


def run(args: argparse.Namespace) -> Path:
    seed_keywords = parse_csv_arg(args.seed_keywords, DEFAULT_SEED_KEYWORDS)
    competitors = parse_csv_arg(args.competitors, DEFAULT_COMPETITORS)
    queries = build_query_pack(seed_keywords=seed_keywords, competitors=competitors)
    if args.query_limit:
        queries = queries[: args.query_limit]

    run_id = args.run_id or f"{date.today().isoformat()}-{slugify(args.topic)}"
    out_dir = Path(args.output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_payloads: list[dict] = []
    evidence: list[dict] = []
    for query in queries:
        payload = search_zyte(
            query,
            domain=args.domain,
            max_results=args.max_results,
            mock=args.mock,
        )
        raw_payloads.append({"query": query, "payload": payload})
        fetched_at = payload.get("fetchedAt") or ""
        for raw in payload.get("organicResults", []):
            evidence.append(normalize_serp_result(raw, query, fetched_at, competitors))

    if args.hn:
        # Direct Hacker News developer signal, searched by plain seed keyword.
        for keyword in seed_keywords:
            payload = search_hn(keyword, max_results=args.hn_max, mock=args.mock, days=args.days)
            raw_payloads.append({"query": f"HN:{keyword}", "payload": payload})
            fetched_at = payload.get("fetchedAt") or ""
            for raw in payload.get("organicResults", []):
                evidence.append(normalize_serp_result(raw, keyword, fetched_at, competitors))

    if args.reddit:
        # Reddit developer signal via Zyte (Reddit 403s unauthenticated bots).
        for keyword in seed_keywords:
            payload = search_reddit(keyword, max_results=args.reddit_max, mock=args.mock, days=args.days)
            raw_payloads.append({"query": f"Reddit:{keyword}", "payload": payload})
            if payload.get("status") == "error":
                print(
                    f"  warning: Reddit fetch for {keyword!r} failed: {payload.get('error', '')}",
                    file=sys.stderr,
                )
            fetched_at = payload.get("fetchedAt") or ""
            for raw in payload.get("organicResults", []):
                evidence.append(normalize_serp_result(raw, keyword, fetched_at, competitors))

    evidence = assign_evidence_ids(evidence)

    extracted_pages: list[dict] = []
    if args.extract:
        # Extract page-level quotes for the top-ranked unique URLs (cost-capped).
        target_urls: list[str] = []
        seen_urls: set[str] = set()
        for item in evidence:
            url = item.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                target_urls.append(url)
            if args.extract_top and len(target_urls) >= args.extract_top:
                break
        extracted_pages = extract_pages(target_urls, mock=args.mock)
        by_url = {page["url"]: page for page in extracted_pages}
        for item in evidence:
            page = by_url.get(item.get("url"))
            if page is None:
                item["extract_status"] = "skipped"
                continue
            item["extract_status"] = page["status"]
            if page.get("quote"):
                item["quote"] = page["quote"]
        (out_dir / "extracted_pages.jsonl").write_text(
            "".join(json.dumps(page) + "\n" for page in extracted_pages), encoding="utf-8"
        )

    deltas = None
    if not args.no_store:
        db_path = args.db or str(Path(args.output_dir) / "last30days.db")
        conn = connect(db_path)
        try:
            # Compute deltas against the previous run BEFORE saving this one.
            deltas = compute_deltas(conn, run_id=run_id, topic=args.topic, evidence=evidence)
            save_run(
                conn,
                run_id=run_id,
                topic=args.topic,
                created_at=utc_now(),
                days=args.days,
                evidence=evidence,
            )
        finally:
            conn.close()

    report = build_indexed_report(
        topic=args.topic,
        competitors=competitors,
        seed_keywords=seed_keywords,
        evidence=evidence,
        date_range=date_range_label(args.days),
        run_id=run_id,
        deltas=deltas,
    )

    (out_dir / "brief.md").write_text(report, encoding="utf-8")
    (out_dir / "raw_serp_results.json").write_text(json.dumps(raw_payloads, indent=2), encoding="utf-8")
    (out_dir / "evidence.jsonl").write_text("".join(json.dumps(item) + "\n" for item in evidence), encoding="utf-8")
    write_evidence_csv(out_dir / "evidence.csv", evidence)
    (out_dir / "queries_used.json").write_text(json.dumps(queries, indent=2), encoding="utf-8")
    metadata = {
        "run_id": run_id,
        "topic": args.topic,
        "days": args.days,
        "domain": args.domain,
        "max_results": args.max_results,
        "mock": args.mock,
        "competitors": competitors,
        "seed_keywords": seed_keywords,
        "evidence_count": len(evidence),
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return out_dir


def write_evidence_csv(path: Path, evidence: list[dict]) -> None:
    fields = [
        "evidence_id",
        "source_type",
        "competitor",
        "query",
        "serp_rank",
        "title",
        "url",
        "displayed_url",
        "snippet",
        "fetched_at",
        "date_confidence",
        "theme_tags",
        "product_area",
        "signal_type",
        "confidence",
        "why_it_matters",
        "recommended_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in evidence:
            row = dict(item)
            row["theme_tags"] = ",".join(row.get("theme_tags", []))
            writer.writerow({field: row.get(field, "") for field in fields})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a Last30Days Pro Max product + competitor intelligence report.")
    parser.add_argument("--topic", default="agentic web scraping")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--competitors", help="Comma-separated competitor names")
    parser.add_argument("--seed-keywords", help="Comma-separated seed keywords")
    parser.add_argument("--domain", default="google.com", help="Zyte Search API supported search domain (live-confirmed: google.com)")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--query-limit", type=int, default=6, help="Limit queries for cheap spikes")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--run-id")
    parser.add_argument("--mock", action="store_true", help="Use deterministic sample SERP results instead of Zyte API")
    parser.add_argument("--extract", action="store_true", help="Fetch top SERP URLs for page-level quotes (extra Zyte cost in live mode)")
    parser.add_argument("--extract-top", type=int, default=5, help="Max unique URLs to extract when --extract is set")
    parser.add_argument("--db", help="SQLite path for run history (default: <output-dir>/last30days.db)")
    parser.add_argument("--no-store", action="store_true", help="Disable run persistence and delta comparison")
    parser.add_argument("--hn", action="store_true", help="Add direct Hacker News developer signal (public Algolia API, no key)")
    parser.add_argument("--hn-max", type=int, default=5, help="HN stories per seed keyword when --hn is set")
    parser.add_argument("--reddit", action="store_true", help="Add Reddit developer signal via Zyte (Reddit blocks unauthenticated bots)")
    parser.add_argument("--reddit-max", type=int, default=5, help="Reddit threads per seed keyword when --reddit is set")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out_dir = run(args)
    print(f"Report written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
