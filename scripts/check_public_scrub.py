#!/usr/bin/env python3
"""Enforce this repository's public-content policy across tracked text files.

This policy-specific scanner is one defense in depth. Its finite patterns and
site-fact exceptions do not constitute exhaustive secret detection.
"""

from __future__ import annotations

import argparse
import errno
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


@dataclass
class OpenedRepositoryPath:
    """Own the descriptors and identities for one opened repository path."""

    repository_path: str
    components: list[str]
    descriptors: list[int]
    identities: list[tuple[int, int]]
    directory_flags: list[bool]

    @property
    def descriptor(self) -> int:
        return self.descriptors[-1]

    def close(self) -> None:
        while self.descriptors:
            descriptor = self.descriptors.pop()
            os.close(descriptor)


ALLOWED_INDEX_MODES = frozenset(("100644", "100755"))
OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
STAT_SUPPORTS_DIR_FD = os.stat in os.supports_dir_fd
STAT_SUPPORTS_NOFOLLOW = os.stat in os.supports_follow_symlinks


class WorktreeBoundaryError(ValueError):
    """A repository path could not be opened inside the no-follow boundary."""

    def __init__(self, path: str, rule: str, value: str) -> None:
        super().__init__(f"{rule}: {path}: {value}")
        self.path = path
        self.rule = rule
        self.value = value


def validate_repository_path(path: str) -> tuple[str, ...]:
    """Validate an unmodified Git-style repository-relative path."""

    if not isinstance(path, str) or not path:
        raise ValueError("repository path must be a non-empty string")
    if "\0" in path:
        raise ValueError("repository path must not contain NUL")
    if path.startswith("/"):
        raise ValueError(f"repository path must be relative: {path!r}")
    components = path.split("/")
    if any(component in ("", ".", "..") for component in components):
        raise ValueError(
            "repository path must not contain empty, dot, or dot-dot components: "
            f"{path!r}"
        )
    return tuple(components)


def _policy_repository_path(policy_path: os.PathLike[str] | str) -> str:
    raw_path = os.fspath(policy_path)
    if Path(raw_path).is_absolute():
        raise ValueError("scrub policy path must be repository-relative")
    validate_repository_path(raw_path)
    return raw_path


class RepositoryReader:
    """Read regular files beneath one anchored repository directory descriptor."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._root_descriptor: int | None = None
        self._root_identity: tuple[int, int] | None = None

    def __enter__(self) -> RepositoryReader:
        required_flags = ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK")
        if any(not hasattr(os, flag) for flag in required_flags):
            raise OSError("this platform cannot guarantee rooted no-follow reads")
        if not OPEN_SUPPORTS_DIR_FD or not STAT_SUPPORTS_DIR_FD:
            raise OSError("this platform cannot guarantee descriptor-relative reads")
        if not STAT_SUPPORTS_NOFOLLOW:
            raise OSError("this platform cannot guarantee no-follow status checks")

        before = os.stat(self.root, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode):
            raise ValueError("repository root must not be a symbolic link")
        if not stat.S_ISDIR(before.st_mode):
            raise ValueError("repository root must be a directory")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        descriptor = os.open(self.root, flags)
        try:
            opened = os.fstat(descriptor)
        except BaseException:
            os.close(descriptor)
            raise
        if not stat.S_ISDIR(opened.st_mode):
            os.close(descriptor)
            raise ValueError("repository root must be a directory")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            os.close(descriptor)
            raise OSError("repository root changed while being opened")
        self._root_descriptor = descriptor
        self._root_identity = (opened.st_dev, opened.st_ino)
        return self

    def __exit__(self, *args: object) -> None:
        if self._root_descriptor is not None:
            os.close(self._root_descriptor)
            self._root_descriptor = None
            self._root_identity = None

    @property
    def root_descriptor(self) -> int:
        if self._root_descriptor is None:
            raise RuntimeError("repository reader is not open")
        return self._root_descriptor

    @property
    def root_identity(self) -> tuple[int, int]:
        if self._root_identity is None:
            raise RuntimeError("repository reader is not open")
        return self._root_identity

    @staticmethod
    def _type_error(
        display_path: str,
        *,
        is_parent: bool,
        mode: int,
    ) -> WorktreeBoundaryError:
        if stat.S_ISLNK(mode):
            return WorktreeBoundaryError(
                display_path,
                "tracked_symlink_not_allowed",
                (
                    "worktree_parent_component_is_symlink"
                    if is_parent
                    else "worktree_entry_is_symlink"
                ),
            )
        return WorktreeBoundaryError(
            display_path,
            "tracked_worktree_type_not_allowed",
            (
                "worktree_parent_component_is_not_directory"
                if is_parent
                else "worktree_entry_is_not_regular"
            ),
        )

    @staticmethod
    def _path_changed(display_path: str) -> WorktreeBoundaryError:
        return WorktreeBoundaryError(
            display_path,
            "tracked_worktree_path_changed",
            "worktree_path_changed_while_opening_or_reading",
        )

    def _revalidate_root(self, display_path: str) -> None:
        try:
            current = os.stat(self.root, follow_symlinks=False)
            opened = os.fstat(self.root_descriptor)
        except (FileNotFoundError, NotADirectoryError):
            raise self._path_changed(display_path) from None
        if (
            not stat.S_ISDIR(current.st_mode)
            or not stat.S_ISDIR(opened.st_mode)
            or (current.st_dev, current.st_ino) != self.root_identity
            or (opened.st_dev, opened.st_ino) != self.root_identity
        ):
            raise self._path_changed(display_path)

    def _revalidate_opened_path(self, opened_path: OpenedRepositoryPath) -> None:
        """Require every retained descriptor to remain at its repository name."""

        self._revalidate_root(opened_path.repository_path)
        parent_descriptor = self.root_descriptor
        for component, descriptor, identity, is_directory in zip(
            opened_path.components,
            opened_path.descriptors,
            opened_path.identities,
            opened_path.directory_flags,
            strict=True,
        ):
            try:
                current = os.stat(
                    component,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                retained = os.fstat(descriptor)
            except (FileNotFoundError, NotADirectoryError):
                raise self._path_changed(opened_path.repository_path) from None
            expected_type = stat.S_ISDIR if is_directory else stat.S_ISREG
            if (
                not expected_type(current.st_mode)
                or not expected_type(retained.st_mode)
                or (current.st_dev, current.st_ino) != identity
                or (retained.st_dev, retained.st_ino) != identity
            ):
                raise self._path_changed(opened_path.repository_path)
            parent_descriptor = descriptor

    def _confirm_missing_component(
        self,
        parent_descriptor: int,
        component: str,
        display_path: str,
    ) -> None:
        """Accept an absent worktree component only if it remains absent."""

        try:
            os.stat(
                component,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return
        except NotADirectoryError:
            raise self._path_changed(display_path) from None
        raise self._path_changed(display_path)

    def _open_checked_component(
        self,
        parent_descriptor: int,
        component: str,
        display_path: str,
        *,
        is_parent: bool,
        allow_missing: bool,
    ) -> int | None:
        try:
            before = os.stat(
                component,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            if allow_missing:
                return None
            raise ValueError(
                f"required regular file does not exist: {display_path}"
            ) from None

        expected_type = stat.S_ISDIR if is_parent else stat.S_ISREG
        if not expected_type(before.st_mode):
            raise self._type_error(
                display_path,
                is_parent=is_parent,
                mode=before.st_mode,
            )

        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        if is_parent:
            flags |= os.O_DIRECTORY
        else:
            flags |= os.O_NONBLOCK
        try:
            descriptor = os.open(
                component,
                flags,
                dir_fd=parent_descriptor,
            )
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOENT, errno.ENOTDIR):
                raise self._path_changed(display_path) from None
            raise

        try:
            opened = os.fstat(descriptor)
        except BaseException:
            os.close(descriptor)
            raise
        if not expected_type(opened.st_mode):
            os.close(descriptor)
            raise self._type_error(
                display_path,
                is_parent=is_parent,
                mode=opened.st_mode,
            )
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            os.close(descriptor)
            raise self._path_changed(display_path)
        return descriptor

    def _open_regular(
        self,
        repository_path: str,
        *,
        allow_missing: bool,
    ) -> OpenedRepositoryPath | None:
        components = validate_repository_path(repository_path)
        parent_descriptor = self.root_descriptor
        opened_path = OpenedRepositoryPath(
            repository_path=repository_path,
            components=[],
            descriptors=[],
            identities=[],
            directory_flags=[],
        )
        try:
            for index, component in enumerate(components):
                is_parent = index < len(components) - 1
                descriptor = self._open_checked_component(
                    parent_descriptor,
                    component,
                    repository_path,
                    is_parent=is_parent,
                    allow_missing=allow_missing,
                )
                if descriptor is None:
                    self._revalidate_opened_path(opened_path)
                    self._confirm_missing_component(
                        parent_descriptor,
                        component,
                        repository_path,
                    )
                    opened_path.close()
                    return None
                opened_path.components.append(component)
                opened_path.descriptors.append(descriptor)
                retained = os.fstat(descriptor)
                opened_path.identities.append((retained.st_dev, retained.st_ino))
                opened_path.directory_flags.append(is_parent)
                parent_descriptor = descriptor
            return opened_path
        except BaseException:
            opened_path.close()
            raise

    def validate_regular(
        self,
        repository_path: str,
        *,
        allow_missing: bool,
    ) -> bool:
        opened_path = self._open_regular(
            repository_path,
            allow_missing=allow_missing,
        )
        if opened_path is None:
            return False
        try:
            self._revalidate_opened_path(opened_path)
            return True
        finally:
            opened_path.close()

    def read_regular_bytes(
        self,
        repository_path: str,
        *,
        allow_missing: bool,
    ) -> bytes | None:
        opened_path = self._open_regular(
            repository_path,
            allow_missing=allow_missing,
        )
        if opened_path is None:
            return None
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(opened_path.descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            self._revalidate_opened_path(opened_path)
            return b"".join(chunks)
        finally:
            opened_path.close()


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
        try:
            validate_repository_path(entry.path)
        except ValueError:
            findings.append(
                Finding(
                    entry.path,
                    0,
                    "tracked_path_not_allowed",
                    "path_is_not_strictly_repository_relative",
                )
            )
            continue
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


def preflight_worktree_entries(
    root: Path,
    entries: Iterable[IndexEntry],
    policy_path: Path,
    *,
    reader: RepositoryReader | None = None,
) -> list[Finding]:
    policy_key = _policy_repository_path(policy_path)
    inspected: set[str] = set()
    candidates = [
        entry.path
        for entry in entries
        if entry.stage == 0 and entry.mode in ALLOWED_INDEX_MODES
    ]
    candidates.append(policy_key)

    def inspect(active_reader: RepositoryReader) -> list[Finding]:
        findings: list[Finding] = []
        for display_path in candidates:
            if display_path in inspected:
                continue
            inspected.add(display_path)
            try:
                active_reader.validate_regular(
                    display_path,
                    allow_missing=display_path != policy_key,
                )
            except WorktreeBoundaryError as exc:
                findings.append(Finding(exc.path, 0, exc.rule, exc.value))
        return findings

    if reader is not None:
        return inspect(reader)
    with RepositoryReader(root) as active_reader:
        return inspect(active_reader)


def read_regular_bytes_no_follow(
    root: Path,
    repository_path: str,
    *,
    allow_missing: bool,
) -> bytes | None:
    """Compatibility wrapper around the rooted descriptor-relative reader."""

    with RepositoryReader(root) as reader:
        return reader.read_regular_bytes(
            repository_path,
            allow_missing=allow_missing,
        )


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
        try:
            validate_repository_path(path)
        except ValueError as exc:
            raise ValueError(
                f"exception {index} path must stay within the repository"
            ) from exc
        normalized = PurePosixPath(path)
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


def load_policy(
    root: Path,
    policy_path: Path,
    *,
    reader: RepositoryReader | None = None,
) -> list[SiteFactException]:
    policy_key = _policy_repository_path(policy_path)

    def load(active_reader: RepositoryReader) -> list[SiteFactException]:
        policy_data = active_reader.read_regular_bytes(
            policy_key,
            allow_missing=False,
        )
        assert policy_data is not None

        def read_worktree_target(path: str) -> bytes:
            target_data = active_reader.read_regular_bytes(
                path,
                allow_missing=False,
            )
            assert target_data is not None
            return target_data

        return parse_policy(policy_data, read_worktree_target)

    if reader is not None:
        return load(reader)
    with RepositoryReader(root) as active_reader:
        return load(active_reader)


def load_index_policy(
    root: Path,
    policy_path: Path,
    entries_by_path: dict[str, IndexEntry],
    *,
    reader: RepositoryReader | None = None,
) -> list[SiteFactException]:
    policy_key = _policy_repository_path(policy_path)
    policy_entry = entries_by_path.get(policy_key)
    if policy_entry is None:
        return load_policy(root, policy_path, reader=reader)
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


def check_repository(
    root: Path,
    policy_path: Path,
    *,
    include_exception_count: bool = False,
) -> tuple[list[Finding], int, int] | tuple[list[Finding], int, int, int]:
    _policy_repository_path(policy_path)
    entries = tracked_entries(root)
    findings = preflight_index_entries(entries)
    if findings:
        result: tuple[list[Finding], int, int] = (findings, 0, 0)
        return (*result, 0) if include_exception_count else result

    with RepositoryReader(root) as reader:
        findings = preflight_worktree_entries(
            root,
            entries,
            policy_path,
            reader=reader,
        )
        if findings:
            result = (findings, 0, 0)
            return (*result, 0) if include_exception_count else result

        entries_by_path = {entry.path: entry for entry in entries}
        index_exceptions = load_index_policy(
            root,
            policy_path,
            entries_by_path,
            reader=reader,
        )
        worktree_exceptions = load_policy(root, policy_path, reader=reader)
        context_hits = 0
        text_file_count = 0
        for entry in entries:
            index_data = read_index_blob(root, entry)
            try:
                worktree_data = reader.read_regular_bytes(
                    entry.path,
                    allow_missing=True,
                )
            except WorktreeBoundaryError as exc:
                findings.append(Finding(exc.path, 0, exc.rule, exc.value))
                continue
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

        result = (findings, text_file_count, context_hits)
        if include_exception_count:
            return (*result, len(worktree_exceptions))
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        default="scripts/public_scrub_exceptions.json",
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
    try:
        policy_path = Path(_policy_repository_path(args.policy))
        (
            findings,
            text_file_count,
            context_hits,
            exception_count,
        ) = check_repository(
            root,
            policy_path,
            include_exception_count=True,
        )
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
        f"site_fact_exceptions={exception_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
