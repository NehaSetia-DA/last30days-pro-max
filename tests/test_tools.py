import unittest

from last30days_pro_max import tools


class ToolsTests(unittest.TestCase):
    def test_build_query_pack_returns_queries(self):
        out = tools.tool_build_query_pack(
            {"seed_keywords": ["MCP web scraping"], "competitors": ["Apify", "Firecrawl"]}
        )
        self.assertIn('"MCP" "web scraping"', out["queries"])
        self.assertEqual(out["count"], len(out["queries"]))

    def test_search_serp_mock_returns_organic_results(self):
        out = tools.tool_search_serp({"query": "MCP web scraping", "mock": True, "max_results": 3})
        self.assertTrue(out["organicResults"])
        self.assertLessEqual(len(out["organicResults"]), 3)

    def test_normalize_evidence_assigns_ids_and_competitor(self):
        raw = [{"rank": 1, "title": "Firecrawl MCP", "url": "https://firecrawl.dev/blog", "snippet": "x"}]
        out = tools.tool_normalize_evidence(
            {"raw_results": raw, "query": '"MCP"', "competitors": ["Apify", "Firecrawl"]}
        )
        self.assertEqual(out["evidence"][0]["evidence_id"], "E001")
        self.assertEqual(out["evidence"][0]["competitor"], "Firecrawl")

    def test_generate_report_returns_indexed_markdown(self):
        evidence = [{
            "evidence_id": "E001", "competitor": "Firecrawl", "title": "T",
            "url": "u", "snippet": "s", "query": "q", "source_type": "competitor-site",
            "signal_type": "x", "theme_tags": ["mcp"], "why_it_matters": "w",
            "recommended_action": "a", "confidence": "medium",
        }]
        out = tools.tool_generate_report({"evidence": evidence, "topic": "agentic web scraping"})
        self.assertIn("# Last30Days Pro Max", out["report_markdown"])
        self.assertIn("## 0. Index", out["report_markdown"])

    def test_run_report_mock_end_to_end(self):
        out = tools.tool_run_report({"mock": True, "query_limit": 2})
        self.assertGreater(out["evidence_count"], 0)
        self.assertIn("# Last30Days Pro Max", out["report_markdown"])
        self.assertEqual(len(out["evidence"]), out["evidence_count"])

    def test_run_report_skips_failed_queries_instead_of_crashing(self):
        # A transient Zyte 500 on one query must not kill the whole report.
        from unittest import mock as _mock

        good = {"fetchedAt": "t", "organicResults": [
            {"rank": 1, "title": "Apify", "url": "https://apify.com", "snippet": "x"}]}
        calls = {"n": 0}

        def flaky(query, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("Zyte API /search failed: HTTP 500")
            return good

        with _mock.patch.object(tools, "search_zyte", side_effect=flaky):
            out = tools.tool_run_report({"query_limit": 2, "seed_keywords": ["a", "b"], "competitors": []})

        self.assertGreater(out["evidence_count"], 0)        # the good query still produced evidence
        self.assertEqual(len(out["skipped_queries"]), 1)    # the failed query was recorded, not raised


if __name__ == "__main__":
    unittest.main()
