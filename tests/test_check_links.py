from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_links import validate_repository


class LinkCheckerTests(unittest.TestCase):
    def make_tree(self, files: dict[str, str]) -> tuple[tempfile.TemporaryDirectory[str], Path, list[Path]]:
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        markdown_paths: list[Path] = []
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            if path.suffix == ".md":
                markdown_paths.append(path)
        return temp_dir, root, markdown_paths

    def test_inline_reference_html_and_duplicate_heading_anchors(self) -> None:
        temp_dir, root, paths = self.make_tree(
            {
                "README.md": (
                    "[Inline](docs/guide_(new).md#repeat-1)\n"
                    "[Reference][guide]\n"
                    '<a href="docs/guide_(new).md#repeat">HTML</a>\n'
                    "[guide]: docs/guide_(new).md#install\n"
                ),
                "docs/guide_(new).md": (
                    "# Install\n\n## Repeat\n\n## Repeat\n"
                ),
            }
        )
        self.addCleanup(temp_dir.cleanup)
        self.assertEqual(validate_repository(root, paths), [])

    def test_ignores_links_inside_code(self) -> None:
        temp_dir, root, paths = self.make_tree(
            {
                "README.md": (
                    "`[inline](missing.md)`\n\n"
                    "```markdown\n[block](also-missing.md)\n```\n"
                )
            }
        )
        self.addCleanup(temp_dir.cleanup)
        self.assertEqual(validate_repository(root, paths), [])

    def test_reports_missing_reference_target_and_anchor(self) -> None:
        temp_dir, root, paths = self.make_tree(
            {
                "README.md": (
                    "[Missing ref][unknown]\n"
                    "[Missing file](absent.md)\n"
                    "[Missing anchor](guide.md#absent)\n"
                ),
                "guide.md": "# Present\n",
            }
        )
        self.addCleanup(temp_dir.cleanup)
        findings = validate_repository(root, paths)
        messages = {finding.message for finding in findings}
        self.assertIn("missing reference definition: unknown", messages)
        self.assertIn("missing local target: absent.md", messages)
        self.assertIn("missing Markdown anchor #absent in guide.md", messages)

    def test_reports_missing_raw_html_target(self) -> None:
        temp_dir, root, paths = self.make_tree(
            {"README.md": '<img src="assets/missing.png" alt="missing">\n'}
        )
        self.addCleanup(temp_dir.cleanup)
        findings = validate_repository(root, paths)
        self.assertEqual(findings[0].message, "missing local target: assets/missing.png")


if __name__ == "__main__":
    unittest.main()
