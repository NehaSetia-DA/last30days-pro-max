import unittest

from last30days_pro_max.competitors import (
    Competitor,
    REGISTRY,
    by_name,
    competitor_for_host,
    detect_competitor,
)
from last30days_pro_max.query_pack import DEFAULT_COMPETITORS


class RegistryShapeTests(unittest.TestCase):
    def test_every_entry_has_name_and_domains(self):
        self.assertTrue(REGISTRY)
        for entry in REGISTRY:
            self.assertIsInstance(entry, Competitor)
            self.assertTrue(entry.name, "competitor name must be non-empty")
            self.assertTrue(entry.domains, f"{entry.name} must have at least one domain")

    def test_all_default_competitors_plus_zyte_present(self):
        names = {entry.name for entry in REGISTRY}
        for expected in DEFAULT_COMPETITORS:
            self.assertIn(expected, names)
        self.assertIn("Zyte", names)


class LookupTests(unittest.TestCase):
    def test_by_name_is_case_insensitive(self):
        self.assertEqual(by_name("apify").name, "Apify")
        self.assertEqual(by_name("APIFY").name, "Apify")

    def test_by_name_unknown_returns_none(self):
        self.assertIsNone(by_name("nope"))

    def test_competitor_for_host_matches_subdomain(self):
        self.assertEqual(competitor_for_host("docs.apify.com"), "Apify")
        self.assertEqual(competitor_for_host("apify.com"), "Apify")

    def test_competitor_for_host_non_competitor_returns_none(self):
        self.assertIsNone(competitor_for_host("reddit.com"))


class DetectCompetitorTests(unittest.TestCase):
    def test_domain_match_wins(self):
        result = detect_competitor(
            title="Some AI agent post",
            url="https://www.firecrawl.dev/blog/mcp-server",
            snippet="mentions Apify and others",
            query='"AI agent" "web scraping"',
            names=DEFAULT_COMPETITORS,
        )
        self.assertEqual(result, "Firecrawl")

    def test_title_mention_outranks_snippet_mention(self):
        # Regression: a "Firecrawl alternatives" thread must NOT be tagged Apify
        # just because Apify appears in the snippet and is earlier in the list.
        result = detect_competitor(
            title="Discussion: Firecrawl alternatives for scraping with LLMs",
            url="https://www.reddit.com/r/webscraping/comments/x/",
            snippet="Developers compare Firecrawl, Apify, Zyte, Browserbase, ScrapeGraphAI",
            query='"AI agent" "web scraping"',
            names=DEFAULT_COMPETITORS,
        )
        self.assertEqual(result, "Firecrawl")

    def test_no_competitor_returns_none(self):
        result = detect_competitor(
            title="A general article about the open web",
            url="https://example.com/article",
            snippet="No vendors named here at all.",
            query='"open web"',
            names=DEFAULT_COMPETITORS,
        )
        self.assertEqual(result, "None")


if __name__ == "__main__":
    unittest.main()
