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
    check_repository,
    preflight_index_entries,
)


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
        opened_paths: list[str] = []

        def open_spy(path: os.PathLike[str] | str, flags: int) -> int:
            opened_paths.append(os.fspath(path))
            return real_open(path, flags)

        with (
            mock.patch("scripts.check_public_scrub.os.open", side_effect=open_spy),
            mock.patch(
                "scripts.check_public_scrub.read_regular_bytes_no_follow",
                wraps=scrub.read_regular_bytes_no_follow,
            ) as safe_read_spy,
        ):
            findings, _, _ = check_repository(root, policy)

        self.assertEqual(findings[0].rule, "tracked_symlink_not_allowed")
        self.assertNotIn(str(external), repr(findings))
        self.assertNotIn(str(external), opened_paths)
        safe_read_spy.assert_not_called()

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
        temp_dir, root, policy = self.make_repo(
            {
                "scripts/example.sh": "#!/bin/sh\nexit 0\n",
                tab_path: "Generic guide.",
            }
        )
        self.addCleanup(temp_dir.cleanup)
        self.run_git(root, "update-index", "--chmod=+x", "scripts/example.sh")

        findings, file_count, _ = check_repository(root, policy)

        self.assertEqual(findings, [])
        self.assertGreaterEqual(file_count, 3)

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
