import json
import unittest
from unittest import mock

from last30days_pro_max import connectors
from last30days_pro_max.normalize import normalize_serp_result


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class HackerNewsConnectorTests(unittest.TestCase):
    def test_mock_mode_returns_deterministic_hn_discussions(self):
        first = connectors.search_hn("MCP web scraping", mock=True)
        self.assertTrue(first["organicResults"])
        for item in first["organicResults"]:
            self.assertIn("news.ycombinator.com/item", item["url"])
            self.assertTrue(item["snippet"])
        again = connectors.search_hn("MCP web scraping", mock=True)
        self.assertEqual(first["organicResults"], again["organicResults"])

    def test_live_maps_algolia_hits_to_discussion_results(self):
        algolia = {
            "hits": [
                {
                    "objectID": "40000001",
                    "title": "Show HN: An MCP server for web scraping",
                    "url": "https://example.com/mcp-scraper",
                    "points": 152,
                    "num_comments": 88,
                    "author": "dev",
                }
            ]
        }
        with mock.patch.object(
            connectors.urllib.request, "urlopen",
            return_value=_FakeResponse(json.dumps(algolia).encode("utf-8")),
        ):
            payload = connectors.search_hn("MCP web scraping", mock=False)
        result = payload["organicResults"][0]
        self.assertEqual(result["url"], "https://news.ycombinator.com/item?id=40000001")
        self.assertEqual(result["displayedUrl"], "news.ycombinator.com")
        self.assertIn("152 points", result["snippet"])
        self.assertIn("88 comments", result["snippet"])

    def test_days_window_adds_recency_filter_to_request(self):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            return _FakeResponse(b'{"hits": []}')

        with mock.patch.object(connectors.urllib.request, "urlopen", side_effect=fake_urlopen):
            connectors.search_hn("q", mock=False, days=30)
        self.assertIn("numericFilters", captured["url"])
        self.assertIn("created_at_i", captured["url"])

    def test_hn_result_normalizes_to_community_hn_source(self):
        raw = connectors.search_hn("MCP web scraping", mock=True)["organicResults"][0]
        item = normalize_serp_result(raw, "MCP web scraping", "2026-06-09T00:00:00Z", ["Apify"])
        self.assertEqual(item["source_type"], "community-hn")


class RedditConnectorTests(unittest.TestCase):
    def test_mock_mode_returns_deterministic_reddit_threads(self):
        first = connectors.search_reddit("Firecrawl alternatives", mock=True)
        self.assertTrue(first["organicResults"])
        for item in first["organicResults"]:
            self.assertIn("reddit.com", item["url"])
            self.assertTrue(item["snippet"])
        again = connectors.search_reddit("Firecrawl alternatives", mock=True)
        self.assertEqual(first["organicResults"], again["organicResults"])

    def test_live_discovers_reddit_threads_via_zyte_site_search(self):
        # Reddit's own endpoints 520-ban bots, but Google has Reddit indexed —
        # so we discover threads with a site:reddit.com query through Zyte.
        serp = {
            "fetchedAt": "2026-06-09T00:00:00Z",
            "organicResults": [
                {"rank": 1, "title": "Firecrawl alternatives?",
                 "url": "https://www.reddit.com/r/LocalLLaMA/comments/abc/firecrawl_alts/",
                 "snippet": "Devs compare Firecrawl, Apify, Zyte.", "displayedUrl": "reddit.com"},
                {"rank": 2, "title": "Some blog (not reddit)",
                 "url": "https://example.com/blog", "snippet": "x", "displayedUrl": "example.com"},
            ],
        }
        captured = {}

        def fake_search_zyte(query, **kwargs):
            captured["query"] = query
            return serp

        with mock.patch.object(connectors, "search_zyte", side_effect=fake_search_zyte):
            result = connectors.search_reddit("Firecrawl alternatives", mock=False)

        # Issued a site-restricted Google query through Zyte.
        self.assertIn("site:reddit.com", captured["query"])
        self.assertIn("Firecrawl alternatives", captured["query"])
        # Only the Reddit URL is kept; the non-reddit result is filtered out.
        self.assertEqual(len(result["organicResults"]), 1)
        self.assertIn("reddit.com", result["organicResults"][0]["url"])

    def test_reddit_degrades_gracefully_when_zyte_fails(self):
        with mock.patch.object(connectors, "search_zyte", side_effect=RuntimeError("HTTP 520")):
            payload = connectors.search_reddit("anything", mock=False)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["organicResults"], [])
        self.assertIn("520", payload["error"])

    def test_reddit_result_normalizes_to_community_reddit_source(self):
        raw = connectors.search_reddit("Firecrawl alternatives", mock=True)["organicResults"][0]
        item = normalize_serp_result(raw, "Firecrawl alternatives", "2026-06-09T00:00:00Z", ["Apify"])
        self.assertEqual(item["source_type"], "community-reddit")


if __name__ == "__main__":
    unittest.main()
