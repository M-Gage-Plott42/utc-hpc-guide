from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.build_pdf import (
    appendix_example_block,
    assemble_markdown,
    build_once,
    code_font_replacements,
    cover_variables,
    locked_font_variables,
)
from scripts.check_pdf import (
    CODE_FILTER_PROOF_LINES,
    EXACT_CODE_EXTRACTION_SPANS,
    extract_unique_fixed_span,
    validate_code_filter_output,
    validate_exact_code_extraction,
    validate_fonts,
)
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
PDF_FONTS = """\
name                                 type              encoding         emb sub uni object ID
------------------------------------ ----------------- ---------------- --- --- --- ---------
XRSAGH+NotoSans-Bold                 CID TrueType      Identity-H       yes yes yes     53  0
VZFBDX+NotoSans-Regular              CID TrueType      Identity-H       yes yes yes     54  0
KIHLRP+DejaVuSansMono                CID TrueType      Identity-H       yes yes yes     55  0
RBAFGN+DejaVuSansMono-Bold           CID TrueType      Identity-H       yes yes yes   1398  0
ABCDEF+FiraCode-Regular              CID TrueType      Identity-H       yes yes yes   1399  0
"""


def candidate_manifest(
    base: dict[str, object] | None = None,
) -> dict[str, object]:
    manifest = copy.deepcopy(base if base is not None else CURRENT_MANIFEST)
    manifest["release_status"] = "candidate"
    manifest["release_target"] = "1.2.2"
    manifest["document_version"] = "1.2.2-rc.1"
    manifest["output_filename"] = "UTC_HPC_Guide_v1.2.2-rc.1.pdf"
    manifest["pdf_trailer_id"] = derive_pdf_trailer_id(
        str(manifest["document_version"]),
        int(manifest["source_date_epoch"]),
    )
    return manifest


def final_manifest(
    base: dict[str, object] | None = None,
) -> dict[str, object]:
    manifest = copy.deepcopy(base if base is not None else CURRENT_MANIFEST)
    manifest["release_status"] = "final"
    manifest["release_target"] = "1.2.2"
    manifest["document_version"] = "1.2.2"
    manifest["output_filename"] = "UTC_HPC_Guide.pdf"
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

    def test_checked_in_manifest_is_candidate_and_derives_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = load_manifest(
                self.write_manifest(root, CURRENT_MANIFEST)
            )
            self.assertEqual(
                output_path(root, manifest),
                root / "dist/UTC_HPC_Guide_v1.2.2-rc.2.pdf",
            )
        self.assertEqual(manifest["release_status"], "candidate")

    def test_accepts_explicit_final_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = load_manifest(
                self.write_manifest(root, final_manifest())
            )
        self.assertEqual(manifest["release_status"], "final")
        self.assertEqual(
            output_path(root, manifest),
            root / "dist/UTC_HPC_Guide.pdf",
        )

    def test_rejects_candidate_version_mismatch(self) -> None:
        manifest = candidate_manifest()
        manifest["document_version"] = "1.2.2"
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
        manifest = final_manifest()
        with tempfile.TemporaryDirectory() as temporary:
            parsed = load_manifest(
                self.write_manifest(Path(temporary), manifest)
            )
        self.assertEqual(parsed["release_status"], "final")

    def test_final_trailer_id_has_documented_deterministic_derivation(self) -> None:
        self.assertEqual(
            derive_pdf_trailer_id("1.2.2-rc.2", 1785628800),
            "f4ea8ec5e9282eabbe16cc4597130260",
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
                "path": "dist/UTC_HPC_Guide_v1.2.2-rc.2.pdf",
                "document_version": "1.2.2-rc.2",
                "release_status": "candidate",
                "artifact_label": "utc-hpc-guide-v1.2.2-rc.2-candidate",
            },
        )

    def test_final_workflow_metadata_is_manifest_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            metadata = workflow_metadata(
                Path(temporary),
                final_manifest(),
            )
        self.assertEqual(
            metadata,
            {
                "path": "dist/UTC_HPC_Guide.pdf",
                "document_version": "1.2.2",
                "release_status": "final",
                "artifact_label": "utc-hpc-guide-v1.2.2-final",
            },
        )

    def test_workflow_metadata_rejects_unsafe_version_token(self) -> None:
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        manifest["release_target"] = "1.2.2\ninjected=true"
        manifest["document_version"] = manifest["release_target"]
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "safe numeric"):
                workflow_metadata(Path(temporary), manifest)

    def test_workflow_metadata_rejects_oversized_artifact_label(self) -> None:
        manifest = copy.deepcopy(CURRENT_MANIFEST)
        manifest["release_status"] = "final"
        manifest["release_target"] = f"{'1' * 120}.2.3"
        manifest["document_version"] = manifest["release_target"]
        manifest["output_filename"] = "UTC_HPC_Guide.pdf"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "workflow-safe"):
                workflow_metadata(Path(temporary), manifest)

    def test_distribution_status_does_not_claim_publication(self) -> None:
        self.assertEqual(
            distribution_status(CURRENT_MANIFEST),
            "review-only release candidate for v1.2.2; not stable",
        )
        self.assertEqual(
            distribution_status(final_manifest()),
            "final document build for v1.2.2; publication is separate",
        )


class PdfAssemblyTests(unittest.TestCase):
    def minimal_source_tree(
        self,
        root: Path,
    ) -> dict[str, object]:
        (root / "chapter.md").write_text(
            "# 00 Overview\n\n## Audience\n\nNative paragraph.\n",
            encoding="utf-8",
        )
        (root / "site.md").write_text(
            "# Site Notes\n\n## Access\n\nSelected public facts.\n",
            encoding="utf-8",
        )
        (root / "example.sbatch").write_text(
            "#!/bin/bash -l\n\n    indented child\ncolumn-a  column-b\n",
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

    def test_appendix_blocks_preserve_exact_tracked_source_boundaries(self) -> None:
        assembled = assemble_markdown(ROOT, CURRENT_MANIFEST)
        self.assertNotIn("```bash\n\n", assembled)
        for index, path in enumerate(CURRENT_MANIFEST["examples"], start=1):
            source = (ROOT / path).read_text(encoding="utf-8")
            expected = (
                f"## B.{index} `{Path(path).name}` "
                f"{{#example-{Path(path).stem.replace('_', '-')}}}\n\n"
                f"```bash\n{source}```"
            )
            self.assertIn(expected, assembled)
            self.assertTrue(source.startswith("#!/bin/bash -l\n"))

    def test_appendix_block_rejects_invalid_source_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            example = root / "example.sbatch"
            invalid_sources = (
                "",
                "\n#!/bin/bash -l\necho ready\n",
                "#!/bin/bash -l\necho ready\n\n",
                "#!/bin/bash -l\necho ready\n   \n",
                "#!/usr/bin/env bash\necho ready\n",
            )
            for source in invalid_sources:
                with self.subTest(source=source):
                    example.write_text(source, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        appendix_example_block(root, example.name, 1)

    def test_code_filter_contract_is_source_line_owned(self) -> None:
        header = (ROOT / "pdf/header.tex").read_text(encoding="utf-8")
        code_filter = (ROOT / "pdf/code-blocks.lua").read_text(encoding="utf-8")
        self.assertNotIn("\\everypar", header)
        self.assertIn("\\tagstructbegin{tag=Code}", header)
        self.assertIn("\\tagmcbegin{artifact=layout}", header)
        self.assertIn("\\llap{", header)
        self.assertIn("local inlines = {code_rail()}", code_filter)
        self.assertIn("ipairs(code_lines(block.text))", code_filter)
        self.assertIn('text:sub(1, 1) == "\\n"', code_filter)
        self.assertIn('text:sub(-1) == "\\n"', code_filter)

    def test_code_filter_output_has_one_direct_rail_per_real_line(self) -> None:
        output = """\\begin{GuideCode}

\\leavevmode\\GuideCodeRail{}RAIL-PROOF-START

\\leavevmode\\GuideCodeRail{}\\hspace*{\\dimexpr4\\fontcharwd\\font`0\\relax}indented child

\\leavevmode\\GuideCodeRail{}\\strut

\\leavevmode\\GuideCodeRail{}column-a \\hspace*{\\dimexpr1\\fontcharwd\\font`0\\relax}column-b

\\leavevmode\\GuideCodeRail{}RAIL-PROOF-END

\\end{GuideCode}
"""
        self.assertEqual(
            output.count("\\leavevmode\\GuideCodeRail{}"),
            len(CODE_FILTER_PROOF_LINES),
        )
        validate_code_filter_output(output)
        with self.assertRaisesRegex(RuntimeError, "one rail per real source line"):
            validate_code_filter_output(
                output.replace("\\leavevmode\\GuideCodeRail{}", "", 1)
            )

    def test_exact_code_extraction_preserves_source_spaces(self) -> None:
        text = "\n\n".join(
            "      " + line if line else ""
            for span in EXACT_CODE_EXTRACTION_SPANS
            for line in span
        )
        validate_exact_code_extraction(text)
        self.assertEqual(
            extract_unique_fixed_span(text, EXACT_CODE_EXTRACTION_SPANS[0]),
            EXACT_CODE_EXTRACTION_SPANS[0],
        )
        changed = text.replace("    try:", "   try:", 1)
        with self.assertRaisesRegex(RuntimeError, "code space extraction changed"):
            validate_exact_code_extraction(changed)

    def test_candidate_and_final_labels_are_manifest_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = candidate_manifest(self.minimal_source_tree(root))
            candidate_text = assemble_markdown(root, candidate)
            self.assertIn("# 1. Overview", candidate_text)
            self.assertIn("## 1.1 Audience", candidate_text)
            self.assertIn("# Appendix A: Site Notes", candidate_text)
            self.assertIn("## A.1 Access", candidate_text)
            self.assertIn("## B.1 `example.sbatch`", candidate_text)
            self.assertNotIn("Release candidate", candidate_text)
            self.assertNotIn("\\lstset", candidate_text)
            self.assertEqual(
                cover_variables(candidate),
                {
                    "cover-release-label": "Release candidate for v1.2.2",
                    "cover-identifier-label": "Candidate identifier",
                    "document-version": "1.2.2-rc.1",
                },
            )

            final = final_manifest(self.minimal_source_tree(root))
            final_text = assemble_markdown(root, final)
            self.assertNotIn("Version 1.2.2", final_text)
            self.assertEqual(
                cover_variables(final),
                {
                    "cover-release-label": "Version 1.2.2",
                    "cover-identifier-label": "Document identifier",
                    "document-version": "1.2.2",
                },
            )

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
                    "scripts.build_pdf.code_font_replacements",
                    return_value={
                        "@CODE_FONT_DEFINITION@": "",
                        "@CODE_FONT_COMMAND@": r"\ttfamily",
                        "@CODE_FONT_SIZE@": "9.1",
                        "@CODE_FONT_LEADING@": "11.5",
                    },
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
            self.assertIn("classoption=titlepage", command)
            self.assertIn(
                "cover-release-label=Release candidate for v1.2.2",
                command,
            )
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
        self.assertIn("\\hypersetup{pageanchor=false}", template)
        self.assertIn("\\thispdfpagelabel{Cover}", template)
        self.assertIn("\\pagenumbering{roman}", template)
        self.assertIn("\\pagenumbering{arabic}", template)
        self.assertIn("\\begin{multicols}{2}", template)
        self.assertNotIn("titlesec", template)
        self.assertNotIn("tocloft", template)

    def test_build_disables_implicit_floating_figures(self) -> None:
        code_filter = (ROOT / "pdf/code-blocks.lua").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("function Figure", code_filter)
        self.assertIn("function Image(image)", code_filter)
        self.assertIn("image.attributes.width = width", code_filter)
        self.assertNotIn("image.caption =", code_filter)

    def test_semantic_code_environment_has_a_visual_block_boundary(self) -> None:
        header = (ROOT / "pdf/header.tex").read_text(encoding="utf-8")
        self.assertIn("\\par\\addvspace{0.55\\baselineskip}", header)
        self.assertIn("\\tagstructbegin{tag=Code}", header)
        self.assertIn("\\tagmcbegin{artifact=layout}", header)
        for incompatible in (
            "titlesec",
            "tocloft",
            "needspace",
            "listings",
            "tcolorbox",
        ):
            self.assertNotIn(f"\\usepackage{{{incompatible}}}", header)

    def test_canonical_fira_definition_disables_every_ligature_path(self) -> None:
        replacements = code_font_replacements(ROOT)
        definition = replacements["@CODE_FONT_DEFINITION@"]
        self.assertEqual(replacements["@CODE_FONT_COMMAND@"], r"\GuideCodeFont")
        self.assertEqual(replacements["@CODE_FONT_SIZE@"], "9.1")
        self.assertEqual(replacements["@CODE_FONT_LEADING@"], "11.5")
        self.assertIn("UprightFont=*Regular", definition)
        self.assertIn("BoldFont=*Bold", definition)
        for feature in (
            "RequiredOff",
            "CommonOff",
            "ContextualOff",
            "DiscretionaryOff",
            "HistoricOff",
            "TeXOff",
        ):
            self.assertEqual(definition.count(f"Ligatures={feature}"), 1)
        for feature in (
            "-calt",
            "-liga",
            "-clig",
            "-dlig",
            "-hlig",
            "-rlig",
            "-tlig",
        ):
            self.assertEqual(definition.count(f"RawFeature={feature}"), 1)

    def locked_font_fixture(
        self,
        root: Path,
    ) -> tuple[Path, Path, dict[str, Path]]:
        lock = root / "pdf/toolchain.lock.json"
        lock.parent.mkdir(parents=True)
        lock.write_text('{"fixture": true}\n', encoding="utf-8")
        toolchain = root / "tools"
        texlive = toolchain / "texlive2025"
        texmf_dist = texlive / "texmf-dist"
        noto = texmf_dist / "fonts/truetype/google/noto"
        dejavu = texmf_dist / "fonts/truetype/public/dejavu"
        noto.mkdir(parents=True)
        dejavu.mkdir(parents=True)
        kpsewhich = texlive / "bin/x86_64-linux/kpsewhich"
        kpsewhich.parent.mkdir(parents=True)
        kpsewhich.touch()
        digest = hashlib.sha256(lock.read_bytes()).hexdigest()
        (toolchain / "lock-attestation.txt").write_text(
            f"lock_sha256={digest}\n",
            encoding="utf-8",
        )
        filenames = (
            "NotoSans-Regular.ttf",
            "NotoSans-Bold.ttf",
            "NotoSans-Italic.ttf",
            "NotoSans-BoldItalic.ttf",
            "DejaVuSansMono.ttf",
            "DejaVuSansMono-Bold.ttf",
            "DejaVuSansMono-Oblique.ttf",
            "DejaVuSansMono-BoldOblique.ttf",
        )
        resolved: dict[str, Path] = {}
        for filename in filenames:
            directory = noto if filename.startswith("Noto") else dejavu
            path = directory / filename
            path.touch()
            resolved[filename] = path
        return kpsewhich, texmf_dist, resolved

    def test_locked_fonts_resolve_noto_and_dejavu_from_pinned_trees(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            kpsewhich, texmf_dist, resolved = self.locked_font_fixture(root)

            def kpsewhich_result(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if command[1] == "--var-value=TEXMFDIST":
                    value = texmf_dist
                else:
                    value = resolved[command[1]]
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=str(value) + "\n",
                    stderr="",
                )

            with (
                mock.patch(
                    "scripts.build_pdf.command_path",
                    return_value=str(kpsewhich),
                ),
                mock.patch(
                    "scripts.build_pdf.subprocess.run",
                    side_effect=kpsewhich_result,
                ),
            ):
                variables = locked_font_variables(root)

        self.assertIn("mainfont=NotoSans", variables)
        self.assertIn("sansfont=NotoSans", variables)
        self.assertIn("monofont=DejaVuSansMono", variables)
        self.assertIn("mainfontoptions=UprightFont=*-Regular", variables)
        self.assertIn("mainfontoptions=Scale=MatchLowercase", variables)
        self.assertIn("monofontoptions=UprightFont=*", variables)
        self.assertIn("monofontoptions=Scale=0.88", variables)

    def test_locked_fonts_reject_texmfhome_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            kpsewhich, texmf_dist, resolved = self.locked_font_fixture(root)
            shadow = root / "texmfhome/NotoSans-Regular.ttf"
            shadow.parent.mkdir()
            shadow.touch()
            resolved[shadow.name] = shadow

            def kpsewhich_result(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                value = (
                    texmf_dist
                    if command[1] == "--var-value=TEXMFDIST"
                    else resolved[command[1]]
                )
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=str(value) + "\n",
                    stderr="",
                )

            with (
                mock.patch(
                    "scripts.build_pdf.command_path",
                    return_value=str(kpsewhich),
                ),
                mock.patch(
                    "scripts.build_pdf.subprocess.run",
                    side_effect=kpsewhich_result,
                ),
                self.assertRaisesRegex(RuntimeError, "outside the attested TEXMFDIST"),
            ):
                locked_font_variables(root)

    def test_locked_fonts_reject_stale_toolchain_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            kpsewhich, texmf_dist, _ = self.locked_font_fixture(root)
            (root / "tools/lock-attestation.txt").write_text(
                "lock_sha256=stale\n",
                encoding="utf-8",
            )
            with (
                mock.patch(
                    "scripts.build_pdf.command_path",
                    return_value=str(kpsewhich),
                ),
                mock.patch(
                    "scripts.build_pdf.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        [],
                        0,
                        stdout=str(texmf_dist) + "\n",
                        stderr="",
                    ),
                ),
                self.assertRaisesRegex(RuntimeError, "not attested"),
            ):
                locked_font_variables(root)


class PdfFontQaTests(unittest.TestCase):
    def test_accepts_exact_embedded_pdf_font_families(self) -> None:
        self.assertEqual(validate_fonts(PDF_FONTS), 5)

    def test_rejects_unlocked_embedded_pdf_font_family(self) -> None:
        unexpected = PDF_FONTS.replace(
            "VZFBDX+NotoSans-Regular",
            "VZFBDX+LiberationSans-Regular",
        )
        with self.assertRaisesRegex(RuntimeError, "font families changed"):
            validate_fonts(unexpected)


if __name__ == "__main__":
    unittest.main()
