from __future__ import annotations

import unittest

from scripts.check_code_width import (
    CANONICAL_WIDTH_EXCEPTIONS,
    MINICONDA_DIGEST_LINE,
    overlong_fenced_code_lines,
    validate_fenced_code_width,
)


class FencedCodeWidthTests(unittest.TestCase):
    def test_accepts_code_at_limit_and_ignores_prose(self) -> None:
        markdown = "x" * 120 + "\n\n```bash\n" + "x" * 80 + "\n```\n"
        validate_fenced_code_width(markdown)

    def test_requires_the_exact_canonical_exception_once(self) -> None:
        markdown = f"```bash\n{MINICONDA_DIGEST_LINE}\n```\n"
        validate_fenced_code_width(
            markdown,
            allowed=CANONICAL_WIDTH_EXCEPTIONS,
        )
        with self.assertRaisesRegex(ValueError, "exceptions changed"):
            validate_fenced_code_width(markdown)
        with self.assertRaisesRegex(ValueError, "exceptions changed"):
            validate_fenced_code_width(
                markdown.replace("ecb4", "acb4"),
                allowed=CANONICAL_WIDTH_EXCEPTIONS,
            )
        with self.assertRaisesRegex(ValueError, "exceptions changed"):
            validate_fenced_code_width(
                markdown + markdown,
                allowed=CANONICAL_WIDTH_EXCEPTIONS,
            )

    def test_reports_overlong_lines_and_expands_tabs(self) -> None:
        markdown = "~~~text\nshort\n" + "x" * 80 + "\t\n~~~\n"
        self.assertEqual(
            overlong_fenced_code_lines(markdown),
            [(3, 84, "x" * 80 + "\t")],
        )
        with self.assertRaisesRegex(ValueError, "line 3: 84 characters"):
            validate_fenced_code_width(markdown)

    def test_rejects_invalid_limit_and_unclosed_fence(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            validate_fenced_code_width("", limit=0)
        with self.assertRaisesRegex(ValueError, "unclosed"):
            validate_fenced_code_width("```bash\necho ok\n")


if __name__ == "__main__":
    unittest.main()
