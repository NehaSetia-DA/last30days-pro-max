import unittest

from last30days_pro_max.normalize import classify_source_type, normalize_serp_result


class NormalizeTests(unittest.TestCase):
    def test_classifies_competitor_docs_and_reddit(self):
        self.assertEqual(classify_source_type("https://docs.apify.com/platform"), "competitor-docs")
        self.assertEqual(classify_source_type("https://www.reddit.com/r/webscraping/comments/abc"), "community-reddit")

    def test_normalize_serp_result_preserves_rank_query_and_competitor(self):
        item = normalize_serp_result(
            raw={"rank": 1, "title": "Firecrawl MCP", "url": "https://www.firecrawl.dev/blog/mcp", "snippet": "MCP for web data"},
            query='"MCP" "web scraping"',
            fetched_at="2026-06-09T00:00:00Z",
            competitors=["Apify", "Firecrawl"],
        )
        self.assertEqual(item["evidence_id"], "pending")
        self.assertEqual(item["competitor"], "Firecrawl")
        self.assertEqual(item["source_type"], "competitor-site")
        self.assertEqual(item["query"], '"MCP" "web scraping"')
        self.assertEqual(item["serp_rank"], 1)


if __name__ == "__main__":
    unittest.main()
