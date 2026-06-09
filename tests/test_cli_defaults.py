import unittest

from last30days_pro_max.cli import build_parser


class CliDefaultsTests(unittest.TestCase):
    def test_default_domain_is_live_confirmed_google(self):
        # Confirmed via live smoke test against api.zyte.com/v1/search:
        # "google.com" returns 200 with organic results; "search.engine.com"
        # (Zyte's docs placeholder) and bing/duckduckgo return 400.
        args = build_parser().parse_args([])
        self.assertEqual(args.domain, "google.com")


if __name__ == "__main__":
    unittest.main()
