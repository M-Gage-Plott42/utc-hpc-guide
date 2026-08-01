from __future__ import annotations

import unittest

from scripts.check_pdf_ocr import normalize_ocr_text, validate_ocr_pages


class PdfOcrCheckerTests(unittest.TestCase):
    def test_normalizes_case_punctuation_and_unicode(self) -> None:
        self.assertEqual(
            normalize_ocr_text("Appendix A: UTC MocsHPC — Site Notes"),
            "appendix a utc mocshpc site notes",
        )

    def test_accepts_text_on_every_page_and_required_phrases(self) -> None:
        validate_ocr_pages(
            [
                "Practical HPC Onboarding Guide " + ("intro " * 10),
                "Appendix A: UTC MocsHPC Site Notes " + ("details " * 10),
            ],
            [
                "practical hpc onboarding guide",
                "UTC MocsHPC Site Notes",
            ],
            40,
            {1: ["Practical HPC Onboarding Guide"]},
        )

    def test_rejects_cover_phrase_found_only_on_later_page(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "page 1"):
            validate_ocr_pages(
                [
                    "Practical HPC Onboarding Guide " + ("intro " * 10),
                    "Release candidate for v1.2.2 " + ("details " * 10),
                ],
                ["Release candidate for v1.2.2"],
                40,
                {1: ["Release candidate for v1.2.2"]},
            )

    def test_rejects_page_specific_requirement_for_missing_page(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing page 2"):
            validate_ocr_pages(
                ["Practical HPC Onboarding Guide " * 3],
                ["Practical HPC Onboarding Guide"],
                40,
                {2: ["Appendix"]},
            )

    def test_rejects_page_with_too_little_text(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "page 2"):
            validate_ocr_pages(
                ["enough text " * 10, "short"],
                ["enough text"],
                40,
            )

    def test_rejects_missing_required_phrase(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "SLURM Basics"):
            validate_ocr_pages(
                ["Practical HPC Onboarding Guide " * 3],
                ["SLURM Basics"],
                40,
            )

    def test_rejects_empty_required_phrase(self) -> None:
        with self.assertRaisesRegex(ValueError, "letters or digits"):
            validate_ocr_pages(
                ["Practical HPC Onboarding Guide " * 3],
                ["---"],
                40,
            )


if __name__ == "__main__":
    unittest.main()
