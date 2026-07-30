from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

from scripts.check_external_links import (
    CheckResult,
    canonical_http_url,
    check_url,
    check_urls,
    collect_external_links,
    load_allowlist,
)


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status
        self.bytes_read = 0

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return self.status

    def read(self, size: int) -> bytes:
        self.bytes_read += size
        return b"x"[:size]


class SequenceOpener:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout: float) -> object:
        self.calls.append((url, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class ExternalLinkCheckerTests(unittest.TestCase):
    def test_collects_http_links_deduplicated_without_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            page = root / "README.md"
            page.write_text(
                "[one](https://example.com/guide#one)\n"
                "[two](https://example.com/guide#two)\n"
                "[local](docs/page.md)\n"
                "```text\n"
                "[masked](https://invalid.example/)\n"
                "```\n",
                encoding="utf-8",
            )

            links, failures = collect_external_links(root, [page])

            self.assertEqual(failures, [])
            self.assertEqual(list(links), ["https://example.com/guide"])
            self.assertEqual(len(links["https://example.com/guide"]), 2)

    def test_canonical_url_rejects_credentials_and_missing_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "user information"):
            canonical_http_url("https://" + "user" + "@" + "example.com/path")
        with self.assertRaisesRegex(ValueError, "hostname"):
            canonical_http_url("https:///missing-host")

    def test_allowlist_requires_exact_urls_and_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            policy = Path(temp_dir) / "policy.json"
            policy.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "allowlist": [
                            {
                                "url": "https://example.com/page#section",
                                "reason": "Automated requests are blocked.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            allowlist = load_allowlist(policy)
            self.assertEqual(list(allowlist), ["https://example.com/page"])

            policy.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "allowlist": [
                            {"url": "https://example.com/page", "reason": ""}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "requires a reason"):
                load_allowlist(policy)

    def test_retries_transport_and_transient_http_failures(self) -> None:
        url = "https://example.com/"
        opener = SequenceOpener(
            [
                URLError("temporary DNS failure"),
                HTTPError(url, 503, "unavailable", {}, None),
                FakeResponse(200),
            ]
        )
        delays: list[float] = []

        result = check_url(
            url,
            timeout=7.5,
            retries=2,
            opener=opener,
            sleeper=delays.append,
        )

        self.assertEqual(result, CheckResult(url, True, 3, "HTTP 200"))
        self.assertEqual(opener.calls, [(url, 7.5), (url, 7.5), (url, 7.5)])
        self.assertEqual(delays, [1, 2])

    def test_does_not_retry_permanent_http_failure(self) -> None:
        url = "https://example.com/missing"
        opener = SequenceOpener([HTTPError(url, 404, "missing", {}, None)])

        result = check_url(
            url,
            timeout=5,
            retries=3,
            opener=opener,
            sleeper=lambda _: self.fail("permanent failure should not sleep"),
        )

        self.assertEqual(result, CheckResult(url, False, 1, "HTTP 404"))
        self.assertEqual(len(opener.calls), 1)

    def test_checks_each_unique_url_and_sorts_results(self) -> None:
        calls: list[str] = []

        def checker(url: str, *, timeout: float, retries: int) -> CheckResult:
            calls.append(url)
            return CheckResult(url, True, 1, f"{timeout}/{retries}")

        results = check_urls(
            ["https://b.example/", "https://a.example/", "https://b.example/"],
            timeout=3,
            retries=1,
            workers=2,
            checker=checker,
        )

        self.assertEqual(
            [result.url for result in results],
            ["https://a.example/", "https://b.example/"],
        )
        self.assertCountEqual(calls, ["https://a.example/", "https://b.example/"])


if __name__ == "__main__":
    unittest.main()
