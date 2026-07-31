from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.build_pdf import assemble_markdown, build_once
from scripts.pdf_manifest import (
    derive_pdf_trailer_id,
    distribution_status,
    load_manifest,
    output_path,
    workflow_metadata,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT_MANIFEST = json.loads(
    (ROOT / "pdf/guide_manifest.json").read_text(encoding="utf-8")
)


def candidate_manifest(
    base: dict[str, object] | None = None,
) -> dict[str, object]:
    manifest = copy.deepcopy(base if base is not None else CURRENT_MANIFEST)
    manifest["release_status"] = "candidate"
    manifest["document_version"] = "1.2.1-rc.2"
    manifest["output_filename"] = "UTC_HPC_Guide_v1.2.1-rc.2.pdf"
    manifest["pdf_trailer_id"] = derive_pdf_trailer_id(
        str(manifest["document_version"]),
        int(manifest["source_date_epoch"]),
    )
    return manifest


class PdfManifestTests(unittest.TestCase):
    def write_manifest(
        self,
        root: Path,
        manifest: dict[str, object],
    ) -> Path:
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_checked_in_manifest_is_final_and_derives_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = load_manifest(
                self.write_manifest(root, CURRENT_MANIFEST)
            )
            self.assertEqual(
                output_path(root, manifest),
                root / "dist/UTC_HPC_Guide.pdf",
            )
        self.assertEqual(manifest["release_status"], "final")

    def test_accepts_explicit_rc2_candidate_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = load_manifest(
                self.write_manifest(root, candidate_manifest())
            )
        self.assertEqual(manifest["release_status"], "candidate")
        self.assertEqual(
            output_path(root, manifest),
            root / "dist/UTC_HPC_Guide_v1.2.1-rc.2.pdf",
        )

    def test_rejects_candidate_version_mismatch(self) -> None:
        manifest = candidate_manifest()
        manifest["document_version"] = "1.2.1"
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(Path(temporary), manifest)
            with self.assertRaisesRegex(ValueError, "release_target-rc.N"):
                load_manifest(path)

    def test_rejects_candidate_filename_mismatch(self) -> None:
        manifest = candidate_manifest()
        manifest["output_filename"] = "UTC_HPC_Guide.pdf"
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(Path(temporary), manifest)
            with self.assertRaisesRegex(ValueError, "release state"):
                load_manifest(path)

    def test_accepts_final_state_without_changing_builder_shape(self) -> None:
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        with tempfile.TemporaryDirectory() as temporary:
            parsed = load_manifest(
                self.write_manifest(Path(temporary), manifest)
            )
        self.assertEqual(parsed["release_status"], "final")

    def test_final_trailer_id_has_documented_deterministic_derivation(self) -> None:
        self.assertEqual(
            derive_pdf_trailer_id("1.2.1", 1785412800),
            "8ea9f52d5afad85d958495b620dbf86a",
        )
        self.assertEqual(
            CURRENT_MANIFEST["pdf_trailer_id"],
            derive_pdf_trailer_id(
                str(CURRENT_MANIFEST["document_version"]),
                int(CURRENT_MANIFEST["source_date_epoch"]),
            ),
        )

    def test_rejects_stale_deterministic_trailer_id(self) -> None:
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        manifest["source_date_epoch"] = int(manifest["source_date_epoch"]) + 1
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(Path(temporary), manifest)
            with self.assertRaisesRegex(
                ValueError,
                "document_version/source_date_epoch",
            ):
                load_manifest(path)

    def test_workflow_metadata_is_manifest_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            metadata = workflow_metadata(
                Path(temporary),
                copy.deepcopy(CURRENT_MANIFEST),
            )
        self.assertEqual(
            metadata,
            {
                "path": "dist/UTC_HPC_Guide.pdf",
                "document_version": "1.2.1",
                "release_status": "final",
                "artifact_label": "utc-hpc-guide-v1.2.1-final",
            },
        )

    def test_candidate_workflow_metadata_is_manifest_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            metadata = workflow_metadata(
                Path(temporary),
                candidate_manifest(),
            )
        self.assertEqual(
            metadata,
            {
                "path": "dist/UTC_HPC_Guide_v1.2.1-rc.2.pdf",
                "document_version": "1.2.1-rc.2",
                "release_status": "candidate",
                "artifact_label": "utc-hpc-guide-v1.2.1-rc.2-candidate",
            },
        )

    def test_workflow_metadata_rejects_unsafe_version_token(self) -> None:
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        manifest["release_target"] = "1.2.1\ninjected=true"
        manifest["document_version"] = manifest["release_target"]
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "safe numeric"):
                workflow_metadata(Path(temporary), manifest)

    def test_workflow_metadata_rejects_oversized_artifact_label(self) -> None:
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        manifest["release_target"] = f"{'1' * 120}.2.3"
        manifest["document_version"] = manifest["release_target"]
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "workflow-safe"):
                workflow_metadata(Path(temporary), manifest)

    def test_distribution_status_does_not_claim_publication(self) -> None:
        self.assertEqual(
            distribution_status(CURRENT_MANIFEST),
            "final document build for v1.2.1; publication is separate",
        )
        self.assertEqual(
            distribution_status(candidate_manifest()),
            "review-only release candidate for v1.2.1; not stable",
        )


class PdfAssemblyTests(unittest.TestCase):
    def minimal_source_tree(
        self,
        root: Path,
    ) -> dict[str, object]:
        (root / "chapter.md").write_text(
            "# 00 Overview\n\nNative paragraph.\n",
            encoding="utf-8",
        )
        (root / "site.md").write_text(
            "# Site Notes\n\nSelected public facts.\n",
            encoding="utf-8",
        )
        (root / "example.sbatch").write_text(
            "#!/usr/bin/env bash\nsqueue --me\n",
            encoding="utf-8",
        )
        (root / "header.tex").write_text(
            "v@DOCUMENT_VERSION@\n",
            encoding="utf-8",
        )
        (root / "template.latex").write_text(
            "$document-metadata.latex()$\n$body$\n",
            encoding="utf-8",
        )
        (root / "code.lua").write_text(
            "function CodeBlock(block) return block end\n",
            encoding="utf-8",
        )
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        manifest["header_source"] = "header.tex"
        manifest["template_source"] = "template.latex"
        manifest["code_filter_source"] = "code.lua"
        manifest["core_sources"] = ["chapter.md"]
        manifest["site_appendices"] = [
            {"path": "site.md", "title": "Appendix A: Site Notes"}
        ]
        manifest["examples"] = ["example.sbatch"]
        return manifest

    def test_candidate_and_final_labels_are_manifest_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = candidate_manifest(self.minimal_source_tree(root))
            candidate_text = assemble_markdown(root, candidate)
            self.assertIn("Release candidate for v1.2.1", candidate_text)
            self.assertIn("Candidate identifier: `v1.2.1-rc.2`", candidate_text)
            self.assertNotIn("\\lstset", candidate_text)

            final = self.minimal_source_tree(root)
            final_text = assemble_markdown(root, final)
            self.assertIn("**Version 1.2.1**", final_text)
            self.assertIn("Document identifier: `v1.2.1`", final_text)

    def test_build_command_uses_lualatex_pdfua_and_semantic_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            manifest = self.minimal_source_tree(root)
            output = root / manifest["output_filename"]
            completed = subprocess.CompletedProcess(args=[], returncode=0)
            with (
                mock.patch(
                    "scripts.build_pdf.command_path",
                    side_effect=lambda name: f"/locked/bin/{name}",
                ),
                mock.patch(
                    "scripts.build_pdf.locked_font_variables",
                    return_value=[],
                ),
                mock.patch(
                    "scripts.build_pdf.subprocess.run",
                    return_value=completed,
                ) as run_mock,
            ):
                build_once(root, manifest, output, work)

            command = run_mock.call_args.args[0]
            self.assertIn("--from=markdown-implicit_figures+smart", command)
            self.assertIn("--pdf-engine=/locked/bin/lualatex", command)
            self.assertIn("--variable", command)
            self.assertIn("pdfstandard=ua-2", command)
            self.assertIn(
                f"--template={root / 'template.latex'}",
                command,
            )
            self.assertIn(f"--lua-filter={root / 'code.lua'}", command)
            self.assertIn("--syntax-highlighting=none", command)
            self.assertNotIn("--listings", command)
            self.assertFalse(any("xelatex" in item for item in command))

    def test_vendored_template_seeds_tagging_before_metadata(self) -> None:
        template = (ROOT / "pdf/tagged-template.latex").read_text(
            encoding="utf-8"
        )
        self.assertLess(
            template.index("\\sys_gset_rand_seed:n"),
            template.index("$document-metadata.latex()$"),
        )
        self.assertNotIn("pdf:trailerid", template)
        self.assertIn("\\pdfvariable trailerid", template)

    def test_build_disables_implicit_floating_figures(self) -> None:
        code_filter = (ROOT / "pdf/code-blocks.lua").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("function Figure", code_filter)

    def test_semantic_code_environment_has_a_visual_block_boundary(self) -> None:
        header = (ROOT / "pdf/header.tex").read_text(encoding="utf-8")
        self.assertIn("\\par\\addvspace{0.5\\baselineskip}", header)


if __name__ == "__main__":
    unittest.main()
