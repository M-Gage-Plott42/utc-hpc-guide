from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.write_pdf_toolchain_record import (
    ci_context,
    code_font_record_lines,
    parse_check_log,
    record_preamble,
    require_exact_line,
    require_locked_font_source,
    texlive_package_version,
    validate_tlmgr_package,
)
from scripts.code_font import load_code_font


PDF_SHA256 = "1" * 64
ROOT = Path(__file__).resolve().parents[1]
CURRENT_MANIFEST = json.loads(
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


class TexLivePackageTests(unittest.TestCase):
    def test_formats_omitted_null_version_as_none(self) -> None:
        details = {"installed": "Yes", "revision": "77677"}
        validate_tlmgr_package(
            "noto",
            details,
            {"revision": "77677", "version": None},
        )
        self.assertEqual(texlive_package_version(details), "none")

    def test_rejects_catalogue_version_for_unversioned_lock(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "does not match lock"):
            validate_tlmgr_package(
                "noto",
                {
                    "installed": "Yes",
                    "revision": "77677",
                    "cat-version": "2025.01.01",
                },
                {"revision": "77677", "version": None},
            )


class LockedFontSourceTests(unittest.TestCase):
    def test_accepts_regular_font_within_locked_texmf_dist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            texmf_dist = Path(temporary) / "texlive2025/texmf-dist"
            font = texmf_dist / "fonts/NotoSans-Regular.ttf"
            font.parent.mkdir(parents=True)
            font.write_bytes(b"font")
            self.assertEqual(
                require_locked_font_source(
                    font,
                    filename=font.name,
                    texmf_dist=texmf_dist,
                ),
                font.resolve(),
            )

    def test_rejects_external_font_and_parent_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            texmf_dist = root / "texlive2025/texmf-dist"
            texmf_dist.mkdir(parents=True)
            external = root / "NotoSans-Regular.ttf"
            external.write_bytes(b"shadow")
            candidates = (external, texmf_dist / "../.." / external.name)
            for candidate in candidates:
                with self.subTest(candidate=candidate):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "outside the locked TeX tree",
                    ):
                        require_locked_font_source(
                            candidate,
                            filename=external.name,
                            texmf_dist=texmf_dist,
                        )


class CodeFontRecordTests(unittest.TestCase):
    def test_records_complete_selected_font_provenance_and_roles(self) -> None:
        lines = code_font_record_lines(load_code_font(ROOT))
        self.assertIn("source=fira-code-6.2", lines)
        self.assertIn("release_tag=6.2", lines)
        self.assertIn(
            "release_commit=eee6db993696aba61ff4eef03698e2987d79910c",
            lines,
        )
        self.assertIn("font_size_pt=9.1", lines)
        self.assertIn("leading_pt=11.5", lines)
        self.assertIn("prose_family=NotoSans", lines)
        self.assertIn("inline_code_family=DejaVuSansMono", lines)
        self.assertIn("regular.postscript_name=FiraCode-Regular", lines)
        self.assertIn("bold.postscript_name=FiraCode-Bold", lines)
        self.assertTrue(
            any(
                line.startswith("archive_sha256=0949915b")
                for line in lines
            )
        )


class RecordPreambleTests(unittest.TestCase):
    def test_final_record_does_not_claim_publication(self) -> None:
        final = dict(CURRENT_MANIFEST)
        final["release_status"] = "final"
        final["document_version"] = "1.2.2"
        final["output_filename"] = "UTC_HPC_Guide.pdf"
        self.assertEqual(
            record_preamble(final),
            [
                "UTC HPC Guide PDF build traceability record",
                (
                    "distribution_status=final document build for v1.2.2; "
                    "publication is separate"
                ),
                "",
            ],
        )

    def test_candidate_record_remains_review_only(self) -> None:
        self.assertIn(
            "distribution_status=review-only release candidate for v1.2.2; "
            "not stable",
            record_preamble(CURRENT_MANIFEST),
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
