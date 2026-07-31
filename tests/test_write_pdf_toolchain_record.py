from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.write_pdf_toolchain_record import (
    ci_context,
    parse_check_log,
    record_preamble,
    require_exact_line,
)


PDF_SHA256 = "1" * 64
ROOT = Path(__file__).resolve().parents[1]
FINAL_MANIFEST = json.loads(
    (ROOT / "pdf/guide_manifest.json").read_text(encoding="utf-8")
)


def passing_log(pdf: Path) -> str:
    return "\n".join(
        (
            f"pdf_reproducible sha256={PDF_SHA256}",
            f"pdf_built path={pdf} sha256={PDF_SHA256}",
            (
                "pdf_qa_passed pages=24 fonts=7 "
                f"sha256={PDF_SHA256}"
            ),
            "pdf_ocr_passed pages=24 dpi=150 min_page_alnum=200",
            (
                "pdf_accessibility_qa_passed "
                "structure_roles=900 figures=3 "
                "verapdf_profile=ua2 verapdf_jobs=1"
            ),
        )
    )


class CheckLogTests(unittest.TestCase):
    def test_accepts_one_complete_log_bound_to_final_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "candidate.pdf"
            checks = parse_check_log(
                passing_log(pdf),
                pdf=pdf,
                pdf_sha256=PDF_SHA256,
            )
        self.assertEqual(checks["reproducibility"], "passed")
        self.assertEqual(checks["structural"], "passed")
        self.assertEqual(checks["render"], "passed")
        self.assertEqual(checks["ocr"], "passed")
        self.assertEqual(checks["accessibility"], "passed")
        self.assertEqual(checks["verapdf"], "passed")
        self.assertEqual(checks["pages"], "24")

    def test_rejects_missing_gate_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "candidate.pdf"
            log = "\n".join(
                line
                for line in passing_log(pdf).splitlines()
                if not line.startswith("pdf_ocr_passed ")
            )
            with self.assertRaisesRegex(
                RuntimeError,
                "exactly one pdf_ocr_passed",
            ):
                parse_check_log(
                    log,
                    pdf=pdf,
                    pdf_sha256=PDF_SHA256,
                )

    def test_rejects_duplicate_success_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "candidate.pdf"
            log = passing_log(pdf)
            log += f"\npdf_reproducible sha256={PDF_SHA256}\n"
            with self.assertRaisesRegex(
                RuntimeError,
                "exactly one pdf_reproducible",
            ):
                parse_check_log(
                    log,
                    pdf=pdf,
                    pdf_sha256=PDF_SHA256,
                )

    def test_rejects_hash_from_a_different_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "candidate.pdf"
            with self.assertRaisesRegex(
                RuntimeError,
                "do not match the final PDF",
            ):
                parse_check_log(
                    passing_log(pdf),
                    pdf=pdf,
                    pdf_sha256="2" * 64,
                )

    def test_rejects_manifest_output_path_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "actual.pdf"
            expected = root / "expected.pdf"
            with self.assertRaisesRegex(
                RuntimeError,
                "manifest-derived output",
            ):
                parse_check_log(
                    passing_log(actual),
                    pdf=expected,
                    pdf_sha256=PDF_SHA256,
                )

    def test_rejects_page_count_disagreement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "candidate.pdf"
            log = passing_log(pdf).replace(
                "pdf_ocr_passed pages=24",
                "pdf_ocr_passed pages=23",
            )
            with self.assertRaisesRegex(RuntimeError, "disagree on page count"):
                parse_check_log(
                    log,
                    pdf=pdf,
                    pdf_sha256=PDF_SHA256,
                )


class ExactToolVersionTests(unittest.TestCase):
    def test_rejects_longer_version_with_locked_prefix(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "expected exact line"):
            require_exact_line(
                "pandoc 3.10.10\n",
                "pandoc 3.10.1",
                "Pandoc",
            )


class RecordPreambleTests(unittest.TestCase):
    def test_final_record_does_not_claim_publication(self) -> None:
        self.assertEqual(
            record_preamble(FINAL_MANIFEST),
            [
                "UTC HPC Guide PDF build traceability record",
                (
                    "distribution_status=final document build for v1.2.1; "
                    "publication is separate"
                ),
                "",
            ],
        )

    def test_candidate_record_remains_review_only(self) -> None:
        candidate = dict(FINAL_MANIFEST)
        candidate["release_status"] = "candidate"
        candidate["document_version"] = "1.2.1-rc.2"
        candidate["output_filename"] = "UTC_HPC_Guide_v1.2.1-rc.2.pdf"
        self.assertIn(
            "distribution_status=review-only release candidate for v1.2.1; "
            "not stable",
            record_preamble(candidate),
        )


class CiContextTests(unittest.TestCase):
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_requires_complete_github_context_when_requested(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "required GitHub Actions context is missing",
        ):
            ci_context("a" * 40, require_github_context=True)

    @mock.patch.dict(
        os.environ,
        {"GITHUB_SHA": "b" * 40},
        clear=True,
    )
    def test_rejects_checkout_commit_mismatch(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "GITHUB_SHA does not match",
        ):
            ci_context("a" * 40, require_github_context=False)

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_local_context_still_records_commit_and_runner(self) -> None:
        context = ci_context("a" * 40, require_github_context=False)
        self.assertEqual(context["GITHUB_SHA"], "a" * 40)
        self.assertEqual(context["GITHUB_REF"], "local-worktree")
        self.assertNotEqual(context["RUNNER_OS"], "unavailable")
        self.assertNotEqual(context["RUNNER_ARCH"], "unavailable")


if __name__ == "__main__":
    unittest.main()
