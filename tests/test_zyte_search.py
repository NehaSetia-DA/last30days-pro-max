import gzip
import io
import json
import unittest
import urllib.error
from unittest import mock

from last30days_pro_max import zyte_search


class _FakeResponse:
    def __init__(self, body: bytes, headers: dict):
        self._body = body
        self.headers = headers

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ZyteSearchTests(unittest.TestCase):
    def test_mock_mode_needs_no_key_and_returns_organic_results(self):
        payload = zyte_search.search_zyte("q", domain="google.com", max_results=2, mock=True)
        self.assertEqual(payload["status"], "mock")
        self.assertTrue(payload["organicResults"])

    def test_search_zyte_decompresses_gzip_response(self):
        # Zyte returns gzip when we send Accept-Encoding: gzip; the client must
        # decompress before json.loads or live mode crashes with a decode error.
        body = gzip.compress(
            json.dumps(
                {"organicResults": [{"rank": 1, "title": "X", "url": "u", "snippet": "s"}],
                 "fetchedAt": "2026-06-09T00:00:00Z"}
            ).encode("utf-8")
        )
        fake = _FakeResponse(body, {"Content-Encoding": "gzip"})
        with mock.patch.object(zyte_search.urllib.request, "urlopen", return_value=fake):
            result = zyte_search.search_zyte(
                "q", domain="google.com", max_results=10, api_key="fake-key"
            )
        self.assertEqual(result["organicResults"][0]["title"], "X")

    def test_retries_on_transient_5xx_then_succeeds(self):
        # Zyte's SERP intermittently returns HTTP 500; a retry should recover.
        good = _FakeResponse(
            json.dumps({"organicResults": [{"rank": 1, "title": "Y"}]}).encode("utf-8"),
            {},
        )
        err = urllib.error.HTTPError("x", 500, "boom", None, io.BytesIO(b""))
        with mock.patch.object(
            zyte_search.urllib.request, "urlopen", side_effect=[err, good]
        ):
            result = zyte_search.search_zyte(
                "q", domain="google.com", max_results=10, api_key="k",
                retries=3, backoff=0,
            )
        self.assertEqual(result["organicResults"][0]["title"], "Y")

    def test_maxresults_coerced_to_valid_multiple_of_ten(self):
        # Zyte rejects maxResults that isn't a multiple of 10 in [10, 100]
        # ("Format of field maxResults is invalid"). Coerce before sending.
        captured = {}

        def fake_post(path, payload, **kwargs):
            captured.update(payload)
            return {"organicResults": []}

        with mock.patch.object(zyte_search, "zyte_post", side_effect=fake_post):
            zyte_search.search_zyte("q", domain="google.com", max_results=5, api_key="k")
            self.assertEqual(captured["maxResults"], 10)
            zyte_search.search_zyte("q", domain="google.com", max_results=250, api_key="k")
            self.assertEqual(captured["maxResults"], 100)

    def test_4xx_raises_immediately_without_retry(self):
        # A 400 (e.g. domain-not-supported) is permanent: fail fast, don't burn retries.
        err = urllib.error.HTTPError("x", 400, "bad", None, io.BytesIO(b'{"detail":"no"}'))
        calls = []

        def fake_urlopen(*args, **kwargs):
            calls.append(1)
            raise err

        with mock.patch.object(
            zyte_search.urllib.request, "urlopen", side_effect=fake_urlopen
        ):
            with self.assertRaises(RuntimeError):
                zyte_search.search_zyte(
                    "q", domain="search.engine.com", max_results=10, api_key="k",
                    retries=3, backoff=0,
                )
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
