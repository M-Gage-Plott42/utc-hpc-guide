from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.font_proofs import (
    REQUIRED_FONTSPEC_LIGATURES,
    REQUIRED_RAW_FEATURES,
    derive_proof_trailer_id,
    effective_manifest,
    load_proof_context,
    proof_output_path,
)
from scripts.pdf_manifest import derive_pdf_trailer_id


ROOT = Path(__file__).resolve().parents[1]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class FontProofFixture:
    temporary: tempfile.TemporaryDirectory[str]
    root: Path
    config_path: Path
    manifest_path: Path
    config: dict[str, object]
    lock: dict[str, object]

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "pdf").mkdir()
        (self.root / "docs/sites").mkdir(parents=True)
        (self.root / "examples").mkdir()

        (self.root / "pdf/header.tex").write_text("header\n", encoding="utf-8")
        (self.root / "pdf/template.latex").write_text(
            "$body$\n",
            encoding="utf-8",
        )
        (self.root / "pdf/code.lua").write_text(
            "function CodeBlock(block) return block end\n",
            encoding="utf-8",
        )
        (self.root / "docs/chapter.md").write_text(
            "# Chapter\n\nORIGINAL ONE\nORIGINAL TWO\n",
            encoding="utf-8",
        )
        (self.root / "docs/sites/site.md").write_text(
            "# Site\n\nPublic note.\n",
            encoding="utf-8",
        )
        (self.root / "examples/example.sbatch").write_text(
            "#!/usr/bin/env bash\nsqueue --me\n",
            encoding="utf-8",
        )
        supplement = """\
# Typeface Proof Specimen

```text
EXTRACTION-PROOF-START
REGULAR AMBIGUOUS GLYPHS
BOLD AMBIGUOUS GLYPHS
```
"""
        (self.root / "pdf/font-proof-specimen.md").write_text(
            supplement,
            encoding="utf-8",
        )

        manifest: dict[str, object] = {
            "schema_version": 2,
            "title": "Fixture Guide",
            "subtitle": "Fixture subtitle",
            "author": "Fixture Author",
            "date": "August 2026",
            "release_status": "candidate",
            "release_target": "1.2.2",
            "document_version": "1.2.2-rc.1",
            "source_date_epoch": 1785585600,
            "pdf_trailer_id": derive_pdf_trailer_id(
                "1.2.2-rc.1",
                1785585600,
            ),
            "output_filename": "UTC_HPC_Guide_v1.2.2-rc.1.pdf",
            "pdf_standard": "ua-2",
            "language": "en-US",
            "header_source": "pdf/header.tex",
            "template_source": "pdf/template.latex",
            "code_filter_source": "pdf/code.lua",
            "core_sources": ["docs/chapter.md"],
            "site_appendices": [
                {"path": "docs/sites/site.md", "title": "Appendix A: Site"}
            ],
            "examples": ["examples/example.sbatch"],
            "required_pdf_text": [
                "Fixture Guide",
                "Release candidate for v1.2.2",
            ],
            "expected_figure_alt_text": [
                "First context meaningful alternative text",
                "Second context meaningful alternative text",
                "Third context meaningful alternative text",
            ],
            "expected_structure_counts": {"H1": 3, "Code": 4},
            "ocr_dpi": 150,
            "ocr_min_alnum_per_page": 20,
            "required_ocr_text": [
                "Fixture Guide",
                "Release candidate for v1.2.2",
            ],
            "required_page_ocr_text": {
                "1": ["Fixture Guide", "Release candidate for v1.2.2"]
            },
        }
        self.manifest_path = self.root / "pdf/guide_manifest.json"
        self.write_json(self.manifest_path, manifest)
        toolchain_path = self.root / "pdf/toolchain.lock.json"
        toolchain_path.write_text('{"fixture": true}\n', encoding="utf-8")

        self.lock = {
            "schema_version": 1,
            "license": "OFL-1.1",
            "ubuntu_24_04_qa_packages": {
                "mupdf-tools": "1.23.10+ds1-1build3",
                "python3-fonttools": "4.46.0-1build2",
            },
            "sources": {
                "cascadia-source": self.lock_source(
                    "cascadia-source",
                    "Cascadia-Regular",
                    "Cascadia-Bold",
                ),
                "fira-source": self.lock_source(
                    "fira-source",
                    "Fira-Regular",
                    "Fira-Bold",
                ),
            },
        }
        self.write_lock()

        self.config = {
            "schema_version": 1,
            "proof_set": "fixture-proof-1",
            "proof_identifier": "1.2.2-proof.1",
            "proof_label": "TYPEFACE PROOF — NOT A RELEASE CANDIDATE",
            "base_manifest": "pdf/guide_manifest.json",
            "base_manifest_sha256": sha256(self.manifest_path.read_bytes()),
            "base_toolchain_lock": "pdf/toolchain.lock.json",
            "base_toolchain_lock_sha256": sha256(toolchain_path.read_bytes()),
            "font_lock": "pdf/font_proofs.lock.json",
            "baseline": {
                "commit": "a" * 40,
                "document_version": "1.2.2-rc.1",
                "filename": "UTC_HPC_Guide_v1.2.2-rc.1.pdf",
                "sha256": "b" * 64,
            },
            "supplement": "pdf/font-proof-specimen.md",
            "structure_count_deltas": {"H1": 1, "Code": 2},
            "required_pdf_text": [
                "Typeface Proof Specimen",
                "EXTRACTION-PROOF-START",
                "REGULAR AMBIGUOUS GLYPHS",
                "BOLD AMBIGUOUS GLYPHS",
            ],
            "required_ocr_text": [
                "Typeface Proof Specimen",
                "Regular Ambiguous Glyphs",
                "Bold Ambiguous Glyphs",
            ],
            "fontspec_ligatures": sorted(REQUIRED_FONTSPEC_LIGATURES),
            "raw_features": sorted(REQUIRED_RAW_FEATURES),
            "source_transforms": [
                {
                    "path": "docs/chapter.md",
                    "original": "ORIGINAL ONE",
                    "replacement": "REPLACEMENT ONE",
                },
                {
                    "path": "docs/chapter.md",
                    "original": "ORIGINAL TWO",
                    "replacement": "REPLACEMENT TWO",
                },
            ],
            "profiles": {
                "dejavu": self.profile(
                    "DejaVu large",
                    "texlive-dejavu",
                    "DejaVuSansMono",
                    "DejaVuSansMono-Bold",
                    "dejavu",
                ),
                "cascadia": self.profile(
                    "Cascadia Mono",
                    "cascadia-source",
                    "Cascadia-Regular",
                    "Cascadia-Bold",
                    "cascadia",
                ),
                "fira": self.profile(
                    "Fira Code",
                    "fira-source",
                    "Fira-Regular",
                    "Fira-Bold",
                    "fira",
                ),
            },
        }
        self.config_path = self.root / "pdf/font_proofs.json"
        self.write_config()

    def write_json(self, path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def write_config(self) -> None:
        self.write_json(self.config_path, self.config)

    def write_lock(self) -> None:
        self.write_json(self.root / "pdf/font_proofs.lock.json", self.lock)

    def locked_file(self, relative: str, content: bytes) -> dict[str, object]:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return {
            "path": relative,
            "size": len(content),
            "sha256": sha256(content),
        }

    def lock_source(
        self,
        source_id: str,
        regular_postscript: str,
        bold_postscript: str,
    ) -> dict[str, object]:
        base = f"pdf/fonts/{source_id}"
        license_entry = self.locked_file(
            f"{base}/LICENSE.txt",
            f"license-{source_id}".encode(),
        )
        license_entry["upstream_url"] = f"https://example.test/{source_id}/license"
        license_entry["upstream_size"] = license_entry["size"]
        license_entry["upstream_sha256"] = license_entry["sha256"]
        license_entry["normalization"] = "none"
        license_entry["stripped_trailing_spaces"] = {}
        regular = self.locked_file(
            f"{base}/Regular.ttf",
            f"regular-{source_id}".encode(),
        )
        regular.update(
            {
                "archive_member": "ttf/Regular.ttf",
                "postscript_name": regular_postscript,
            }
        )
        bold = self.locked_file(
            f"{base}/Bold.ttf",
            f"bold-{source_id}".encode(),
        )
        bold.update(
            {
                "archive_member": "ttf/Bold.ttf",
                "postscript_name": bold_postscript,
            }
        )
        return {
            "project": source_id,
            "project_url": f"https://example.test/{source_id}",
            "release": "1.0",
            "release_tag": "v1.0",
            "release_commit": "c" * 40,
            "release_url": f"https://example.test/{source_id}/release",
            "archive_url": f"https://example.test/{source_id}/archive.zip",
            "archive_size": 123,
            "archive_sha256": "d" * 64,
            "license_file": license_entry,
            "regular": regular,
            "bold": bold,
        }

    def profile(
        self,
        label: str,
        source: str,
        regular_postscript: str,
        bold_postscript: str,
        output_suffix: str,
    ) -> dict[str, object]:
        return {
            "label": label,
            "font_source": source,
            "font_stem": "FixtureFont-",
            "upright_pattern": "*Regular",
            "bold_pattern": "*Bold",
            "regular_postscript": regular_postscript,
            "bold_postscript": bold_postscript,
            "font_size": 9.2,
            "leading": 11.5,
            "extraction_pitch": 5.5,
            "units_per_em": 2000,
            "x_height_units": 1070,
            "output_filename": f"UTC_HPC_Guide_font-proof-{output_suffix}.pdf",
        }

    def load(self, profile: str = "cascadia"):
        return load_proof_context(
            self.root,
            Path("pdf/font_proofs.json"),
            profile,
            Path("pdf/guide_manifest.json"),
        )


class FontProofTests(FontProofFixture, unittest.TestCase):
    def test_checked_in_configuration_loads_all_profiles(self) -> None:
        for profile_id in ("dejavu-large", "cascadia-mono", "fira-code"):
            with self.subTest(profile=profile_id):
                context = load_proof_context(
                    ROOT,
                    Path("pdf/font_proofs.json"),
                    profile_id,
                    Path("pdf/guide_manifest.json"),
                )
                self.assertEqual(context.profile.id, profile_id)
                self.assertEqual(len(context.config_hash), 64)
                self.assertEqual(len(context.lock_hash), 64)
                self.assertGreater(context.profile.effective_x_height_pt, 4.9)

    def test_resolves_vendored_faces_and_leaves_dejavu_to_texlive(self) -> None:
        context = self.load("cascadia")
        self.assertEqual(
            context.regular_font_path,
            self.root / "pdf/fonts/cascadia-source/Regular.ttf",
        )
        self.assertEqual(
            context.bold_font_path,
            self.root / "pdf/fonts/cascadia-source/Bold.ttf",
        )
        self.assertEqual(context.profile.font_size, 9.2)
        self.assertIn("ContextualOff", context.ligature_denylist)
        self.assertIn("-calt", context.ligature_denylist)

        dejavu = self.load("dejavu")
        self.assertIsNone(dejavu.regular_font_path)
        self.assertIsNone(dejavu.bold_font_path)

    def test_effective_manifest_is_additive_and_profile_specific(self) -> None:
        context = self.load("cascadia")
        base_before = copy.deepcopy(context.base_manifest)
        manifest = effective_manifest(context.base_manifest, context)

        self.assertEqual(context.base_manifest, base_before)
        self.assertEqual(manifest["expected_structure_counts"]["H1"], 4)
        self.assertEqual(manifest["expected_structure_counts"]["Code"], 6)
        self.assertNotIn(
            "Release candidate for v1.2.2",
            manifest["required_pdf_text"],
        )
        self.assertIn(context.proof_label, manifest["required_pdf_text"])
        self.assertIn(context.proof_identifier, manifest["required_pdf_text"])
        self.assertIn(context.profile.label, manifest["required_ocr_text"])
        self.assertIn("EXTRACTION-PROOF-START", manifest["required_pdf_text"])
        self.assertEqual(
            manifest["output_filename"],
            context.profile.output_filename,
        )
        self.assertEqual(
            manifest["pdf_trailer_id"],
            derive_proof_trailer_id(
                context.base_manifest,
                context.proof_set,
                context.profile.id,
            ),
        )
        self.assertEqual(
            proof_output_path(self.root, context),
            self.root / "dist" / context.profile.output_filename,
        )

    def test_rejects_unknown_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown font proof profile"):
            self.load("missing")

    def test_rejects_out_of_range_profile_numbers(self) -> None:
        profiles = self.config["profiles"]
        assert isinstance(profiles, dict)
        profile = profiles["cascadia"]
        assert isinstance(profile, dict)
        cases = (
            ("font_size", 6.99, "font_size"),
            ("font_size", 14.01, "font_size"),
            ("leading", 9.2, "greater than font_size"),
            ("leading", 20.01, "leading"),
            ("extraction_pitch", 2.99, "extraction_pitch"),
            ("extraction_pitch", 10.01, "extraction_pitch"),
            ("units_per_em", 499, "units_per_em"),
            ("units_per_em", 4097, "units_per_em"),
            ("x_height_units", 2000, "less than units_per_em"),
        )
        for key, value, message in cases:
            with self.subTest(key=key, value=value):
                original = profile[key]
                profile[key] = value
                self.write_config()
                with self.assertRaisesRegex(ValueError, message):
                    self.load()
                profile[key] = original

    def test_rejects_unmatched_effective_x_height(self) -> None:
        profiles = self.config["profiles"]
        assert isinstance(profiles, dict)
        profile = profiles["fira"]
        assert isinstance(profile, dict)
        profile["x_height_units"] = 900
        self.write_config()
        with self.assertRaisesRegex(ValueError, "effective x-heights"):
            self.load()

    def test_rejects_duplicate_outputs_and_json_keys(self) -> None:
        profiles = self.config["profiles"]
        assert isinstance(profiles, dict)
        dejavu = profiles["dejavu"]
        cascadia = profiles["cascadia"]
        assert isinstance(dejavu, dict)
        assert isinstance(cascadia, dict)
        dejavu["output_filename"] = cascadia["output_filename"]
        self.write_config()
        with self.assertRaisesRegex(ValueError, "output_filename is duplicated"):
            self.load()

        self.write_config()
        raw = self.config_path.read_text(encoding="utf-8")
        raw = raw.replace(
            '{\n  "schema_version": 1,',
            '{\n  "schema_version": 1,\n  "schema_version": 1,',
            1,
        )
        self.config_path.write_text(raw, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.load()

    def test_rejects_supplement_path_traversal(self) -> None:
        self.config["supplement"] = "../outside.md"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "stay inside the repository"):
            self.load()

    def test_rejects_output_path_traversal(self) -> None:
        profiles = self.config["profiles"]
        assert isinstance(profiles, dict)
        cascadia = profiles["cascadia"]
        assert isinstance(cascadia, dict)
        cascadia["output_filename"] = "../proof.pdf"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "one safe PDF filename"):
            self.load()

    def test_rejects_vendored_path_traversal(self) -> None:
        sources = self.lock["sources"]
        assert isinstance(sources, dict)
        source = sources["cascadia-source"]
        assert isinstance(source, dict)
        regular = source["regular"]
        assert isinstance(regular, dict)
        regular["path"] = "../outside.ttf"
        self.write_lock()
        with self.assertRaisesRegex(ValueError, "stay inside the repository"):
            self.load()

    def test_rejects_vendored_font_symlink(self) -> None:
        font = self.root / "pdf/fonts/cascadia-source/Regular.ttf"
        target = self.root / "real-font.ttf"
        shutil.copyfile(font, target)
        font.unlink()
        font.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "without symbolic links"):
            self.load()

    def test_rejects_vendored_font_hash_or_size_mismatch(self) -> None:
        font = self.root / "pdf/fonts/cascadia-source/Regular.ttf"
        font.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "size mismatch|SHA-256 mismatch"):
            self.load()

    def test_verifies_declared_crlf_license_normalization(self) -> None:
        sources = self.lock["sources"]
        assert isinstance(sources, dict)
        source = sources["cascadia-source"]
        assert isinstance(source, dict)
        license_entry = source["license_file"]
        assert isinstance(license_entry, dict)
        local = b"line one\nline two\n"
        upstream = b"line one\r\nline two \r\n"
        path = self.root / str(license_entry["path"])
        path.write_bytes(local)
        license_entry.update(
            {
                "size": len(local),
                "sha256": sha256(local),
                "upstream_size": len(upstream),
                "upstream_sha256": sha256(upstream),
                "normalization": "crlf-to-lf",
                "stripped_trailing_spaces": {"2": 1},
            }
        )
        self.write_lock()
        self.load()

        license_entry["upstream_sha256"] = "0" * 64
        self.write_lock()
        with self.assertRaisesRegex(ValueError, "reconstructed upstream SHA-256"):
            self.load()

    def test_rejects_manifest_and_toolchain_hash_drift(self) -> None:
        self.config["base_manifest_sha256"] = "0" * 64
        self.write_config()
        with self.assertRaisesRegex(ValueError, "base manifest SHA-256 mismatch"):
            self.load()

        self.config["base_manifest_sha256"] = sha256(
            self.manifest_path.read_bytes()
        )
        self.config["base_toolchain_lock_sha256"] = "0" * 64
        self.write_config()
        with self.assertRaisesRegex(
            ValueError,
            "base toolchain lock SHA-256 mismatch",
        ):
            self.load()

    def test_requires_requested_manifest_to_match_config_exactly(self) -> None:
        other = self.root / "pdf/other.json"
        shutil.copyfile(self.manifest_path, other)
        with self.assertRaisesRegex(ValueError, "exactly match"):
            load_proof_context(
                self.root,
                self.config_path,
                "cascadia",
                other,
            )

    def test_rejects_inexact_or_nonunique_source_transforms(self) -> None:
        transforms = self.config["source_transforms"]
        assert isinstance(transforms, list)
        first = transforms[0]
        assert isinstance(first, dict)
        first["original"] = "MISSING ORIGINAL"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "occur exactly once"):
            self.load()

        first["original"] = "ORIGINAL ONE"
        transforms.append(copy.deepcopy(first))
        self.write_config()
        with self.assertRaisesRegex(ValueError, "duplicates another"):
            self.load()

    def test_rejects_lock_profile_postscript_mismatch(self) -> None:
        sources = self.lock["sources"]
        assert isinstance(sources, dict)
        source = sources["cascadia-source"]
        assert isinstance(source, dict)
        regular = source["regular"]
        assert isinstance(regular, dict)
        regular["postscript_name"] = "Wrong-Regular"
        self.write_lock()
        with self.assertRaisesRegex(ValueError, "does not match its profile"):
            self.load()


if __name__ == "__main__":
    unittest.main()
