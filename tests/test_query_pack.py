import unittest

from last30days_pro_max.query_pack import build_query_pack


class QueryPackTests(unittest.TestCase):
    def test_build_query_pack_combines_seed_keywords_and_competitors(self):
        queries = build_query_pack(
            seed_keywords=["MCP web scraping", "AI agent web scraping"],
            competitors=["Apify", "Firecrawl", "Nimble"],
        )

        self.assertIn('"MCP" "web scraping"', queries)
        self.assertIn('"AI agent" "web scraping"', queries)
        self.assertIn('"Apify" "MCP" OR "AI agent" OR "web scraping"', queries)
        self.assertIn('"Apify" vs "Firecrawl"', queries)
        self.assertEqual(len(queries), len(set(queries)))


if __name__ == "__main__":
    unittest.main()
