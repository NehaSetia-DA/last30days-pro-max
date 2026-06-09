import unittest

from last30days_pro_max.report import build_indexed_report


class ReportTests(unittest.TestCase):
    def test_report_contains_index_competitors_and_evidence_ids(self):
        evidence = [
            {
                "evidence_id": "E001",
                "competitor": "Firecrawl",
                "title": "Firecrawl MCP",
                "url": "https://firecrawl.dev/blog/mcp",
                "snippet": "MCP launch",
                "query": '"MCP" "web scraping"',
                "source_type": "competitor-site",
                "signal_type": "competitor-positioning",
                "theme_tags": ["mcp", "ai-agent"],
                "why_it_matters": "Competitor is claiming agentic web data territory.",
                "recommended_action": "Publish Zyte MCP/search evidence demo.",
                "confidence": "medium",
            }
        ]
        report = build_indexed_report(
            topic="agentic web scraping",
            competitors=["Apify", "Firecrawl", "Nimble"],
            seed_keywords=["MCP web scraping"],
            evidence=evidence,
            date_range="2026-05-10 → 2026-06-09",
            run_id="test-run",
        )
        self.assertIn("# Last30Days Pro Max", report)
        self.assertIn("## 0. Index", report)
        self.assertIn("### 4.2 Firecrawl", report)
        self.assertIn("E001", report)
        self.assertIn("Publish Zyte MCP/search evidence demo", report)


if __name__ == "__main__":
    unittest.main()
