from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_public_scrub import check_repository


class PublicScrubTests(unittest.TestCase):
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
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        return temp_dir, root, policy_path

    def test_scans_tracked_text_outside_legacy_paths(self) -> None:
        marker = "sim" + "center"
        temp_dir, root, policy = self.make_repo({"config/example.txt": marker})
        self.addCleanup(temp_dir.cleanup)
        findings, file_count, _ = check_repository(root, policy)
        self.assertGreaterEqual(file_count, 2)
        self.assertEqual(findings[0].rule, "internal_marker")

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


if __name__ == "__main__":
    unittest.main()
