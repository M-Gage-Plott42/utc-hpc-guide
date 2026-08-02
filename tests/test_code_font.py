from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_code_font_fixture import (
    AMBIGUOUS_GLYPHS,
    EXTRACTION_LINES,
    extract_unique_span,
    fixture_tex,
)
from scripts.code_font import (
    REQUIRED_LIGATURES,
    REQUIRED_RAW_FEATURES,
    fontspec_definition,
    load_code_font,
)


ROOT = Path(__file__).resolve().parents[1]


class CheckedInCodeFontTests(unittest.TestCase):
    def test_loads_only_the_selected_fira_source_and_exact_provenance(self) -> None:
        font = load_code_font(ROOT)
        self.assertEqual(font.source_id, "fira-code-6.2")
        self.assertEqual(font.source["release_tag"], "6.2")
        self.assertEqual(
            font.source["release_commit"],
            "eee6db993696aba61ff4eef03698e2987d79910c",
        )
        self.assertEqual(font.source["archive_size"], 2462987)
        self.assertEqual(
            font.source["archive_sha256"],
            "0949915ba8eb24d89fd93d10a7ff623f42830d7c5ffc3ecbf960e4ecad3e3e79",
        )
        self.assertEqual(font.regular.postscript_name, "FiraCode-Regular")
        self.assertEqual(font.bold.postscript_name, "FiraCode-Bold")
        self.assertEqual(font.font_size_pt, 9.1)
        self.assertEqual(font.leading_pt, 11.5)
        self.assertEqual(font.prose_family, "NotoSans")
        self.assertEqual(font.inline_code_family, "DejaVuSansMono")

    def test_canonical_lock_pins_required_host_font_inspection_tools(self) -> None:
        lock = json.loads(
            (ROOT / "pdf/toolchain.lock.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            lock["ubuntu_24_04_qa_packages"]["mupdf-tools"],
            "1.23.10+ds1-1build3",
        )
        self.assertEqual(
            lock["ubuntu_24_04_qa_packages"]["python3-fonttools"],
            "4.46.0-1build2",
        )
        self.assertEqual(
            lock["qa_tools"]["mutool"]["version_line"],
            "mutool version 1.23.10",
        )

    def test_fontspec_definition_contains_the_complete_exact_denylist(self) -> None:
        definition = fontspec_definition(load_code_font(ROOT))
        for feature in REQUIRED_LIGATURES:
            self.assertEqual(definition.count(f"Ligatures={feature}"), 1)
        for feature in REQUIRED_RAW_FEATURES:
            self.assertEqual(definition.count(f"RawFeature={feature}"), 1)
        self.assertIn("UprightFont=*Regular", definition)
        self.assertIn("BoldFont=*Bold", definition)

    def test_fixture_is_isolated_and_exercises_both_faces_and_spaces(self) -> None:
        source = fixture_tex(load_code_font(ROOT))
        self.assertEqual(source.count(AMBIGUOUS_GLYPHS), 2)
        self.assertIn(r"\bfseries", source)
        self.assertIn("    indented child", source)
        self.assertIn("column-a  column-b", source)
        self.assertNotIn("UTC_HPC_Guide", source)

    def test_extracts_exact_indentation_and_interior_spaces(self) -> None:
        text = "\n".join(f"      {line}" for line in EXTRACTION_LINES)
        self.assertEqual(extract_unique_span(text), EXTRACTION_LINES)


class CodeFontFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        target = self.root / "pdf"
        target.mkdir()
        shutil.copy2(ROOT / "pdf/toolchain.lock.json", target)
        shutil.copytree(
            ROOT / "pdf/fonts/fira-code-6.2",
            target / "fonts/fira-code-6.2",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def lock_path(self) -> Path:
        return self.root / "pdf/toolchain.lock.json"

    def read_lock(self) -> dict[str, object]:
        return json.loads(self.lock_path.read_text(encoding="utf-8"))

    def write_lock(self, lock: dict[str, object]) -> None:
        self.lock_path.write_text(
            json.dumps(lock, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_rejects_an_incomplete_ligature_or_raw_feature_denylist(self) -> None:
        for key, removed, message in (
            ("fontspec_ligatures", "ContextualOff", "full denylist"),
            ("raw_features", "-calt", "full denylist"),
        ):
            with self.subTest(key=key):
                lock = self.read_lock()
                config = lock["code_font"]
                assert isinstance(config, dict)
                values = config[key]
                assert isinstance(values, list)
                values.remove(removed)
                self.write_lock(lock)
                with self.assertRaisesRegex(ValueError, message):
                    load_code_font(self.root)
                shutil.copy2(ROOT / "pdf/toolchain.lock.json", self.lock_path)

    def test_rejects_tampered_or_link_replaced_font_bytes(self) -> None:
        regular = self.root / "pdf/fonts/fira-code-6.2/FiraCode-Regular.ttf"
        regular.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            load_code_font(self.root)

        shutil.copy2(
            ROOT / "pdf/fonts/fira-code-6.2/FiraCode-Regular.ttf",
            regular,
        )
        external = self.root / "external.ttf"
        shutil.copy2(regular, external)
        regular.unlink()
        regular.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "without symbolic links"):
            load_code_font(self.root)


if __name__ == "__main__":
    unittest.main()
