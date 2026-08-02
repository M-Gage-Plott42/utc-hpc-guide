from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_public_scrub as scrub
from scripts.check_public_scrub import (
    IndexEntry,
    preflight_index_entries,
)


def check_repository(
    root: Path,
    policy_path: Path,
) -> tuple[list[scrub.Finding], int, int]:
    """Exercise the public checker with its required repository-relative policy."""

    result = scrub.check_repository(root, policy_path.relative_to(root))
    assert len(result) == 3
    return result


class PublicScrubTests(unittest.TestCase):
    def run_git(
        self,
        root: Path,
        *arguments: str,
        input_data: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            input=input_data,
        )

    def make_repo(
        self,
        files: dict[str, str],
        exceptions: list[dict[str, object]] | None = None,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        for relative, content in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        policy_path = root / "policy.json"
        policy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "site_fact_exceptions": exceptions or [],
                }
            ),
            encoding="utf-8",
        )
        self.run_git(root, "init", "-q")
        self.run_git(root, "add", ".")
        return temp_dir, root, policy_path

    def write_policy(
        self,
        policy_path: Path,
        exceptions: list[dict[str, object]],
    ) -> None:
        policy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "site_fact_exceptions": exceptions,
                }
            ),
            encoding="utf-8",
        )

    def test_scans_tracked_text_outside_legacy_paths(self) -> None:
        marker = "sim" + "center"
        temp_dir, root, policy = self.make_repo({"config/example.txt": marker})
        self.addCleanup(temp_dir.cleanup)
        findings, file_count, _ = check_repository(root, policy)
        self.assertGreaterEqual(file_count, 2)
        self.assertEqual(findings[0].rule, "internal_marker")

    def test_rejects_private_windows_home_path_source_forms(self) -> None:
        for separator in ("/", "\\", "\\\\"):
            with self.subTest(separator=repr(separator)):
                private_path = separator.join(
                    ("C:", "Users", "ExampleUser", "Desktop", "guide.pdf")
                )
                temp_dir, root, policy = self.make_repo(
                    {"README.md": private_path}
                )
                try:
                    findings, _, _ = check_repository(root, policy)
                finally:
                    temp_dir.cleanup()

                self.assertEqual(len(findings), 1)
                self.assertEqual(
                    findings[0].rule,
                    "private_windows_home_path",
                )
                self.assertEqual(
                    findings[0].value,
                    separator.join(("C:", "Users", "ExampleUser")),
                )

    def test_allows_placeholder_windows_home_paths(self) -> None:
        placeholders = (
            "<username>",
            "REPLACE_WITH_USERNAME",
            "%USERNAME%",
        )
        for separator in ("/", "\\", "\\\\"):
            for placeholder in placeholders:
                with self.subTest(
                    separator=repr(separator),
                    placeholder=placeholder,
                ):
                    placeholder_path = separator.join(
                        ("C:", "Users", placeholder, "Desktop", "guide.pdf")
                    )
                    temp_dir, root, policy = self.make_repo(
                        {"README.md": placeholder_path}
                    )
                    try:
                        findings, _, _ = check_repository(root, policy)
                    finally:
                        temp_dir.cleanup()

                    self.assertEqual(findings, [])

    def test_scans_both_staged_content_and_unstaged_edits(self) -> None:
        marker = "sim" + "center"
        temp_dir, root, policy = self.make_repo({"README.md": marker})
        self.addCleanup(temp_dir.cleanup)
        (root / "README.md").write_text("Safe worktree copy.", encoding="utf-8")

        findings, _, _ = check_repository(root, policy)

        self.assertIn("internal_marker", [finding.rule for finding in findings])

        self.run_git(root, "add", "README.md")
        (root / "README.md").write_text(marker, encoding="utf-8")
        findings, _, _ = check_repository(root, policy)
        self.assertIn("internal_marker", [finding.rule for finding in findings])

    def test_unstaged_exception_cannot_allow_disallowed_index_fact(self) -> None:
        hostname = "login." + "mocshpc." + "utc.edu"
        exception = {
            "path": "docs/sites/example.md",
            "literal_fragments": ["login.", "mocshpc.", "utc.edu"],
            "reason": "Unstaged official-host exception.",
        }
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": hostname}
        )
        self.addCleanup(temp_dir.cleanup)
        self.write_policy(policy, [exception])

        findings, _, _ = check_repository(root, policy)

        site_findings = [
            finding
            for finding in findings
            if finding.path == "docs/sites/example.md"
        ]
        self.assertEqual(len(site_findings), 1)
        self.assertEqual(site_findings[0].rule, "unapproved_site_fact")

    def test_unstaged_content_uses_matching_unstaged_exception(self) -> None:
        hostname = "login." + "mocshpc." + "utc.edu"
        exception = {
            "path": "docs/sites/example.md",
            "literal_fragments": ["login.", "mocshpc.", "utc.edu"],
            "reason": "Official public hostname under development.",
        }
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": "Generic site notes."}
        )
        self.addCleanup(temp_dir.cleanup)
        (root / "docs/sites/example.md").write_text(hostname, encoding="utf-8")
        self.write_policy(policy, [exception])

        findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings, [])

    def test_allows_exact_site_fact_only_in_declared_site_page(self) -> None:
        hostname = "login." + "mocshpc." + "utc.edu"
        exception = {
            "path": "docs/sites/example.md",
            "literal_fragments": ["login.", "mocshpc.", "utc.edu"],
            "reason": "Official public hostname.",
        }
        temp_dir, root, policy = self.make_repo(
            {
                "docs/sites/example.md": hostname,
                "README.md": "Generic guide.",
            },
            [exception],
        )
        self.addCleanup(temp_dir.cleanup)
        findings, _, _ = check_repository(root, policy)
        self.assertEqual(findings, [])

        (root / "README.md").write_text(hostname, encoding="utf-8")
        findings, _, _ = check_repository(root, policy)
        self.assertEqual(findings[0].rule, "unapproved_site_fact")

    def test_rejects_valid_broken_absolute_and_relative_index_symlinks(self) -> None:
        cases = {
            "valid-link.md": "target.md",
            "broken-link.md": "missing.md",
            "absolute-link.md": "/tmp/public-scrub-external-target",
            "relative-link.md": "./docs/../target.md",
        }
        for link_name, link_target in cases.items():
            with self.subTest(link_name=link_name):
                temp_dir, root, policy = self.make_repo(
                    {
                        "target.md": "Safe target.",
                        "README.md": "Generic guide.",
                    }
                )
                try:
                    (root / link_name).symlink_to(link_target)
                    self.run_git(root, "add", link_name)

                    findings, file_count, context_hits = check_repository(
                        root,
                        policy,
                    )

                    self.assertEqual(file_count, 0)
                    self.assertEqual(context_hits, 0)
                    self.assertEqual(
                        [
                            (finding.path, finding.rule, finding.value)
                            for finding in findings
                        ],
                        [
                            (
                                link_name,
                                "tracked_symlink_not_allowed",
                                "mode=120000",
                            )
                        ],
                    )
                finally:
                    temp_dir.cleanup()

    def test_rejects_materialized_index_link_blob(self) -> None:
        temp_dir, root, policy = self.make_repo({"target.md": "Safe target."})
        self.addCleanup(temp_dir.cleanup)
        link = root / "materialized-link.md"
        link.symlink_to("target.md")
        self.run_git(root, "add", "materialized-link.md")
        link.unlink()
        link.write_text("target.md", encoding="utf-8")

        findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings[0].path, "materialized-link.md")
        self.assertEqual(findings[0].rule, "tracked_symlink_not_allowed")
        self.assertEqual(findings[0].value, "mode=120000")

    def test_rejects_worktree_link_replacing_regular_index_file(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)
        external = root / "external-untracked.txt"
        external.write_text("sim" + "center", encoding="utf-8")
        readme = root / "README.md"
        readme.unlink()
        readme.symlink_to(external)

        findings, file_count, _ = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        self.assertEqual(
            [
                (finding.path, finding.rule, finding.value)
                for finding in findings
            ],
            [
                (
                    "README.md",
                    "tracked_symlink_not_allowed",
                    "worktree_entry_is_symlink",
                )
            ],
        )

    def test_rejects_absolute_and_relative_parent_directory_links(self) -> None:
        for nested in (False, True):
            for relative in (False, True):
                with self.subTest(nested=nested, relative=relative):
                    temp_dir, root, policy = self.make_repo(
                        {"docs/sites/example.md": "Safe indexed copy."}
                    )
                    external_dir = tempfile.TemporaryDirectory()
                    try:
                        external = Path(external_dir.name)
                        (external / "example.md").write_text(
                            "sim" + "center",
                            encoding="utf-8",
                        )
                        linked_parent = root / ("docs/sites" if nested else "docs")
                        original = root / (
                            "original-sites" if nested else "original-docs"
                        )
                        linked_parent.rename(original)
                        link_target = (
                            os.path.relpath(external, start=linked_parent.parent)
                            if relative
                            else str(external)
                        )
                        linked_parent.symlink_to(
                            link_target,
                            target_is_directory=True,
                        )

                        findings, file_count, context_hits = check_repository(
                            root,
                            policy,
                        )

                        self.assertEqual(file_count, 0)
                        self.assertEqual(context_hits, 0)
                        escaped = next(
                            finding
                            for finding in findings
                            if finding.path == "docs/sites/example.md"
                        )
                        self.assertEqual(
                            escaped.rule,
                            "tracked_symlink_not_allowed",
                        )
                        self.assertEqual(
                            escaped.value,
                            "worktree_parent_component_is_symlink",
                        )
                        self.assertNotIn(str(external), repr(findings))
                    finally:
                        temp_dir.cleanup()
                        external_dir.cleanup()

    def test_rejects_broken_parent_directory_link(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": "Safe indexed copy."}
        )
        self.addCleanup(temp_dir.cleanup)
        (root / "docs").rename(root / "original-docs")
        (root / "docs").symlink_to(
            root / "missing-external-directory",
            target_is_directory=True,
        )

        findings, file_count, context_hits = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        escaped = next(
            finding
            for finding in findings
            if finding.path == "docs/sites/example.md"
        )
        self.assertEqual(escaped.rule, "tracked_symlink_not_allowed")
        self.assertEqual(
            escaped.value,
            "worktree_parent_component_is_symlink",
        )

    def test_rejects_non_directory_parent_component(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": "Safe indexed copy."}
        )
        self.addCleanup(temp_dir.cleanup)
        (root / "docs").rename(root / "original-docs")
        (root / "docs").write_text("Not a directory.", encoding="utf-8")

        findings, file_count, context_hits = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        blocked = next(
            finding
            for finding in findings
            if finding.path == "docs/sites/example.md"
        )
        self.assertEqual(
            blocked.rule,
            "tracked_worktree_type_not_allowed",
        )
        self.assertEqual(
            blocked.value,
            "worktree_parent_component_is_not_directory",
        )

    def test_parent_link_target_inode_is_never_opened_or_read(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": "Safe indexed copy."}
        )
        external_dir = tempfile.TemporaryDirectory()
        try:
            external = Path(external_dir.name)
            external_file = external / "sites/example.md"
            external_file.parent.mkdir()
            external_file.write_text("sim" + "center", encoding="utf-8")
            external_identities = {
                (external.stat().st_dev, external.stat().st_ino),
                (
                    external_file.parent.stat().st_dev,
                    external_file.parent.stat().st_ino,
                ),
                (external_file.stat().st_dev, external_file.stat().st_ino),
            }
            (root / "docs").rename(root / "original-docs")
            (root / "docs").symlink_to(external, target_is_directory=True)

            real_open = os.open
            real_read = os.read
            opened_identities: set[tuple[int, int]] = set()
            read_identities: set[tuple[int, int]] = set()

            def open_spy(
                path: os.PathLike[str] | str,
                flags: int,
                *,
                dir_fd: int | None = None,
            ) -> int:
                descriptor = real_open(path, flags, dir_fd=dir_fd)
                opened = os.fstat(descriptor)
                opened_identities.add((opened.st_dev, opened.st_ino))
                return descriptor

            def read_spy(descriptor: int, length: int) -> bytes:
                opened = os.fstat(descriptor)
                read_identities.add((opened.st_dev, opened.st_ino))
                return real_read(descriptor, length)

            with (
                mock.patch(
                    "scripts.check_public_scrub.os.open",
                    side_effect=open_spy,
                ),
                mock.patch(
                    "scripts.check_public_scrub.os.read",
                    side_effect=read_spy,
                ),
            ):
                findings, _, _ = check_repository(root, policy)

            self.assertEqual(
                next(
                    finding
                    for finding in findings
                    if finding.path == "docs/sites/example.md"
                ).rule,
                "tracked_symlink_not_allowed",
            )
            self.assertTrue(external_identities.isdisjoint(opened_identities))
            self.assertTrue(external_identities.isdisjoint(read_identities))
            self.assertNotIn(str(external), repr(findings))
        finally:
            temp_dir.cleanup()
            external_dir.cleanup()

    def test_rejects_parent_component_replacement_race(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {"docs/example.md": "Safe indexed copy."}
        )
        self.addCleanup(temp_dir.cleanup)
        replacement = root / "replacement-docs"
        replacement.mkdir()
        (replacement / "example.md").write_text(
            "sim" + "center",
            encoding="utf-8",
        )
        real_open = os.open
        swapped = False

        def open_spy(
            path: os.PathLike[str] | str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal swapped
            if path == "docs" and dir_fd is not None and not swapped:
                swapped = True
                (root / "docs").rename(root / "docs-before-race")
                replacement.rename(root / "docs")
            return real_open(path, flags, dir_fd=dir_fd)

        with mock.patch(
            "scripts.check_public_scrub.os.open",
            side_effect=open_spy,
        ):
            findings, file_count, context_hits = check_repository(root, policy)

        self.assertTrue(swapped)
        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        raced = next(
            finding
            for finding in findings
            if finding.path == "docs/example.md"
        )
        self.assertEqual(raced.rule, "tracked_worktree_path_changed")

    def test_rejects_parent_replacement_after_descriptor_open(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {"docs/example.md": "Safe indexed copy."}
        )
        self.addCleanup(temp_dir.cleanup)
        replacement = root / "replacement-docs"
        replacement.mkdir()
        (replacement / "example.md").write_text(
            "sim" + "center",
            encoding="utf-8",
        )
        real_open = os.open
        docs_open_count = 0
        swapped = False

        def open_spy(
            path: os.PathLike[str] | str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal docs_open_count, swapped
            descriptor = real_open(path, flags, dir_fd=dir_fd)
            if path == "docs" and dir_fd is not None:
                docs_open_count += 1
                if docs_open_count == 2:
                    swapped = True
                    (root / "docs").rename(root / "docs-before-race")
                    replacement.rename(root / "docs")
            return descriptor

        with mock.patch(
            "scripts.check_public_scrub.os.open",
            side_effect=open_spy,
        ):
            findings, _, _ = check_repository(root, policy)

        self.assertTrue(swapped)
        raced = next(
            finding
            for finding in findings
            if finding.path == "docs/example.md"
        )
        self.assertEqual(raced.rule, "tracked_worktree_path_changed")

    def test_rejects_parent_and_final_replacement_during_read(self) -> None:
        for component_kind in ("parent", "final"):
            with self.subTest(component_kind=component_kind):
                tracked_path = (
                    "docs/example.md"
                    if component_kind == "parent"
                    else "README.md"
                )
                temp_dir, root, policy = self.make_repo(
                    {tracked_path: "Safe indexed copy."}
                )
                try:
                    tracked_file = root / tracked_path
                    tracked_identity = (
                        tracked_file.stat().st_dev,
                        tracked_file.stat().st_ino,
                    )
                    if component_kind == "parent":
                        replacement = root / "replacement-docs"
                        replacement.mkdir()
                        (replacement / "example.md").write_text(
                            "sim" + "center",
                            encoding="utf-8",
                        )
                    else:
                        replacement = root / "replacement-readme"
                        replacement.write_text(
                            "sim" + "center",
                            encoding="utf-8",
                        )

                    real_read = os.read
                    swapped = False

                    def read_spy(descriptor: int, length: int) -> bytes:
                        nonlocal swapped
                        opened = os.fstat(descriptor)
                        if (
                            not swapped
                            and (opened.st_dev, opened.st_ino)
                            == tracked_identity
                        ):
                            swapped = True
                            if component_kind == "parent":
                                (root / "docs").rename(
                                    root / "docs-before-read-race"
                                )
                                replacement.rename(root / "docs")
                            else:
                                (root / "README.md").rename(
                                    root / "README-before-read-race"
                                )
                                replacement.rename(root / "README.md")
                        return real_read(descriptor, length)

                    with mock.patch(
                        "scripts.check_public_scrub.os.read",
                        side_effect=read_spy,
                    ):
                        findings, _, _ = check_repository(root, policy)

                    self.assertTrue(swapped)
                    raced = next(
                        finding
                        for finding in findings
                        if finding.path == tracked_path
                    )
                    self.assertEqual(
                        raced.rule,
                        "tracked_worktree_path_changed",
                    )
                finally:
                    temp_dir.cleanup()

    def test_rejects_final_component_replacement_race(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Safe copy."})
        self.addCleanup(temp_dir.cleanup)
        replacement = root / "replacement-readme"
        replacement.write_text("sim" + "center", encoding="utf-8")
        real_open = os.open
        swapped = False

        def open_spy(
            path: os.PathLike[str] | str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal swapped
            if path == "README.md" and dir_fd is not None and not swapped:
                swapped = True
                (root / "README.md").rename(root / "README-before-race")
                replacement.rename(root / "README.md")
            return real_open(path, flags, dir_fd=dir_fd)

        with mock.patch(
            "scripts.check_public_scrub.os.open",
            side_effect=open_spy,
        ):
            findings, file_count, context_hits = check_repository(root, policy)

        self.assertTrue(swapped)
        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        raced = next(
            finding for finding in findings if finding.path == "README.md"
        )
        self.assertEqual(raced.rule, "tracked_worktree_path_changed")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO support is required")
    def test_final_component_fifo_race_is_nonblocking_and_fails_closed(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Safe copy."})
        self.addCleanup(temp_dir.cleanup)
        replacement = root / "replacement-readme"
        os.mkfifo(replacement)
        real_open = os.open
        swapped = False

        def open_spy(
            path: os.PathLike[str] | str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal swapped
            if path == "README.md" and dir_fd is not None and not swapped:
                swapped = True
                (root / "README.md").rename(root / "README-before-race")
                replacement.rename(root / "README.md")
                self.assertTrue(
                    flags & os.O_NONBLOCK,
                    "a raced FIFO must never be opened in blocking mode",
                )
            return real_open(path, flags, dir_fd=dir_fd)

        with mock.patch(
            "scripts.check_public_scrub.os.open",
            side_effect=open_spy,
        ):
            findings, file_count, context_hits = check_repository(root, policy)

        self.assertTrue(swapped)
        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        raced = next(
            finding for finding in findings if finding.path == "README.md"
        )
        self.assertEqual(raced.rule, "tracked_worktree_type_not_allowed")
        self.assertEqual(raced.value, "worktree_entry_is_not_regular")

    def test_symlink_races_never_open_or_read_external_inodes(self) -> None:
        for component_kind in ("parent", "final"):
            with self.subTest(component_kind=component_kind):
                tracked_path = (
                    "docs/example.md"
                    if component_kind == "parent"
                    else "README.md"
                )
                temp_dir, root, policy = self.make_repo(
                    {tracked_path: "Safe indexed copy."}
                )
                external_dir = tempfile.TemporaryDirectory()
                try:
                    external = Path(external_dir.name)
                    if component_kind == "parent":
                        external_target = external
                        external_file = external / "example.md"
                        external_file.write_text(
                            "sim" + "center",
                            encoding="utf-8",
                        )
                        raced_component = "docs"
                        original = root / "docs"
                        replacement = root / "replacement-docs-link"
                        replacement.symlink_to(
                            external_target,
                            target_is_directory=True,
                        )
                        external_identities = {
                            (external_target.stat().st_dev, external_target.stat().st_ino),
                            (external_file.stat().st_dev, external_file.stat().st_ino),
                        }
                    else:
                        external_target = external / "external-readme"
                        external_target.write_text(
                            "sim" + "center",
                            encoding="utf-8",
                        )
                        raced_component = "README.md"
                        original = root / "README.md"
                        replacement = root / "replacement-readme-link"
                        replacement.symlink_to(external_target)
                        external_identities = {
                            (external_target.stat().st_dev, external_target.stat().st_ino)
                        }

                    real_open = os.open
                    real_read = os.read
                    opened_identities: set[tuple[int, int]] = set()
                    read_identities: set[tuple[int, int]] = set()
                    swapped = False

                    def open_spy(
                        path: os.PathLike[str] | str,
                        flags: int,
                        *,
                        dir_fd: int | None = None,
                    ) -> int:
                        nonlocal swapped
                        if (
                            path == raced_component
                            and dir_fd is not None
                            and not swapped
                        ):
                            swapped = True
                            original.rename(root / f"{raced_component}-before-race")
                            replacement.rename(original)
                        descriptor = real_open(path, flags, dir_fd=dir_fd)
                        opened = os.fstat(descriptor)
                        opened_identities.add((opened.st_dev, opened.st_ino))
                        return descriptor

                    def read_spy(descriptor: int, length: int) -> bytes:
                        opened = os.fstat(descriptor)
                        read_identities.add((opened.st_dev, opened.st_ino))
                        return real_read(descriptor, length)

                    with (
                        mock.patch(
                            "scripts.check_public_scrub.os.open",
                            side_effect=open_spy,
                        ),
                        mock.patch(
                            "scripts.check_public_scrub.os.read",
                            side_effect=read_spy,
                        ),
                    ):
                        findings, file_count, context_hits = check_repository(
                            root,
                            policy,
                        )

                    self.assertTrue(swapped)
                    self.assertEqual(file_count, 0)
                    self.assertEqual(context_hits, 0)
                    raced = next(
                        finding
                        for finding in findings
                        if finding.path == tracked_path
                    )
                    self.assertEqual(
                        raced.rule,
                        "tracked_worktree_path_changed",
                    )
                    self.assertTrue(
                        external_identities.isdisjoint(opened_identities)
                    )
                    self.assertTrue(
                        external_identities.isdisjoint(read_identities)
                    )
                    self.assertNotIn(str(external), repr(findings))
                finally:
                    temp_dir.cleanup()
                    external_dir.cleanup()

    def test_external_link_target_is_never_opened_or_read(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)
        descriptor, external_name = tempfile.mkstemp()
        os.close(descriptor)
        external = Path(external_name)
        self.addCleanup(external.unlink, missing_ok=True)
        external.write_text("sim" + "center", encoding="utf-8")
        readme = root / "README.md"
        readme.unlink()
        readme.symlink_to(external)

        real_open = os.open
        real_read = os.read
        external_identity = (external.stat().st_dev, external.stat().st_ino)
        opened_identities: set[tuple[int, int]] = set()
        read_identities: set[tuple[int, int]] = set()

        def open_spy(
            path: os.PathLike[str] | str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            opened = real_open(path, flags, dir_fd=dir_fd)
            status = os.fstat(opened)
            opened_identities.add((status.st_dev, status.st_ino))
            return opened

        def read_spy(descriptor: int, length: int) -> bytes:
            status = os.fstat(descriptor)
            read_identities.add((status.st_dev, status.st_ino))
            return real_read(descriptor, length)

        with (
            mock.patch("scripts.check_public_scrub.os.open", side_effect=open_spy),
            mock.patch(
                "scripts.check_public_scrub.os.read",
                side_effect=read_spy,
            ),
        ):
            findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings[0].rule, "tracked_symlink_not_allowed")
        self.assertNotIn(str(external), repr(findings))
        self.assertNotIn(external_identity, opened_identities)
        self.assertNotIn(external_identity, read_identities)

    def test_rejects_gitlink_before_reading_blobs(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)
        self.run_git(
            root,
            "update-index",
            "--add",
            "--cacheinfo",
            "160000,1111111111111111111111111111111111111111,vendor/module",
        )

        findings, file_count, context_hits = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        self.assertEqual(findings[0].path, "vendor/module")
        self.assertEqual(findings[0].rule, "tracked_gitlink_not_allowed")

    def test_rejects_unknown_index_mode(self) -> None:
        findings = preflight_index_entries(
            [
                IndexEntry(
                    mode="100600",
                    object_id="1" * 40,
                    stage=0,
                    path="unknown-mode.md",
                )
            ]
        )

        self.assertEqual(findings[0].rule, "tracked_mode_not_allowed")
        self.assertEqual(findings[0].value, "mode=100600")

    def test_rejects_nonzero_index_stage(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)
        object_id = self.run_git(root, "rev-parse", ":README.md").stdout.strip()
        record = b"100644 " + object_id + b" 1\tconflicted.md\0"
        self.run_git(root, "update-index", "-z", "--index-info", input_data=record)

        findings, file_count, context_hits = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        self.assertEqual(context_hits, 0)
        conflict = next(
            finding for finding in findings if finding.path == "conflicted.md"
        )
        self.assertEqual(conflict.rule, "unmerged_index_entry_not_allowed")
        self.assertEqual(conflict.value, "stage=1 mode=100644")

    def test_accepts_executable_and_tab_bearing_path(self) -> None:
        tab_path = "docs/name\twith-tab.md"
        newline_path = "docs/name\nwith-newline.md"
        temp_dir, root, policy = self.make_repo(
            {
                "scripts/example.sh": "#!/bin/sh\nexit 0\n",
                tab_path: "Generic guide.",
                newline_path: "Another generic guide.",
            }
        )
        self.addCleanup(temp_dir.cleanup)
        self.run_git(root, "update-index", "--chmod=+x", "scripts/example.sh")

        findings, file_count, _ = check_repository(root, policy)

        self.assertEqual(findings, [])
        self.assertGreaterEqual(file_count, 4)

    def test_strict_repository_path_validation(self) -> None:
        for invalid in (
            "",
            "/absolute.md",
            ".",
            "..",
            "./file.md",
            "../file.md",
            "docs/../file.md",
            "docs/./file.md",
            "docs//file.md",
            "docs/",
            "bad\0path.md",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    scrub.validate_repository_path(invalid)

        self.assertEqual(
            scrub.validate_repository_path("docs/name\tand\nlines.md"),
            ("docs", "name\tand\nlines.md"),
        )

    def test_rejects_absolute_and_escaping_policy_paths(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)

        with self.assertRaisesRegex(ValueError, "repository-relative"):
            scrub.check_repository(root, policy)
        with self.assertRaisesRegex(ValueError, "dot-dot"):
            scrub.check_repository(root, Path("../policy.json"))

    def test_check_and_exception_recount_share_one_root_descriptor(self) -> None:
        temp_dir, root, _ = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)
        real_open = os.open
        root_opens = 0

        def open_spy(
            path: os.PathLike[str] | str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal root_opens
            if os.fspath(path) == str(root) and dir_fd is None:
                root_opens += 1
            return real_open(path, flags, dir_fd=dir_fd)

        with mock.patch(
            "scripts.check_public_scrub.os.open",
            side_effect=open_spy,
        ):
            result = scrub.check_repository(
                root,
                Path("policy.json"),
                include_exception_count=True,
            )

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], [])
        self.assertEqual(result[3], 0)
        self.assertEqual(root_opens, 1)

    def test_rejects_stale_exception(self) -> None:
        exception = {
            "path": "docs/sites/example.md",
            "literal_fragments": ["epyc", "-gpu"],
            "reason": "Official public partition.",
        }
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": "No partition here."},
            [exception],
        )
        self.addCleanup(temp_dir.cleanup)
        with self.assertRaisesRegex(ValueError, "stale exception"):
            check_repository(root, policy)

    def test_rejects_policy_replacement_link_before_json_parsing(self) -> None:
        temp_dir, root, policy = self.make_repo({"README.md": "Generic guide."})
        self.addCleanup(temp_dir.cleanup)
        malformed = root / "malformed-untracked.json"
        malformed.write_text("{", encoding="utf-8")
        policy.unlink()
        policy.symlink_to(malformed)

        findings, file_count, _ = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        policy_finding = next(
            finding for finding in findings if finding.path == "policy.json"
        )
        self.assertEqual(policy_finding.rule, "tracked_symlink_not_allowed")

    def test_rejects_policy_parent_link_before_json_parsing(self) -> None:
        temp_dir, root, _ = self.make_repo({"README.md": "Generic guide."})
        external_dir = tempfile.TemporaryDirectory()
        try:
            policy_parent = root / "config"
            policy_parent.mkdir()
            nested_policy = policy_parent / "policy.json"
            nested_policy.write_text(
                '{"version": 1, "site_fact_exceptions": []}',
                encoding="utf-8",
            )
            self.run_git(root, "add", "config/policy.json")
            policy_parent.rename(root / "original-config")
            external = Path(external_dir.name)
            (external / "policy.json").write_text("{", encoding="utf-8")
            policy_parent.symlink_to(external, target_is_directory=True)

            findings, file_count, context_hits = check_repository(
                root,
                nested_policy,
            )

            self.assertEqual(file_count, 0)
            self.assertEqual(context_hits, 0)
            policy_finding = next(
                finding
                for finding in findings
                if finding.path == "config/policy.json"
            )
            self.assertEqual(
                policy_finding.rule,
                "tracked_symlink_not_allowed",
            )
            self.assertEqual(
                policy_finding.value,
                "worktree_parent_component_is_symlink",
            )
            self.assertNotIn(str(external), repr(findings))
        finally:
            temp_dir.cleanup()
            external_dir.cleanup()

    def test_rejects_exception_target_link_before_policy_parsing(self) -> None:
        hostname = "login." + "mocshpc." + "utc.edu"
        exception = {
            "path": "docs/sites/example.md",
            "literal_fragments": ["login.", "mocshpc.", "utc.edu"],
            "reason": "Official public hostname.",
        }
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": hostname},
            [exception],
        )
        self.addCleanup(temp_dir.cleanup)
        target = root / "docs/sites/example.md"
        target.unlink()
        target.symlink_to(root / "external-untracked.md")
        policy.write_text("{", encoding="utf-8")

        findings, file_count, _ = check_repository(root, policy)

        self.assertEqual(file_count, 0)
        target_finding = next(
            finding
            for finding in findings
            if finding.path == "docs/sites/example.md"
        )
        self.assertEqual(target_finding.rule, "tracked_symlink_not_allowed")

    def test_exception_target_parent_uses_rooted_no_follow_reader(self) -> None:
        hostname = "login." + "mocshpc." + "utc.edu"
        exception = {
            "path": "docs/sites/example.md",
            "literal_fragments": ["login.", "mocshpc.", "utc.edu"],
            "reason": "Official public hostname.",
        }
        temp_dir, root, policy = self.make_repo(
            {"docs/sites/example.md": hostname},
            [exception],
        )
        external_dir = tempfile.TemporaryDirectory()
        try:
            external = Path(external_dir.name)
            (external / "sites").mkdir()
            (external / "sites/example.md").write_text(
                hostname,
                encoding="utf-8",
            )
            (root / "docs").rename(root / "original-docs")
            (root / "docs").symlink_to(external, target_is_directory=True)

            with self.assertRaises(scrub.WorktreeBoundaryError) as raised:
                scrub.load_policy(root, policy.relative_to(root))

            self.assertEqual(
                raised.exception.rule,
                "tracked_symlink_not_allowed",
            )
            self.assertEqual(
                raised.exception.value,
                "worktree_parent_component_is_symlink",
            )
            self.assertNotIn(str(external), str(raised.exception))
        finally:
            temp_dir.cleanup()
            external_dir.cleanup()

    def test_requires_exception_for_node_range_notation(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {"notes.md": "Nodes use " + "epyc" + "[00-15]."}
        )
        self.addCleanup(temp_dir.cleanup)
        findings, _, _ = check_repository(root, policy)
        self.assertEqual(findings[0].rule, "unapproved_site_fact")

    def test_skips_tracked_file_deleted_from_worktree(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {
                "README.md": "Generic guide.",
                "obsolete.md": "Tracked but removed before commit.",
            }
        )
        self.addCleanup(temp_dir.cleanup)
        (root / "obsolete.md").unlink()

        findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings, [])

    def test_skips_tracked_file_with_deleted_parent_from_worktree(self) -> None:
        temp_dir, root, policy = self.make_repo(
            {
                "README.md": "Generic guide.",
                "obsolete/nested/file.md": "Tracked but removed before commit.",
            }
        )
        self.addCleanup(temp_dir.cleanup)
        (root / "obsolete/nested/file.md").unlink()
        (root / "obsolete/nested").rmdir()
        (root / "obsolete").rmdir()

        findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings, [])

    def test_scans_deleted_file_from_index(self) -> None:
        marker = "sim" + "center"
        temp_dir, root, policy = self.make_repo({"deleted.md": marker})
        self.addCleanup(temp_dir.cleanup)
        (root / "deleted.md").unlink()

        findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings[0].path, "deleted.md")
        self.assertEqual(findings[0].rule, "internal_marker")


if __name__ == "__main__":
    unittest.main()
