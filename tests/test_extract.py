import base64
import unittest
from unittest import mock

from last30days_pro_max import extract


class ExtractTests(unittest.TestCase):
    def test_mock_mode_returns_deterministic_non_empty_quote(self):
        url = "https://www.firecrawl.dev/blog/mcp-server"
        first = extract.extract_pages([url], mock=True)
        self.assertEqual(len(first), 1)
        page = first[0]
        self.assertEqual(page["status"], "mock")
        self.assertEqual(page["url"], url)
        self.assertTrue(page["quote"])
        # Deterministic: same input → same quote (mock mode must be reproducible).
        again = extract.extract_pages([url], mock=True)
        self.assertEqual(page["quote"], again[0]["quote"])

    def test_live_extract_decodes_and_strips_html(self):
        html = (
            b"<html><head><style>.x{color:red}</style></head><body>"
            b"<h1>Heading</h1><p>Real page text about MCP web scraping.</p>"
            b"<script>evil()</script></body></html>"
        )
        response = {"url": "u", "httpResponseBody": base64.b64encode(html).decode("ascii")}
        with mock.patch.object(extract, "zyte_post", return_value=response):
            pages = extract.extract_pages(["https://example.com/x"], mock=False, api_key="k")
        page = pages[0]
        self.assertEqual(page["status"], "ok")
        self.assertIn("Real page text about MCP web scraping.", page["quote"])
        self.assertNotIn("evil()", page["quote"])   # <script> stripped
        self.assertNotIn(".x{color", page["quote"])  # <style> stripped
        self.assertNotIn("<", page["quote"])          # tags stripped

    def test_live_extract_handles_error_without_crashing(self):
        with mock.patch.object(extract, "zyte_post", side_effect=RuntimeError("boom")):
            pages = extract.extract_pages(["https://example.com/x"], mock=False, api_key="k")
        page = pages[0]
        self.assertEqual(page["status"], "error")
        self.assertEqual(page["quote"], "")
        self.assertIn("boom", page["error"])

    def test_extract_deduplicates_repeated_urls(self):
        url = "https://example.com/x"
        calls = []

        def fake_post(path, payload, **kwargs):
            calls.append(payload["url"])
            return {"httpResponseBody": base64.b64encode(b"<p>hello world</p>").decode("ascii")}

        with mock.patch.object(extract, "zyte_post", side_effect=fake_post):
            pages = extract.extract_pages([url, url, url], mock=False, api_key="k")
        self.assertEqual(len(calls), 1)          # only fetched once
        self.assertEqual(len(pages), 1)


if __name__ == "__main__":
    unittest.main()
