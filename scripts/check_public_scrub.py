#!/usr/bin/env python3
"""Fail closed on sensitive values in every tracked text file."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


STRICT_PATTERNS = (
    (
        "internal_marker",
        re.compile("|".join((re.escape("sim" + "center"), re.escape("abc" + "123"))), re.I),
    ),
    (
        "internal_hostname",
        re.compile(re.escape("research" + ".utc" + ".edu"), re.I),
    ),
    (
        "github_token",
        re.compile(
            "|".join(
                (
                    "gh" + r"p_[A-Za-z0-9]{20,}",
                    "github" + r"_pat_[A-Za-z0-9_]{20,}",
                )
            )
        ),
    ),
    ("aws_access_key", re.compile("AK" + r"IA[0-9A-Z]{16}")),
    (
        "private_key",
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    ),
    (
        "email_address",
        re.compile(r"(?<![<\w])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ),
    (
        "private_home_path",
        re.compile(r"/home/(?!<username>|\$USER(?:/|$))[A-Za-z0-9._-]+"),
    ),
)

SITE_FACT_PATTERN = re.compile(
    r"(?<![a-z0-9_-])(?:[a-z0-9-]+\.)+utc\.edu(?![a-z0-9_-])"
    r"|(?<![a-z0-9_-])epyc(?:-[a-z0-9]+|\[[0-9-]+\]|\d+)(?![a-z0-9_-])",
    re.I,
)

CONTEXT_PATTERN = re.compile(
    r"@|/home/|\blogin\b|\bpartition\b|\baccount\b|\ballocation\b"
    r"|\bproject\b|\btoken\b|\bsecret\b",
    re.I,
)


@dataclass(frozen=True)
class SiteFactException:
    path: str
    literal: str
    reason: str


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    value: str


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def read_tracked_text(root: Path, path: str) -> str | None:
    data = (root / path).read_bytes()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def load_policy(root: Path, policy_path: Path) -> list[SiteFactException]:
    raw = json.loads(policy_path.read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("scrub policy version must be 1")
    entries = raw.get("site_fact_exceptions")
    if not isinstance(entries, list):
        raise ValueError("site_fact_exceptions must be a list")

    exceptions: list[SiteFactException] = []
    seen: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"exception {index} must be an object")
        path = entry.get("path")
        fragments = entry.get("literal_fragments")
        reason = entry.get("reason")
        if not isinstance(path, str) or not path:
            raise ValueError(f"exception {index} requires path")
        normalized = PurePosixPath(path)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError(f"exception {index} path must stay within the repository")
        if normalized.parts[:2] != ("docs", "sites") or normalized.suffix != ".md":
            raise ValueError(f"exception {index} must target a Markdown file under docs/sites")
        if (
            not isinstance(fragments, list)
            or not fragments
            or any(not isinstance(part, str) or not part for part in fragments)
        ):
            raise ValueError(f"exception {index} requires non-empty literal_fragments")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"exception {index} requires reason")
        literal = "".join(fragments)
        key = (path, literal.casefold())
        if key in seen:
            raise ValueError(f"duplicate exception for {path}: {literal}")
        seen.add(key)
        target = root / path
        if not target.is_file():
            raise ValueError(f"exception target does not exist: {path}")
        if literal.casefold() not in target.read_text(encoding="utf-8").casefold():
            raise ValueError(f"stale exception is not present in {path}: {literal}")
        exceptions.append(SiteFactException(path, literal, reason.strip()))
    return exceptions


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_text(
    path: str,
    text: str,
    exceptions: Iterable[SiteFactException],
) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    for rule, pattern in STRICT_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                Finding(path, line_number(text, match.start()), rule, match.group(0))
            )

    allowed = {
        exception.literal.casefold()
        for exception in exceptions
        if exception.path == path
    }
    for match in SITE_FACT_PATTERN.finditer(text):
        if match.group(0).casefold() not in allowed:
            findings.append(
                Finding(
                    path,
                    line_number(text, match.start()),
                    "unapproved_site_fact",
                    match.group(0),
                )
            )
    return findings, len(CONTEXT_PATTERN.findall(text))


def check_repository(root: Path, policy_path: Path) -> tuple[list[Finding], int, int]:
    exceptions = load_policy(root, policy_path)
    findings: list[Finding] = []
    context_hits = 0
    text_file_count = 0
    for path in tracked_paths(root):
        text = read_tracked_text(root, path)
        if text is None:
            continue
        text_file_count += 1
        file_findings, file_context_hits = scan_text(path, text, exceptions)
        findings.extend(file_findings)
        context_hits += file_context_hits
    return findings, text_file_count, context_hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("scripts/public_scrub_exceptions.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = Path(root_result.stdout.strip())
    policy_path = args.policy
    if not policy_path.is_absolute():
        policy_path = root / policy_path
    try:
        findings, text_file_count, context_hits = check_repository(root, policy_path)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: scrub policy could not be evaluated: {exc}", file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print(
                f"{finding.path}:{finding.line}: {finding.rule}: {finding.value}",
                file=sys.stderr,
            )
        print(
            f"ERROR: public scrub failed with {len(findings)} finding(s).",
            file=sys.stderr,
        )
        return 1
    print(
        "public_scrub_clean "
        f"tracked_text_files={text_file_count} "
        f"contextual_review_hits={context_hits} "
        f"site_fact_exceptions={len(load_policy(root, policy_path))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
