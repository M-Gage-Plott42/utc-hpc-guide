#!/usr/bin/env python3
"""Enforce this repository's public-content policy across tracked text files.

This policy-specific scanner is one defense in depth. Its finite patterns and
site-fact exceptions do not constitute exhaustive secret detection.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable


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


@dataclass(frozen=True)
class IndexEntry:
    mode: str
    object_id: str
    stage: int
    path: str


ALLOWED_INDEX_MODES = frozenset(("100644", "100755"))


def tracked_entries(root: Path) -> list[IndexEntry]:
    result = subprocess.run(
        ["git", "ls-files", "-s", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    entries: list[IndexEntry] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        try:
            header, raw_path = record.split(b"\t", 1)
            raw_mode, raw_object_id, raw_stage = header.split(b" ")
            mode = raw_mode.decode("ascii")
            object_id = raw_object_id.decode("ascii")
            stage_text = raw_stage.decode("ascii")
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("malformed git index entry") from exc
        if (
            not re.fullmatch(r"[0-7]{6}", mode)
            or not re.fullmatch(r"[0-9a-fA-F]+", object_id)
            or not re.fullmatch(r"[0-9]+", stage_text)
        ):
            raise ValueError("malformed git index entry")
        entries.append(
            IndexEntry(
                mode=mode,
                object_id=object_id,
                stage=int(stage_text),
                path=os.fsdecode(raw_path),
            )
        )
    return entries


def preflight_index_entries(entries: Iterable[IndexEntry]) -> list[Finding]:
    findings: list[Finding] = []
    for entry in entries:
        if entry.stage != 0:
            findings.append(
                Finding(
                    entry.path,
                    0,
                    "unmerged_index_entry_not_allowed",
                    f"stage={entry.stage} mode={entry.mode}",
                )
            )
        elif entry.mode == "120000":
            findings.append(
                Finding(
                    entry.path,
                    0,
                    "tracked_symlink_not_allowed",
                    f"mode={entry.mode}",
                )
            )
        elif entry.mode == "160000":
            findings.append(
                Finding(
                    entry.path,
                    0,
                    "tracked_gitlink_not_allowed",
                    f"mode={entry.mode}",
                )
            )
        elif entry.mode not in ALLOWED_INDEX_MODES:
            findings.append(
                Finding(
                    entry.path,
                    0,
                    "tracked_mode_not_allowed",
                    f"mode={entry.mode}",
                )
            )
    return findings


def _display_path(root: Path, target: Path) -> str:
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return str(target)


def preflight_worktree_entries(
    root: Path,
    entries: Iterable[IndexEntry],
    policy_path: Path,
) -> list[Finding]:
    findings: list[Finding] = []
    inspected: set[Path] = set()
    candidates = [
        (root / entry.path, entry.path)
        for entry in entries
        if entry.stage == 0 and entry.mode in ALLOWED_INDEX_MODES
    ]
    candidates.append((policy_path, _display_path(root, policy_path)))
    for target, display_path in candidates:
        if target in inspected:
            continue
        inspected.add(target)
        try:
            status = target.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(status.st_mode):
            findings.append(
                Finding(
                    display_path,
                    0,
                    "tracked_symlink_not_allowed",
                    "worktree_entry_is_symlink",
                )
            )
        elif not stat.S_ISREG(status.st_mode):
            findings.append(
                Finding(
                    display_path,
                    0,
                    "tracked_worktree_type_not_allowed",
                    "worktree_entry_is_not_regular",
                )
            )
    return findings


def read_regular_bytes_no_follow(
    target: Path,
    display_path: str,
    *,
    allow_missing: bool,
) -> bytes | None:
    try:
        before = target.lstat()
    except FileNotFoundError:
        if allow_missing:
            return None
        raise ValueError(f"required regular file does not exist: {display_path}") from None
    if stat.S_ISLNK(before.st_mode):
        raise ValueError(f"symbolic link is not allowed: {display_path}")
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"regular file required: {display_path}")
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("this platform cannot guarantee no-follow file reads")

    flags = os.O_RDONLY | os.O_NOFOLLOW
    descriptor = os.open(target, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"regular file required: {display_path}")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise OSError(f"file changed while being opened: {display_path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def decode_text(data: bytes | None) -> str | None:
    if data is None or b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def read_index_blob(root: Path, entry: IndexEntry) -> bytes:
    result = subprocess.run(
        ["git", "cat-file", "blob", entry.object_id],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return result.stdout


def parse_policy(
    policy_data: bytes,
    read_exception_target: Callable[[str], bytes],
) -> list[SiteFactException]:
    raw = json.loads(policy_data.decode("utf-8"))
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
        target_data = read_exception_target(path)
        try:
            target_text = target_data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"exception target is not UTF-8 text: {path}") from exc
        if literal.casefold() not in target_text.casefold():
            raise ValueError(f"stale exception is not present in {path}: {literal}")
        exceptions.append(SiteFactException(path, literal, reason.strip()))
    return exceptions


def load_policy(root: Path, policy_path: Path) -> list[SiteFactException]:
    policy_data = read_regular_bytes_no_follow(
        policy_path,
        _display_path(root, policy_path),
        allow_missing=False,
    )
    assert policy_data is not None

    def read_worktree_target(path: str) -> bytes:
        target_data = read_regular_bytes_no_follow(
            root / path,
            path,
            allow_missing=False,
        )
        assert target_data is not None
        return target_data

    return parse_policy(policy_data, read_worktree_target)


def load_index_policy(
    root: Path,
    policy_path: Path,
    entries_by_path: dict[str, IndexEntry],
) -> list[SiteFactException]:
    policy_key = _display_path(root, policy_path)
    policy_entry = entries_by_path.get(policy_key)
    if policy_entry is None:
        return load_policy(root, policy_path)
    policy_data = read_index_blob(root, policy_entry)

    def read_index_target(path: str) -> bytes:
        target_entry = entries_by_path.get(path)
        if target_entry is None:
            raise ValueError(f"exception target does not exist in index: {path}")
        return read_index_blob(root, target_entry)

    return parse_policy(policy_data, read_index_target)


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
    entries = tracked_entries(root)
    findings = preflight_index_entries(entries)
    if findings:
        return findings, 0, 0
    findings = preflight_worktree_entries(root, entries, policy_path)
    if findings:
        return findings, 0, 0

    entries_by_path = {entry.path: entry for entry in entries}
    index_exceptions = load_index_policy(root, policy_path, entries_by_path)
    worktree_exceptions = load_policy(root, policy_path)
    context_hits = 0
    text_file_count = 0
    for entry in entries:
        index_data = read_index_blob(root, entry)
        worktree_data = read_regular_bytes_no_follow(
            root / entry.path,
            entry.path,
            allow_missing=True,
        )
        index_allowed = {
            exception.literal.casefold()
            for exception in index_exceptions
            if exception.path == entry.path
        }
        worktree_allowed = {
            exception.literal.casefold()
            for exception in worktree_exceptions
            if exception.path == entry.path
        }
        snapshots = [(index_data, index_exceptions)]
        if worktree_data is not None and (
            worktree_data != index_data or worktree_allowed != index_allowed
        ):
            snapshots.append((worktree_data, worktree_exceptions))

        found_text = False
        for data, exceptions in snapshots:
            text = decode_text(data)
            if text is None:
                continue
            found_text = True
            file_findings, file_context_hits = scan_text(
                entry.path,
                text,
                exceptions,
            )
            findings.extend(file_findings)
            context_hits += file_context_hits
        if found_text:
            text_file_count += 1
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
            "ERROR: repository public-content policy failed with "
            f"{len(findings)} finding(s).",
            file=sys.stderr,
        )
        return 1
    print(
        "public_scrub_policy_passed "
        f"tracked_text_files={text_file_count} "
        f"contextual_review_hits={context_hits} "
        f"site_fact_exceptions={len(load_policy(root, policy_path))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
