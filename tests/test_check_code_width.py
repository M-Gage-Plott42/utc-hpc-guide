from __future__ import annotations

import unittest

from scripts.check_code_width import (
    overlong_fenced_code_lines,
    validate_fenced_code_width,
)


class FencedCodeWidthTests(unittest.TestCase):
    def test_accepts_code_at_limit_and_ignores_prose(self) -> None:
        markdown = "x" * 120 + "\n\n```bash\n" + "x" * 80 + "\n```\n"
        validate_fenced_code_width(markdown)

    def test_reports_only_overlong_fenced_lines(self) -> None:
        markdown = "~~~text\nshort\n" + "x" * 81 + "\n~~~\n"
        self.assertEqual(
            overlong_fenced_code_lines(markdown),
            [(3, 81, "x" * 81)],
        )
        with self.assertRaisesRegex(ValueError, "line 3: 81 characters"):
            validate_fenced_code_width(markdown)

    def test_expands_tabs_and_requires_closed_fence(self) -> None:
        with self.assertRaisesRegex(ValueError, "84 characters"):
            validate_fenced_code_width("```\n" + "x" * 80 + "\t\n```\n")
        with self.assertRaisesRegex(ValueError, "unclosed"):
            validate_fenced_code_width("```bash\necho ok\n")


if __name__ == "__main__":
    unittest.main()
