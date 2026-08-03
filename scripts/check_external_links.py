#!/usr/bin/env python3
"""Monitor external HTTP(S) links outside the pull-request quality gate."""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urlsplit, urlunsplit
from urllib.request import Request, urlopen

if __package__:
    from .check_links import parse_document, tracked_markdown_paths
else:
    from check_links import parse_document, tracked_markdown_paths


USER_AGENT = (
    "utc-hpc-guide-link-monitor/1.0 "
    "(+https://github.com/M-Gage-Plott42/utc-hpc-guide)"
)
RETRYABLE_HTTP_STATUSES = {408, 425, 429, 500, 502, 503, 504}


@dataclass(frozen=True, order=True)
class Source:
    path: str
    line: int


@dataclass(frozen=True)
class AllowlistEntry:
    url: str
    reason: str


@dataclass(frozen=True)
class CheckResult:
    url: str
    success: bool
    attempts: int
    detail: str


def canonical_http_url(value: str) -> str:
    """Normalize an HTTP(S) destination for requests and exact allowlisting."""
    candidate = html.unescape(value.strip())
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    candidate, _ = urldefrag(candidate)
    parsed = urlsplit(candidate)
    if parsed.scheme.casefold() not in {"http", "https"}:
        raise ValueError("URL must use http or https")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL must not contain user information")
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc,
            parsed.path,
            parsed.query,
            "",
        )
    )


def collect_external_links(
    root: Path,
    markdown_paths: Iterable[Path],
) -> tuple[dict[str, set[Source]], list[str]]:
    """Collect de-fragmented HTTP(S) links and report malformed destinations."""
    links: dict[str, set[Source]] = {}
    failures: list[str] = []
    for path in markdown_paths:
        relative = path.relative_to(root).as_posix()
        parsed_links, parser_findings, _ = parse_document(
            path.read_text(encoding="utf-8")
        )
        for finding in parser_findings:
            failures.append(f"{relative}:{finding.line}: {finding.message}")
        for link in parsed_links:
            destination = html.unescape(link.destination.strip())
            parsed = urlsplit(
                "https:" + destination if destination.startswith("//") else destination
            )
            if parsed.scheme.casefold() not in {"http", "https"}:
                continue
            try:
                url = canonical_http_url(destination)
            except ValueError as exc:
                failures.append(
                    f"{relative}:{link.line}: invalid external link "
                    f"{link.destination!r}: {exc}"
                )
                continue
            links.setdefault(url, set()).add(Source(relative, link.line))
    return links, failures


def load_allowlist(policy_path: Path) -> dict[str, AllowlistEntry]:
    """Load an exact-URL allowlist whose entries require reviewable reasons."""
    raw = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("external-link policy version must be 1")
    entries = raw.get("allowlist")
    if not isinstance(entries, list):
        raise ValueError("external-link allowlist must be a list")

    allowlist: dict[str, AllowlistEntry] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"allowlist entry {index} must be an object")
        url = entry.get("url")
        url_fragments = entry.get("url_fragments")
        reason = entry.get("reason")
        if url is not None and url_fragments is not None:
            raise ValueError(
                f"allowlist entry {index} requires exactly one of URL or URL fragments"
            )
        if url_fragments is not None:
            if (
                not isinstance(url_fragments, list)
                or not url_fragments
                or any(
                    not isinstance(fragment, str) or not fragment
                    for fragment in url_fragments
                )
            ):
                raise ValueError(
                    f"allowlist entry {index} requires non-empty URL fragments"
                )
            url = "".join(url_fragments)
        if not isinstance(url, str) or not url:
            raise ValueError(
                f"allowlist entry {index} requires a URL or URL fragments"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"allowlist entry {index} requires a reason")
        canonical = canonical_http_url(url)
        if canonical in allowlist:
            raise ValueError(f"duplicate allowlist URL: {canonical}")
        allowlist[canonical] = AllowlistEntry(canonical, reason.strip())
    return allowlist


def _request(url: str, timeout: float):
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.1",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    return urlopen(request, timeout=timeout)


def check_url(
    url: str,
    *,
    timeout: float,
    retries: int,
    opener: Callable[[str, float], object] = _request,
    sleeper: Callable[[float], None] = time.sleep,
) -> CheckResult:
    """Fetch one byte, retrying transient HTTP and transport failures."""
    attempts = retries + 1
    last_detail = "request was not attempted"
    for attempt in range(1, attempts + 1):
        retryable = False
        try:
            response = opener(url, timeout)
            with response:
                status = getattr(response, "status", response.getcode())
                response.read(1)
            if 200 <= status < 400:
                return CheckResult(url, True, attempt, f"HTTP {status}")
            last_detail = f"HTTP {status}"
            retryable = status in RETRYABLE_HTTP_STATUSES
        except HTTPError as exc:
            last_detail = f"HTTP {exc.code}"
            retryable = exc.code in RETRYABLE_HTTP_STATUSES
        except (URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            last_detail = f"{type(exc).__name__}: {reason}"
            retryable = True

        if not retryable or attempt == attempts:
            return CheckResult(url, False, attempt, last_detail)
        sleeper(min(2 ** (attempt - 1), 8))
    return CheckResult(url, False, attempts, last_detail)


def check_urls(
    urls: Iterable[str],
    *,
    timeout: float,
    retries: int,
    workers: int,
    checker: Callable[..., CheckResult] = check_url,
) -> list[CheckResult]:
    """Check unique URLs concurrently and return deterministic result ordering."""
    unique_urls = sorted(set(urls))
    if not unique_urls:
        return []
    results: list[CheckResult] = []
    with ThreadPoolExecutor(max_workers=min(workers, len(unique_urls))) as executor:
        futures = {
            executor.submit(
                checker,
                url,
                timeout=timeout,
                retries=retries,
            ): url
            for url in unique_urls
        }
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda result: result.url)


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("scripts/external_link_policy.json"),
    )
    parser.add_argument("--timeout", type=positive_float, default=15.0)
    parser.add_argument("--retries", type=nonnegative_int, default=2)
    parser.add_argument("--workers", type=positive_int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        root = Path(result.stdout.strip()).resolve()
        policy_path = args.policy
        if not policy_path.is_absolute():
            policy_path = root / policy_path
        allowlist = load_allowlist(policy_path)
        links, collection_failures = collect_external_links(
            root,
            tracked_markdown_paths(root),
        )
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: external-link policy could not be evaluated: {exc}", file=sys.stderr)
        return 2

    stale_allowlist = sorted(set(allowlist) - set(links))
    if collection_failures or stale_allowlist:
        for failure in collection_failures:
            print(failure, file=sys.stderr)
        for url in stale_allowlist:
            print(f"stale external-link allowlist entry: {url}", file=sys.stderr)
        print("ERROR: external-link inputs are invalid.", file=sys.stderr)
        return 2

    checked_urls = sorted(set(links) - set(allowlist))
    results = check_urls(
        checked_urls,
        timeout=args.timeout,
        retries=args.retries,
        workers=args.workers,
    )
    failures = [result for result in results if not result.success]
    if failures:
        for failure in failures:
            sources = ", ".join(
                f"{source.path}:{source.line}" for source in sorted(links[failure.url])
            )
            print(
                f"{sources}: external link failed after {failure.attempts} "
                f"attempt(s): {failure.url} ({failure.detail})",
                file=sys.stderr,
            )
        print(
            f"ERROR: {len(failures)} external HTTP(S) link(s) failed.",
            file=sys.stderr,
        )
        return 1

    print(
        "external_link_monitor_passed "
        f"checked_urls={len(results)} "
        f"allowlisted_urls={len(allowlist)} "
        f"source_occurrences={sum(len(sources) for sources in links.values())}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
